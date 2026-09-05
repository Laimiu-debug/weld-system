from datetime import datetime
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.services.ai_extraction_service import AIExtractionRunError
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.models.engineering import DrawingParseRun, ProductRevision
from app.models.smart_import import DocumentPage, ExtractionJob, SourceDocument
from app.services.ai_provider_service import AIProviderResult
from app.services.engineering_service import (
    EngineeringService, clean_evidence, drawing_risks, validate_drawing_payload,
)


def test_numeric_and_padded_references_keep_weld_associations():
    data = {"parts": [{"ref": 1, "name": "筒体"}, {"ref": " 2 ", "parent_ref": 1}],
            "weld_joints": [{"weld_number": "W1", "part_a_ref": 1, "part_b_ref": " 2 "}]}
    validate_drawing_payload(data)
    assert [part["ref"] for part in data["parts"]] == ["1", "2"]
    assert data["parts"][1]["parent_ref"] == "1"
    assert data["weld_joints"][0]["part_a_ref"] == "1"
    assert data["weld_joints"][0]["part_b_ref"] == "2"


@pytest.mark.parametrize("refs", [["A", "A"], [1, "1"], ["A", " A "]])
def test_ambiguous_part_references_fail_before_persistence(refs):
    with pytest.raises(AIExtractionRunError) as error:
        validate_drawing_payload({"parts": [{"ref": ref} for ref in refs]})
    assert error.value.code == "duplicate_part_reference"
    assert error.value.status_code == 422


def test_missing_references_receive_distinct_internal_ids():
    data = {"parts": [{"ref": "part-2"}, {"ref": "  "}, {"ref": None}]}
    validate_drawing_payload(data)
    assert len({part["ref"] for part in data["parts"]}) == 3


def test_boolean_reference_is_not_silently_converted_to_identifier():
    with pytest.raises(AIExtractionRunError) as error:
        validate_drawing_payload({"parts": [{"ref": True}]})
    assert error.value.code == "invalid_drawing_result"


@pytest.mark.parametrize("section,field,limit", [
    ("parts", "name", 200), ("parts", "material_spec", 200),
    ("parts", "part_number", 100), ("weld_joints", "weld_number", 100),
    ("weld_joints", "weld_position", 80),
])
def test_database_text_limits_are_checked_before_insert(section, field, limit):
    valid = {section: [{field: "中" * limit}]}
    validate_drawing_payload(valid)
    invalid = deepcopy(valid)
    invalid[section][0][field] += "中"
    with pytest.raises(AIExtractionRunError) as error:
        validate_drawing_payload(invalid)
    assert error.value.status_code == 422
    assert field in str(error.value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 10 ** 400])
@pytest.mark.parametrize("field", ["quantity", "thickness_mm", "confidence"])
def test_non_finite_numbers_are_rejected_before_schema_or_database_errors(value, field):
    with pytest.raises(AIExtractionRunError) as error:
        validate_drawing_payload({"parts": [{field: value}]})
    assert error.value.code == "invalid_drawing_result"
    assert error.value.status_code == 422
    assert f"parts.0.{field}" in str(error.value)


@pytest.mark.parametrize("section,field,value", [
    ("parts", "quantity", 0), ("parts", "quantity", -1),
    ("parts", "quantity", 2147483648), ("parts", "quantity", 1.5),
    ("parts", "thickness_mm", 0), ("parts", "thickness_mm", -2),
    ("parts", "confidence", 1.1), ("weld_joints", "confidence", -0.1),
    ("weld_joints", "root_gap", -1), ("weld_joints", "root_face", -1),
    ("weld_joints", "groove_angle", -30), ("weld_joints", "weld_size", 0),
    ("weld_joints", "length_mm", 0), ("weld_joints", "diameter_mm", -1),
])
def test_invalid_engineering_numbers_cannot_be_saved_or_replaced_with_defaults(section, field, value):
    with pytest.raises(AIExtractionRunError) as error:
        validate_drawing_payload({section: [{field: value}]})
    assert error.value.status_code == 422
    assert field in str(error.value)


def test_unknown_dimensions_and_zero_gap_remain_valid_partial_findings():
    payload = {"parts": [{"ref": "A", "quantity": None, "thickness_mm": None}],
               "weld_joints": [{"root_gap": 0, "root_face": 0, "groove_angle": 0,
                                "length_mm": None, "confidence": 0}]}
    original = deepcopy(payload)
    validate_drawing_payload(payload)
    assert payload == original


@pytest.mark.parametrize("bbox", [[0, 0, 1, 1.01], [-0.1, 0, 0.5, 1]])
def test_provider_evidence_outside_image_is_rejected_before_coordinate_transform(bbox):
    with pytest.raises(AIExtractionRunError):
        validate_drawing_payload({"parts": [{"ref": "A", "evidence": {"page": 1, "bbox": bbox}}]})


@pytest.mark.parametrize("parents", [
    [("A", "A")], [("A", "B"), ("B", "A")],
    [("C", "A"), ("A", "B"), ("B", "C")],
])
def test_ai_assembly_cycles_are_rejected(parents):
    with pytest.raises(AIExtractionRunError) as error:
        validate_drawing_payload({"parts": [{"ref": ref, "parent_ref": parent} for ref, parent in parents]})
    assert error.value.code == "cyclic_part_reference"
    assert error.value.status_code == 422


def test_deep_valid_assembly_does_not_exceed_python_recursion_limit():
    parts = [{"ref": str(i), "parent_ref": str(i + 1)} for i in range(1500)]
    parts[-1]["parent_ref"] = None
    validate_drawing_payload({"parts": parts})


def test_missing_parent_is_retained_for_review_with_explicit_risk():
    payload = {"parts": [{"ref": "A", "parent_ref": "missing"}]}
    validate_drawing_payload(payload)
    risks = drawing_risks(payload, 1)
    assert payload["parts"][0]["parent_ref"] == "missing"
    assert any(risk["code"] == "unresolved_parent_part" for risk in risks)


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), -float("inf"), 10 ** 400])
def test_invalid_evidence_coordinates_are_not_converted_to_plausible_boxes(value):
    result = clean_evidence({"page": True, "bbox": [0, 0, value, 1]}, 1)
    assert result["page"] is None
    assert result["bbox"] == []


@pytest.mark.parametrize("payload", [
    {"product": "bad", "parts": [{"ref": "A"}]},
    {"product": {"evidence": "bad"}, "parts": [{"ref": "A"}]},
    {"product": {"confidence": "high"}, "parts": [{"ref": "A"}]},
    {"parts": [{"ref": "A", "quantity": float("inf")}]},
    {"parts": [{"ref": "A", "parent_ref": "A"}]},
])
def test_text_provider_result_is_validated_before_identity_reads_or_replacing_saved_data(payload):
    db = Mock()
    revision = SimpleNamespace(
        id="revision-1", drawing_document_id="document-1", status="draft",
        parse_status="completed", access_level="private", drawing_metadata={"previous": "valid"},
        data_version=1,
    )
    queries = {model: Mock() for model in (DocumentPage, SourceDocument, ProductRevision, DrawingParseRun, ExtractionJob)}
    queries[DocumentPage].filter.return_value.order_by.return_value.all.return_value = [
        SimpleNamespace(page_number=1, text_content="drawing text")
    ]
    queries[SourceDocument].filter.return_value.one.return_value = SimpleNamespace(
        original_filename="drawing.doc", storage_key="private/drawing.doc"
    )
    queries[ProductRevision].filter.return_value.first.return_value = revision
    queries[DrawingParseRun].filter.return_value.first.return_value = None
    queries[ExtractionJob].filter.return_value.first.return_value = None
    queries[ProductRevision].filter.return_value.with_for_update.return_value.first.return_value = revision
    queries[ExtractionJob.id] = queries[ExtractionJob]
    db.add.side_effect = lambda row: setattr(row, "created_at", datetime(2026, 9, 5)) if isinstance(row, ExtractionJob) else None
    db.query.side_effect = lambda model: queries[model]
    service = EngineeringService(db)
    service._get = Mock(return_value=revision)
    service._replace_extracted_data = Mock()
    provider = Mock(provider_name="test", model_name="test")
    provider.structured_response.return_value = AIProviderResult(payload, None, 1, 1, 2)
    with patch("app.services.engineering_service.AIQuotaService") as quota:
        with patch("app.services.engineering_service.drawing_identity_problems") as identity:
            with pytest.raises(AIExtractionRunError) as error:
                service.parse_revision(
                    revision.id, None, provider, "byok", None, SimpleNamespace(id=7),
                    WorkspaceContext(user_id=7, workspace_type=WorkspaceType.PERSONAL), Mock(),
                )
    assert error.value.status_code == 422
    identity.assert_not_called()
    service._replace_extracted_data.assert_not_called()
    db.rollback.assert_called_once()
    quota.return_value.settle.assert_not_called()
    assert revision.drawing_metadata == {"previous": "valid"}
    assert revision.parse_status == "failed"

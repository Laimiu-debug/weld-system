from datetime import date, timedelta
from io import BytesIO
from types import SimpleNamespace as NS

import pytest
from PIL import Image
from pydantic import ValidationError
from reportlab.pdfgen import canvas

from app.schemas.engineering import DrawingAIRequest
from app.services.execution_validation_service import (
    parameter_report,
    parse_range,
    inspection_closed,
)
from app.services.drawing_preprocessing_service import (
    prepare_drawing_page,
    restore_payload_evidence,
)
from app.services.document_parser_service import (
    DefaultDocumentParser,
    _pdf_page_has_images,
)
from app.services.drawing_review_service import completeness_report


@pytest.mark.parametrize(
    "value,expected",
    [
        ("90-130 A", (90, 130)),
        ("90A～130A", (90, 130)),
        ("≤130A", (None, 130)),
        (">=90 A", (90, None)),
        ("100 A", (100, 100)),
    ],
)
def test_explicit_parameter_range_formats(value, expected):
    assert parse_range(value, "A") == expected


@pytest.mark.parametrize(
    "value", ["130-90A", "90-130mA", "layer1:90 layer2:130", "NaN", "90/130", True]
)
def test_ambiguous_or_conflicting_range_is_not_guessed(value):
    with pytest.raises(ValueError):
        parse_range(value, "A")


@pytest.mark.parametrize(
    "actual",
    [
        {},
        {"current": 89},
        {"current": 131},
        {"current": True},
        {"current": float("nan")},
    ],
)
def test_missing_or_outside_frozen_range_fails(actual):
    assert not parameter_report({"current_range": "90-130 A"}, actual)["passed"]


def test_all_frozen_limits_are_required_and_inclusive():
    wps = {
        "current_range": "90-130 A",
        "heat_input_min": 0.5,
        "heat_input_max": 2,
        "preheat_temp_min": 50,
        "interpass_temp_max": 150,
    }
    actual = {
        "current": 90,
        "heat_input": 2,
        "preheat_temperature": 50,
        "interpass_temperature": 150,
    }
    assert parameter_report(wps, actual)["passed"]
    assert not parameter_report(wps, {**actual, "heat_input": 2.1})["passed"]
    assert not parameter_report({}, actual)["passed"]
    assert not parameter_report(
        {"travel_speed": "90-130 mm/min", "welding_speed": "150-200 mm/min"},
        {"travel_speed": 100},
    )["passed"]


def repaired():
    return NS(
        inspection_result="fail",
        repair_required=True,
        repair_description="返修完成",
        inspection_date=date.today() - timedelta(days=1),
        reinspection_date=date.today(),
        reinspection_result="pass",
        reinspection_inspector_id=1,
        reinspection_notes="复验合格",
    )


@pytest.mark.parametrize(
    "field",
    [
        "repair_description",
        "reinspection_date",
        "reinspection_result",
        "reinspection_inspector_id",
        "reinspection_notes",
    ],
)
def test_repair_closure_requires_actual_followup_fields(field):
    item = repaired()
    assert inspection_closed(item)
    setattr(item, field, None)
    assert not inspection_closed(item)


@pytest.mark.parametrize(
    "options",
    [
        {"page_numbers": [0]},
        {"page_numbers": [True]},
        {"page_numbers": [1, 1]},
        {"region": [0, 0, 1, 1]},
        {"page_numbers": [1], "region": [0.9, 0, 0.1, 1]},
        {"page_numbers": [1], "region": [0, 0, float("nan"), 1]},
        {"page_rotations": {1: 45}},
        {"retry_job_id": "x", "page_numbers": [1]},
    ],
)
def test_scoped_request_rejects_invalid_input(options):
    with pytest.raises(ValidationError):
        DrawingAIRequest(mode="offline", **options)


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("size", [(600, 400), (400, 600)])
def test_whole_input_preserved_and_scoped_coordinates_restore(rotation, size):
    source = Image.new("RGB", size, "white")
    source.putpixel((0, 0), (255, 0, 0))  # A title can be at any corner.
    stream = BytesIO()
    source.save(stream, format="PNG")
    prepared = prepare_drawing_page(stream.getvalue(), 2, rotation_degrees=rotation)
    with Image.open(BytesIO(prepared.full_png)) as full:
        assert full.tobytes() == source.rotate(rotation, expand=True).tobytes()
    prepared = prepare_drawing_page(
        stream.getvalue(), 2, rotation_degrees=rotation, region=[0.2, 0.3, 0.8, 0.9]
    )
    payload = {"parts": [{"evidence": {"page": 2, "bbox": [0, 0, 1, 1]}}]}
    restore_payload_evidence(payload, [prepared])
    assert payload["parts"][0]["evidence"]["bbox"] == pytest.approx(
        [0.2, 0.3, 0.8, 0.9]
    )


def test_searchable_header_with_vector_body_requests_ocr():
    stream = BytesIO()
    pdf = canvas.Canvas(stream)
    pdf.drawString(10, 700, "Searchable PQR header with more than twenty characters")
    path = pdf.beginPath()
    path.moveTo(10, 10)
    for i in range(100):
        path.lineTo(i + 10, i % 20 + 10)
    pdf.drawPath(path)
    pdf.save()
    stream.seek(0)
    page = DefaultDocumentParser().parse(stream, "pqr.pdf").pages[0]
    assert page.ocr_status == "pending" and page.metadata["vector_outline_candidate"]
    assert "Searchable" in page.text_content


def test_nested_form_image_detection_and_cycle_safety():
    image = {"/Subtype": "/Image"}
    form = {"/Subtype": "/Form", "/Resources": {"/XObject": {"image": image}}}
    page = {"/Resources": {"/XObject": {"form": form}}}
    assert _pdf_page_has_images(page)
    form["/Resources"]["/XObject"]["cycle"] = form
    assert _pdf_page_has_images(page)


def test_completeness_distinguishes_counts_from_unknown_coverage():
    revision = NS(
        drawing_page_count=3,
        drawing_metadata={
            "recognition_coverage": {
                "pages": [1, 2],
                "unresolved_regions": [{"reason": "不可读"}],
            }
        },
    )
    parts = [NS(id="p", name="Plate", quantity=None, evidence={})]
    joints = [
        NS(id=str(i), weld_number="W1", part_a_id="p", part_b_id=None, evidence={})
        for i in range(2)
    ]
    report = completeness_report(revision, parts, joints)
    assert report["unrecognized_pages"] == [3]
    assert report["duplicate_weld_numbers"] == ["W1"]
    assert report["unknown_quantities"] == ["Plate"]
    assert len(report["missing_evidence"]) == 3


def test_region_evidence_cannot_claim_an_unseen_page():
    stream = BytesIO()
    Image.new("RGB", (100, 100), "white").save(stream, format="PNG")
    prepared = prepare_drawing_page(stream.getvalue(), 2, region=[0.1, 0.2, 0.8, 0.9])
    payload = {
        "parts": [{"evidence": {"page": 1, "bbox": [0, 0, 1, 1], "text": "unverified"}}]
    }
    restore_payload_evidence(payload, [prepared])
    assert payload["parts"][0]["evidence"] == {
        "page": None,
        "bbox": None,
        "text": "unverified",
    }


def test_cancel_refunds_even_if_broker_revoke_is_unavailable(monkeypatch):
    from unittest.mock import Mock
    from app.api.v1.endpoints import smart_import as endpoint

    db, user, context = Mock(), NS(id=7), NS()
    job = NS(id="job", document_id="doc", status="cancelled")
    queue, quota, documents = Mock(), Mock(), Mock()
    queue.cancel_job.return_value = job
    monkeypatch.setattr(endpoint, "resolve_workspace", lambda *args: context)
    monkeypatch.setattr(endpoint, "AIExtractionQueueService", lambda *args: queue)
    monkeypatch.setattr(endpoint, "AIQuotaService", lambda *args: quota)
    monkeypatch.setattr(endpoint, "SmartImportService", lambda *args: documents)
    monkeypatch.setattr(
        endpoint.celery_app.control,
        "revoke",
        Mock(side_effect=RuntimeError("broker down")),
    )
    assert endpoint.cancel_extraction_job("job", db, user, None) is job
    quota.refund.assert_called_once_with("job", user, context, "用户取消后台任务")

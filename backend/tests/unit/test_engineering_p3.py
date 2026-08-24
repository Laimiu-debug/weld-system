from app.models.engineering import (
    EngineeringDependencyState,
    EngineeringProject,
    EngineeringReviewRecord,
    Part,
    Product,
    ProductRevision,
    WeldJoint,
    WeldRequirement,
)
from app.models.smart_import import ImportBatch, SourceDocument
from app.services.engineering_service import (
    DRAWING_SCHEMA,
    clean_evidence,
    drawing_risks,
    EngineeringService,
    validate_drawing_identity,
)
from app.services.ai_extraction_service import AIExtractionRunError
from app.services.ai_provider_service import AIProviderError


def test_engineering_models_include_workspace_and_version_isolation() -> None:
    for model in (
        EngineeringProject,
        Product,
        ProductRevision,
        Part,
        WeldJoint,
        WeldRequirement,
        EngineeringReviewRecord,
        EngineeringDependencyState,
    ):
        columns = set(model.__table__.columns.keys())
        assert {
            "user_id",
            "workspace_type",
            "company_id",
            "factory_id",
            "access_level",
            "created_by",
        } <= columns
    assert {
        "drawing_document_id",
        "drawing_sha256",
        "revision_number",
        "data_version",
    } <= set(ProductRevision.__table__.columns.keys())
    assert Part.__table__.columns["parent_part_id"].foreign_keys


def test_smart_import_storage_accepts_drawing_documents() -> None:
    batch_constraint = " ".join(
        str(c.sqltext)
        for c in ImportBatch.__table__.constraints
        if hasattr(c, "sqltext")
    )
    document_constraint = " ".join(
        str(c.sqltext)
        for c in SourceDocument.__table__.constraints
        if hasattr(c, "sqltext")
    )
    assert "drawing" in batch_constraint
    assert "drawing" in document_constraint


def test_evidence_is_normalized_and_invalid_boxes_remain_unlocated() -> None:
    assert clean_evidence({"page": 2, "bbox": [-1, 0.2, 1.4, 0.8], "text": "A"}, 3) == {
        "page": 2,
        "bbox": [0.0, 0.2, 1.0, 0.8],
        "text": "A",
    }
    assert clean_evidence({"page": 9, "bbox": [0.4, 0.4, 0.2, 0.3]}, 3)["bbox"] == []


def test_drawing_risks_flag_duplicates_missing_critical_data_and_evidence() -> None:
    payload = {
        "parts": [{"ref": "P1"}],
        "weld_joints": [
            {
                "weld_number": "W1",
                "part_a_ref": "P1",
                "part_b_ref": None,
                "joint_type": None,
                "groove_type": None,
                "evidence": {},
            },
            {
                "weld_number": "W1",
                "part_a_ref": "P1",
                "part_b_ref": "P2",
                "joint_type": "butt",
                "groove_type": "V",
                "evidence": {"page": 1, "bbox": [0.1, 0.1, 0.2, 0.2]},
            },
        ],
        "unresolved_regions": [],
    }
    codes = {risk["code"] for risk in drawing_risks(payload, 1)}
    assert {
        "duplicate_weld_number",
        "insufficient_weld_data",
        "unresolved_part",
        "missing_evidence",
    } <= codes


def test_pressure_vessel_schema_requires_traceable_structured_sections() -> None:
    assert set(DRAWING_SCHEMA["required"]) == {
        "product",
        "parts",
        "weld_joints",
        "unresolved_regions",
    }
    weld = DRAWING_SCHEMA["properties"]["weld_joints"]["items"]
    assert {"nde_methods", "pwht_required", "impact_required", "evidence"} <= set(
        weld["required"]
    )
    product = DRAWING_SCHEMA["properties"]["product"]
    assert {"confidence", "evidence"} <= set(product["required"])


def test_drawing_identity_rejects_hallucinated_number() -> None:
    payload = {
        "product": {
            "drawing_number": "YK-5-03-014",
            "product_name": "储气罐1",
            "confidence": 0.95,
            "evidence": {
                "drawing_number": {
                    "page": 1,
                    "bbox": [0.1, 0.1, 0.2, 0.2],
                    "text": "YK-5-03-014",
                },
                "product_name": {
                    "page": 1,
                    "bbox": [0.2, 0.2, 0.3, 0.3],
                    "text": "储气罐1",
                },
            },
        }
    }

    with pytest.raises(AIExtractionRunError) as exc_info:
        validate_drawing_identity(
            payload, "26047-100立方米XAI液化缓冲罐.pdf", 1
        )

    assert exc_info.value.code == "drawing_identity_unverified"
    assert "文件名编号不一致" in str(exc_info.value)


def test_drawing_identity_accepts_located_title_values() -> None:
    payload = {
        "product": {
            "drawing_number": "26047-001",
            "product_name": "XAI液化缓冲罐",
            "confidence": 0.91,
            "evidence": {
                "drawing_number": {
                    "page": 1,
                    "bbox": [0.1, 0.1, 0.2, 0.2],
                    "text": "图号 26047-001",
                },
                "product_name": {
                    "page": 1,
                    "bbox": [0.2, 0.2, 0.3, 0.3],
                    "text": "XAI液化缓冲罐",
                },
            },
        }
    }

    validate_drawing_identity(payload, "26047-100立方米XAI液化缓冲罐.pdf", 1)


def test_drawing_provider_rejection_becomes_user_facing_run_error() -> None:
    db = Mock()
    pages_query = Mock()
    pages_query.filter.return_value.order_by.return_value.all.return_value = [
        SimpleNamespace(page_number=1, text_content="drawing text")
    ]
    document_query = Mock()
    document_query.filter.return_value.one.return_value = SimpleNamespace(
        original_filename="drawing.doc", storage_key="private/drawing.doc"
    )
    revision_query = Mock()
    run_query = Mock()
    job_query = Mock()
    db.query.side_effect = [
        pages_query,
        document_query,
        revision_query,
        run_query,
        job_query,
    ]
    revision = SimpleNamespace(
        id="revision-1",
        drawing_document_id="document-1",
        drawing_page_count=1,
        status="draft",
        parse_status="pending",
        access_level="private",
        user_id=7,
        workspace_type="personal",
        company_id=None,
        factory_id=None,
    )
    revision_query.filter.return_value.first.return_value = revision
    run_query.filter.return_value.first.return_value = None
    job_query.filter.return_value.first.return_value = None
    service = EngineeringService(db)
    service._get = Mock(return_value=revision)
    provider = Mock(provider_name="openai_compatible_chat", model_name="text-only")
    provider.structured_response.side_effect = AIProviderError(
        "provider_rejected", "AI 服务拒绝了本次请求"
    )
    user = SimpleNamespace(id=7)
    context = WorkspaceContext(user_id=7, workspace_type=WorkspaceType.PERSONAL)

    with patch("app.services.engineering_service.AIQuotaService"):
        with pytest.raises(AIExtractionRunError) as exc_info:
            service.parse_revision(
                revision.id,
                None,
                provider,
                "byok",
                None,
                user,
                context,
                Mock(),
            )

    assert exc_info.value.code == "provider_rejected"
    assert exc_info.value.status_code == 422
    assert "拒绝" in str(exc_info.value)
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.core.data_access import WorkspaceContext, WorkspaceType

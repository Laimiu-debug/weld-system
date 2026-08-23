from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.core.data_access import WorkspaceContext, WorkspaceType
from app.models.smart_import import (
    AIPlanEntitlement,
    AIUsageLedger,
    ExtractedEntity,
    ExtractedField,
    ExtractionJob,
    SourceDocument,
)
from app.schemas.smart_import import FieldReviewRequest, FormPublishRequest
from app.services.ai_quota_service import AIQuotaError, AIQuotaService
from app.services.smart_import_review_service import SmartImportReviewService


def _user() -> SimpleNamespace:
    return SimpleNamespace(id=7, member_tier="personal_pro")


def _context() -> WorkspaceContext:
    return WorkspaceContext(user_id=7, workspace_type=WorkspaceType.PERSONAL)


def _entity(entity_type: str = "pqr") -> ExtractedEntity:
    return ExtractedEntity(
        id="entity-1",
        document_id="document-1",
        job_id="job-1",
        entity_type=entity_type,
        source_mode="ai",
        status="draft",
        draft_data={},
        version=1,
        is_current=True,
        user_id=7,
        workspace_type="personal",
        access_level="private",
        created_at=datetime(2026, 1, 1),
    )


def _field(key: str, value: object, field_id: str) -> ExtractedField:
    return ExtractedField(
        id=field_id,
        entity_id="entity-1",
        module_id="pqr_basic_info",
        instance_id="basic-1",
        field_key=key,
        raw_value=value,
        normalized_value=value,
        confidence=0.9,
        review_status="pending",
        schema_version="1.0",
        user_id=7,
        workspace_type="personal",
        access_level="private",
    )


def test_platform_quota_reserves_points_and_rejects_overage() -> None:
    db = Mock()
    service = AIQuotaService(db)
    service._ledger = Mock(return_value=None)
    service._get_entitlement = Mock(
        return_value=SimpleNamespace(
            is_enabled=True,
            daily_points=20,
            monthly_points=100,
            max_points_per_task=30,
            max_pages_per_task=30,
        )
    )
    service._used_points = Mock(return_value=92)
    service._used_points_since = Mock(return_value=4)
    job = ExtractionJob(id="job-1", mode="platform", provider="openai", model="m")

    points = service.reserve(job, _user(), _context(), 5)

    assert points == 5
    ledger = db.add.call_args.args[0]
    assert isinstance(ledger, AIUsageLedger)
    assert ledger.transaction_type == "reservation"
    assert ledger.balance_delta == -5
    assert ledger.idempotency_key == "reserve:job-1"

    service._used_points.return_value = 98
    with pytest.raises(AIQuotaError) as exc_info:
        service.reserve(ExtractionJob(id="job-2"), _user(), _context(), 5)
    assert exc_info.value.code == "ai_quota_exhausted"


def test_workspace_and_enterprise_user_task_limits_apply_to_byok_too() -> None:
    service = AIQuotaService(Mock())
    service._get_entitlement = Mock(
        return_value=SimpleNamespace(
            is_enabled=True,
            max_pages_per_task=30,
            max_tasks_per_day=100,
            max_tasks_per_month=1000,
            max_concurrent_tasks=10,
            max_user_tasks_per_day=20,
            max_user_tasks_per_month=200,
            max_user_concurrent_tasks=2,
        )
    )
    enterprise = WorkspaceContext(
        user_id=7,
        workspace_type=WorkspaceType.ENTERPRISE,
        company_id=3,
    )
    service._job_count = Mock(side_effect=[10, 50, 3, 5, 40, 2])

    with pytest.raises(AIQuotaError) as exc_info:
        service.enforce_task_limits(_user(), enterprise, pages=5)

    assert exc_info.value.code == "ai_user_concurrent_limit"


def test_single_task_page_limit_is_shared_by_platform_and_byok() -> None:
    service = AIQuotaService(Mock())
    service._get_entitlement = Mock(
        return_value=SimpleNamespace(is_enabled=True, max_pages_per_task=3)
    )

    with pytest.raises(AIQuotaError) as exc_info:
        service.enforce_task_limits(_user(), _context(), pages=4)

    assert exc_info.value.code == "ai_task_limit_exceeded"


def test_quota_settlement_records_tokens_without_charging_byok() -> None:
    db = Mock()
    service = AIQuotaService(db)
    service._ledger = Mock(return_value=None)
    job = ExtractionJob(
        id="job-1",
        mode="byok",
        provider="openai_responses",
        model="model",
        input_tokens=100,
        output_tokens=20,
        total_tokens=120,
    )

    service.settle(job, _user(), _context(), 3)

    ledger = db.add.call_args.args[0]
    assert ledger.source == "byok"
    assert ledger.points == 0
    assert ledger.balance_delta == 0
    assert ledger.total_tokens == 120


def test_failed_platform_job_refunds_reserved_points_once() -> None:
    db = Mock()
    service = AIQuotaService(db)
    reservation = SimpleNamespace(points=4)
    service._ledger = Mock(
        side_effect=lambda key: reservation if key == "reserve:job-1" else None
    )
    job_query = Mock()
    job_query.filter.return_value.first.return_value = ExtractionJob(
        id="job-1", mode="platform", provider="openai", model="model"
    )
    db.query.return_value = job_query

    service.refund("job-1", _user(), _context(), "provider timeout")

    ledger = db.add.call_args.args[0]
    assert ledger.transaction_type == "refund"
    assert ledger.balance_delta == 4
    assert ledger.metadata_json["reason"] == "provider timeout"


def test_correct_field_updates_draft_and_creates_audit_record() -> None:
    db = Mock()
    entity = _entity()
    field = _field("pqr_number", "PQR-OLD", "field-1")
    field_query = Mock()
    field_query.filter.return_value.first.return_value = field
    pending_query = Mock()
    pending_query.filter.return_value.count.return_value = 0
    db.query.side_effect = [field_query, pending_query]
    service = SmartImportReviewService(db)
    service.get_entity = Mock(return_value=entity)

    result = service.review_field(
        entity.id,
        field.id,
        FieldReviewRequest(action="correct", value="PQR-001", reason="核对原件"),
        _user(),
        _context(),
    )

    assert result.source_mode == "mixed"
    assert result.status == "review"
    assert result.draft_data == {"basic-1": {"pqr_number": "PQR-001"}}
    assert field.review_status == "corrected"
    audit = db.add.call_args.args[0]
    assert audit.action == "correct"
    assert audit.previous_value == "PQR-OLD"
    assert audit.new_value == "PQR-001"


def test_publish_requires_all_fields_reviewed() -> None:
    db = Mock()
    entity = _entity()
    pending = _field("pqr_number", "PQR-001", "field-1")
    existing_query = Mock()
    existing_query.filter.return_value.order_by.return_value.first.return_value = None
    fields_query = Mock()
    fields_query.filter.return_value.all.return_value = [pending]
    db.query.side_effect = [existing_query, fields_query]
    service = SmartImportReviewService(db)
    service.get_entity = Mock(return_value=entity)

    with pytest.raises(HTTPException) as exc_info:
        service.publish(entity.id, _user(), _context())

    assert exc_info.value.status_code == 409


def test_publish_rejects_conflicting_fixed_field_values() -> None:
    service = SmartImportReviewService(Mock())
    first = _field("pqr_number", "PQR-001", "field-1")
    second = _field("pqr_number", "PQR-002", "field-2")
    first.review_status = "accepted"
    second.review_status = "accepted"

    with pytest.raises(HTTPException) as exc_info:
        service._build_payload(_entity(), [first, second], None)

    assert exc_info.value.status_code == 409
    assert "多个已确认值" in exc_info.value.detail


def test_publish_maps_custom_semantic_field_to_fixed_column_and_module_data() -> None:
    service = SmartImportReviewService(Mock())
    number = _field("enterprise_pqr_no", "PQR-SEM-001", "field-number")
    number.canonical_field_key = "document.number"
    title = _field("title", "Semantic PQR", "field-title")
    number.review_status = "accepted"
    title.review_status = "accepted"
    job = ExtractionJob(
        id="job-1",
        schema_snapshot={
            "field_bindings": [
                {
                    "module_id": "pqr_basic_info",
                    "instance_id": "basic-1",
                    "field_key": "enterprise_pqr_no",
                    "canonical_field_key": "document.number",
                },
                {
                    "module_id": "alternate_info",
                    "instance_id": "alternate-1",
                    "field_key": "rejected_number_alias",
                    "canonical_field_key": "document.number",
                },
            ]
        },
    )

    payload = service._build_payload(_entity(), [number, title], job)

    assert payload["pqr_number"] == "PQR-SEM-001"
    assert (
        payload["modules_data"]["basic-1"]["data"]["enterprise_pqr_no"] == "PQR-SEM-001"
    )
    assert "alternate-1" not in payload["modules_data"]


def test_pqr_publish_uses_existing_service_and_keeps_formal_record_draft() -> None:
    db = Mock()
    entity = _entity()
    number = _field("pqr_number", "PQR-001", "field-number")
    title = _field("title", "Imported PQR", "field-title")
    number.review_status = "accepted"
    title.review_status = "corrected"
    job = ExtractionJob(id="job-1", template_id="template-1")
    document = SourceDocument(id="document-1", batch_id="batch-1")
    existing_query = Mock()
    existing_query.filter.return_value.order_by.return_value.first.return_value = None
    fields_query = Mock()
    fields_query.filter.return_value.all.return_value = [number, title]
    job_query = Mock()
    job_query.filter.return_value.first.return_value = job
    document_query = Mock()
    document_query.filter.return_value.first.return_value = document
    db.query.side_effect = [existing_query, fields_query, job_query, document_query]
    service = SmartImportReviewService(db)
    service.get_entity = Mock(return_value=entity)
    service._check_formal_quota = Mock()
    service._increment_formal_quota = Mock()
    service.smart_import.get_batch = Mock(
        return_value=SimpleNamespace(
            processed_documents=1, total_documents=1, status="review", progress=100
        )
    )

    with patch(
        "app.services.smart_import_review_service.PQRService.create",
        return_value=SimpleNamespace(id=101),
    ) as create:
        record = service.publish(entity.id, _user(), _context())

    payload = create.call_args.kwargs["obj_in"]
    assert payload.pqr_number == "PQR-001"
    assert payload.title == "Imported PQR"
    assert payload.template_id == "template-1"
    assert payload.modules_data["basic-1"]["data"]["pqr_number"] == "PQR-001"
    assert record.target_entity_id == "101"
    assert entity.status == "published"


def test_wps_quick_publish_requires_existing_form_and_pqr_confirmation() -> None:
    db = Mock()
    entity = _entity("wps")
    existing_query = Mock()
    existing_query.filter.return_value.order_by.return_value.first.return_value = None
    db.query.return_value = existing_query
    service = SmartImportReviewService(db)
    service.get_entity = Mock(return_value=entity)

    with pytest.raises(HTTPException) as exc_info:
        service.publish(entity.id, _user(), _context())

    assert exc_info.value.status_code == 409
    assert "确认支持 PQR" in exc_info.value.detail


def test_wps_existing_form_can_save_without_pqr_but_marks_capability_ineligible() -> (
    None
):
    db = Mock()
    entity = _entity("wps")
    existing_query = Mock()
    existing_query.filter.return_value.order_by.return_value.first.return_value = None
    fields_query = Mock()
    fields_query.filter.return_value.all.return_value = []
    db.query.side_effect = [existing_query, fields_query]
    service = SmartImportReviewService(db)
    service.get_entity = Mock(return_value=entity)
    service._check_formal_quota = Mock()
    service._increment_formal_quota = Mock()
    request = FormPublishRequest(
        payload={"wps_number": "WPS-FORM-1", "title": "Imported form"},
        supporting_pqr_decision="no_match",
    )

    with patch(
        "app.services.smart_import_review_service.WPSService.create",
        return_value=SimpleNamespace(id=303),
    ) as create:
        record = service.publish_form(entity.id, request, _user(), _context())

    payload = create.call_args.kwargs["obj_in"]
    control = payload.modules_data["_import_control"]["data"]
    assert payload.status == "draft"
    assert control["supporting_pqr_decision"] == "no_match"
    assert control["capability_eligible"] is False
    assert record.target_entity_id == "303"


def test_ai_entitlement_model_is_data_driven() -> None:
    columns = AIPlanEntitlement.__table__.columns
    assert {
        "tier_key",
        "daily_points",
        "monthly_points",
        "max_points_per_task",
        "max_tasks_per_day",
        "max_user_concurrent_tasks",
    }.issubset(columns.keys())
    assert date(2026, 1, 1).day == 1

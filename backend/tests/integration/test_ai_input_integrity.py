"""Real local PostgreSQL, real document rendering, deterministic provider boundary."""
import os
from copy import deepcopy
from datetime import datetime, timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from reportlab.pdfgen import canvas
from sqlalchemy.exc import DataError

from test_foundation_integrity import sessions, db, user
from app.core.data_access import WorkspaceContext
from app.models.engineering import Part, DrawingParseRun, ProductRevision
from app.models.smart_import import (
    ExtractionJob,
    DocumentPage,
    SourceDocument,
    ImportBatch,
    ExtractedEntity,
    ExtractedField,
)
from app.schemas.engineering import ProjectCreate, ProductCreate, DrawingAIRequest
from app.services.document_storage_service import LocalDocumentStorage
from app.services.engineering_service import EngineeringService
from app.services.ai_extraction_service import AIExtractionService, AIExtractionRunError
from app.services.ai_provider_service import AIProviderResult, AIProviderError
from app.services.ai_routing_service import routing_snapshot
from app.api.v1.endpoints.engineering import queue_drawing, drawing_jobs
from app.tasks import smart_import_tasks as worker

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LOCAL_DB_TESTS") != "1", reason="local PostgreSQL opt-in"
)


def pdf_bytes():
    out = BytesIO()
    pdf = canvas.Canvas(out)
    pdf.drawString(30, 600, "PQR: TEST-001; drawing TEST-001; Plate 12 mm")
    pdf.save()
    return out.getvalue()


def drawing(db, tmp_path):
    owner = user(db)
    db.commit()
    context = WorkspaceContext(user_id=owner.id, workspace_type="personal")
    service = EngineeringService(db)
    project = service.create_project(
        ProjectCreate(code=uuid4().hex, name="QA"), owner, context
    )
    product = service.create_product(
        project.id, ProductCreate(code=uuid4().hex, name="QA"), owner, context
    )
    storage = LocalDocumentStorage(tmp_path)
    rev = service.upload_drawing(
        product.id,
        BytesIO(pdf_bytes()),
        "TEST-001.pdf",
        owner,
        context,
        storage,
        1000000,
    )
    return owner, context, rev, storage


class DrawingProvider:
    provider_name = "openai_compatible_chat"
    model_name = "qa"

    def __init__(self, fail_stage=None):
        self.requests = []
        self.fail_stage = fail_stage

    def structured_response(self, request):
        self.requests.append(request)
        if self.fail_stage == len(self.requests):
            raise AIProviderError("provider_timeout", "AI 服务响应超时", True)
        values = [
            {
                "product": {
                    "drawing_number": "TEST-001",
                    "product_name": "QA",
                    "evidence": {},
                },
                "unresolved_regions": [],
            },
            {
                "parts": [
                    {"ref": "A", "name": "Plate", "quantity": 2, "thickness_mm": 12}
                ],
                "unresolved_regions": [],
            },
            {
                "weld_joints": [{"weld_number": "W1", "part_a_ref": "A"}],
                "unresolved_regions": [],
            },
        ]
        return AIProviderResult(
            deepcopy(
                values[
                    0
                    if "title" in request.schema_name
                    else 1
                    if "parts" in request.schema_name
                    else 2
                ]
            ),
            "qa-response",
            3,
            4,
            7,
        )

    def close(self):
        pass


def queue(db, owner, rev, **options):
    config = SimpleNamespace(
        id=None,
        provider="openai_compatible_chat",
        model="qa",
        base_url="http://localhost:9999/v1",
    )
    with patch(
        "app.api.v1.endpoints.engineering.resolve_offline_provider_config",
        return_value=config,
    ), patch("app.api.v1.endpoints.engineering.dispatch_extraction_job") as dispatch:
        result = queue_drawing(
            rev.id, DrawingAIRequest(mode="offline", **options), db, owner, None
        )
        assert dispatch.call_count == 1
    return result["job"].id


def run_job(sessions, job_id, provider, storage):
    with patch.object(worker, "SessionLocal", sessions), patch.object(
        worker, "build_provider", return_value=provider
    ), patch.object(worker, "get_document_storage", return_value=storage), patch.object(
        worker.settings, "AI_OFFLINE_BASE_URL", "http://localhost:9999/v1"
    ), patch.object(
        worker.settings, "AI_OFFLINE_MODEL", "qa"
    ), patch.object(
        worker.settings, "AI_OFFLINE_PROVIDER", "openai_compatible_chat"
    ):
        return worker.run_smart_import_extraction.run(job_id)


def test_queued_drawing_survives_new_session_and_duplicate_delivery(
    db, sessions, tmp_path
):
    owner, context, rev, storage = drawing(db, tmp_path)
    job_id = queue(db, owner, rev)
    with pytest.raises(HTTPException) as exc:
        queue(db, owner, rev)
    assert exc.value.status_code == 409
    db.rollback()
    provider = DrawingProvider()
    assert run_job(sessions, job_id, provider, storage)["status"] == "completed"
    assert run_job(sessions, job_id, provider, storage)["status"] == "completed"
    assert len(provider.requests) == 3
    assert all(request.images for request in provider.requests)
    assert provider.requests[0].images == provider.requests[1].images
    db.expire_all()
    job = db.get(ExtractionJob, job_id)
    assert (job.status, job.total_tokens) == ("completed", 21)
    assert db.query(Part).filter(Part.revision_id == rev.id).one().quantity == 2
    assert drawing_jobs(rev.id, db, owner, None)[0].id == job_id
    outsider = user(db)
    db.commit()
    with pytest.raises(HTTPException):
        drawing_jobs(rev.id, db, outsider, None)


def test_model_failure_preserves_old_data_and_new_job_retries(db, sessions, tmp_path):
    owner, context, rev, storage = drawing(db, tmp_path)
    EngineeringService(db).parse_revision(
        rev.id,
        {"parts": [{"ref": "old", "name": "Retained"}]},
        None,
        "manual",
        None,
        owner,
        context,
        storage,
    )
    job_id = queue(db, owner, rev)
    assert (
        run_job(sessions, job_id, DrawingProvider(fail_stage=2), storage)["status"]
        == "failed"
    )
    db.expire_all()
    assert db.get(ExtractionJob, job_id).error_code == "provider_timeout"
    assert db.query(Part).filter(Part.revision_id == rev.id).one().name == "Retained"
    new_id = queue(db, owner, rev)
    assert new_id != job_id
    assert (
        run_job(sessions, new_id, DrawingProvider(), storage)["status"] == "completed"
    )


def test_title_only_drawing_keeps_previous_parts_and_exposes_partial_identity(
    db, sessions, tmp_path
):
    owner, context, rev, storage = drawing(db, tmp_path)
    EngineeringService(db).parse_revision(
        rev.id,
        {"parts": [{"ref": "old", "name": "Retained"}]},
        None,
        "manual",
        None,
        owner,
        context,
        storage,
    )
    provider = DrawingProvider()
    original = provider.structured_response

    def title_only(request):
        result = original(request)
        if "product" in result.data:
            result.data["product"]["confidence"] = 0.9
            result.data["product"]["evidence"] = {
                field: {"page": 1, "bbox": [0.1, 0.1, 0.5, 0.3], "text": value}
                for field, value in [
                    ("drawing_number", "TEST-001"),
                    ("product_name", "QA"),
                ]
            }
        if "parts" in result.data:
            result.data["parts"] = []
        if "weld_joints" in result.data:
            result.data["weld_joints"] = []
        return result

    provider.structured_response = title_only
    job_id = queue(db, owner, rev)
    assert run_job(sessions, job_id, provider, storage)["status"] == "failed"
    db.expire_all()
    job = db.get(ExtractionJob, job_id)
    assert job.error_code == "drawing_detail_required"
    assert job.progress_detail["partial_product"]["drawing_number"] == "TEST-001"
    assert db.query(Part).filter(Part.revision_id == rev.id).one().name == "Retained"


def test_database_failure_rolls_back_replacement_and_hides_sql(db, sessions, tmp_path):
    owner, context, rev, storage = drawing(db, tmp_path)
    service = EngineeringService(db)
    service.parse_revision(
        rev.id,
        {"parts": [{"ref": "old", "name": "Retained"}]},
        None,
        "manual",
        None,
        owner,
        context,
        storage,
    )
    job_id = queue(db, owner, rev)
    original = EngineeringService._replace_extracted_data

    def fail(self, *args):
        original(self, *args)
        raise DataError("private-sql", {}, RuntimeError("private-value"))

    with patch.object(EngineeringService, "_replace_extracted_data", fail):
        assert (
            run_job(sessions, job_id, DrawingProvider(), storage)["status"] == "failed"
        )
    db.expire_all()
    job = db.get(ExtractionJob, job_id)
    assert job.error_code == "drawing_persistence_failed"
    assert "private" not in job.error_message
    assert db.query(Part).filter(Part.revision_id == rev.id).one().name == "Retained"


def test_queue_unavailable_is_retryable_and_worker_loss_recovers(
    db, sessions, tmp_path
):
    owner, context, rev, storage = drawing(db, tmp_path)
    job_id = queue(db, owner, rev)
    job = db.get(ExtractionJob, job_id)
    job.created_at = datetime.utcnow() - timedelta(hours=1)
    db.commit()
    with patch.object(worker, "SessionLocal", sessions):
        assert worker.recover_stale_jobs.run()["recovered"] == 1
    db.expire_all()
    assert db.get(ExtractionJob, job_id).error_code == "worker_timeout"
    assert db.get(ProductRevision, rev.id).parse_status == "failed"
    assert queue(db, owner, rev) != job_id


def test_edit_while_queued_rejects_stale_results_before_model_call(
    db, sessions, tmp_path
):
    owner, context, rev, storage = drawing(db, tmp_path)
    job_id = queue(db, owner, rev)
    rev.data_version += 1
    db.commit()
    provider = DrawingProvider()
    assert run_job(sessions, job_id, provider, storage)["status"] == "failed"
    assert provider.requests == []
    db.expire_all()
    assert db.get(ExtractionJob, job_id).error_code == "drawing_changed"
    assert db.get(ProductRevision, rev.id).parse_status == "failed"


def test_broker_failure_does_not_leave_drawing_stuck(db, tmp_path):
    owner, context, rev, storage = drawing(db, tmp_path)
    config = SimpleNamespace(
        id=None,
        provider="openai_compatible_chat",
        model="qa",
        base_url="http://localhost:9999/v1",
    )
    with patch(
        "app.api.v1.endpoints.engineering.resolve_offline_provider_config",
        return_value=config,
    ), patch(
        "app.api.v1.endpoints.engineering.dispatch_extraction_job",
        side_effect=HTTPException(503, "queue down"),
    ):
        with pytest.raises(HTTPException):
            queue_drawing(rev.id, DrawingAIRequest(mode="offline"), db, owner, None)
    db.refresh(rev)
    assert rev.parse_status == "failed"
    job = (
        db.query(ExtractionJob)
        .filter(ExtractionJob.document_id == rev.drawing_document_id)
        .one()
    )
    assert job.status == "failed"
    assert job.error_code == "queue_unavailable"


def test_cancelled_queue_can_retry_and_late_delivery_cannot_reset_new_job(
    db, sessions, tmp_path
):
    from app.services.ai_extraction_queue_service import AIExtractionQueueService

    owner, context, rev, storage = drawing(db, tmp_path)
    old_id = queue(db, owner, rev)
    AIExtractionQueueService(db).cancel_job(db.get(ExtractionJob, old_id))
    new_id = queue(db, owner, rev)
    assert (
        run_job(sessions, old_id, DrawingProvider(), storage)["status"] == "cancelled"
    )
    db.expire_all()
    assert db.get(ProductRevision, rev.id).parse_status == "processing"
    assert (
        run_job(sessions, new_id, DrawingProvider(), storage)["status"] == "completed"
    )


def test_pqr_ocr_retry_reuses_good_pages_and_persists_fields(db, tmp_path):
    owner, context, rev, storage = drawing(db, tmp_path)
    document = db.get(SourceDocument, rev.drawing_document_id)
    document.document_type = "pqr"
    batch = db.get(ImportBatch, document.batch_id)
    batch.target_entity_type = "pqr"
    page = db.query(DocumentPage).filter(DocumentPage.document_id == document.id).one()
    page.ocr_status, page.text_content = "pending", ""
    db.commit()
    evidence = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"page": {"type": "integer"}, "text": {"type": "string"}},
            "required": ["page", "text"],
        },
    }
    schema = {
        "schema_version": "1",
        "document_type": "pqr",
        "json_schema": {
            "type": "object",
            "properties": {
                "pqr_number": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                        "confidence": {"type": "number"},
                        "evidence": evidence,
                    },
                    "required": ["value", "confidence", "evidence"],
                }
            },
        },
        "field_bindings": [
            {
                "field_key": "pqr_number",
                "field_id": "number",
                "module_id": "core",
                "extractable": True,
            }
        ],
    }
    provider = Mock(provider_name="qa", model_name="qa")
    provider.structured_response.return_value = AIProviderResult(
        {"text": "", "confidence": 0.9}, None, 1, 1, 2
    )
    service = AIExtractionService(db, storage, provider)
    with pytest.raises(AIExtractionRunError, match="OCR"):
        service.run(document.id, schema, None, "offline", True, owner, context)
    db.refresh(page)
    assert page.ocr_status == "failed"
    provider.structured_response.side_effect = [
        AIProviderResult({"text": "PQR TEST-001", "confidence": 0.9}, None, 1, 1, 2),
        AIProviderResult({"pqr_number": "TEST-001"}, None, 1, 1, 2),
        AIProviderResult(
            {
                "pqr_number": {
                    "value": "TEST-001",
                    "confidence": 0.9,
                    "evidence": [{"page": 1, "text": "PQR TEST-001"}],
                }
            },
            None,
            1,
            1,
            2,
        ),
        AIProviderResult({"unmapped_fields": []}, None, 1, 1, 2),
    ]
    job, entity, pages = service.run(
        document.id, schema, None, "offline", True, owner, context
    )
    assert job.status == "completed"
    correction = provider.structured_response.call_args_list[-2].args[0].instructions
    assert "pqr_number" in correction
    assert "object" in correction
    assert pages[0].ocr_status == "completed"
    assert (
        db.query(ExtractedField)
        .filter(ExtractedField.entity_id == entity.id)
        .one()
        .normalized_value
        == "TEST-001"
    )
    assert (
        db.query(ExtractedEntity)
        .filter(
            ExtractedEntity.document_id == document.id,
            ExtractedEntity.is_current.is_(True),
        )
        .count()
        == 1
    )
    # A later extraction reuses the completed OCR page instead of sending it again.
    provider.reset_mock()
    provider.structured_response.side_effect = [
        AIProviderResult(
            {
                "pqr_number": {
                    "value": "TEST-001",
                    "confidence": 0.9,
                    "evidence": [{"page": 1, "text": "PQR TEST-001"}],
                }
            },
            None,
            1,
            1,
            2,
        ),
        AIProviderResult({"unmapped_fields": []}, None, 1, 1, 2),
    ]
    schema["field_bindings"].append(
        {
            "field_key": "missing_parameter",
            "field_id": "missing",
            "module_id": "core",
            "extractable": True,
        }
    )
    next_job, next_entity, _ = service.run(
        document.id, schema, None, "offline", True, owner, context
    )
    assert next_job.status == "completed"
    assert next_entity.version == 2
    missing = (
        db.query(ExtractedField)
        .filter_by(entity_id=next_entity.id, field_key="missing_parameter")
        .one()
    )
    assert missing.normalized_value is None and missing.review_status == "pending"
    from app.models.smart_import import FieldEvidence

    assert db.query(FieldEvidence).filter_by(extracted_field_id=missing.id).count() == 0
    from app.services.smart_import_review_service import SmartImportReviewService
    from app.schemas.smart_import import FieldReviewRequest

    SmartImportReviewService(db).review_field(
        next_entity.id,
        missing.id,
        FieldReviewRequest(action="correct", value=12, reason="核对原件后补录"),
        owner,
        context,
    )
    db.refresh(missing)
    assert missing.normalized_value == 12 and missing.review_status == "corrected"
    assert all(
        not call.args[0].images for call in provider.structured_response.call_args_list
    )


def test_failed_stage_retry_reuses_validated_checkpoints(db, sessions, tmp_path):
    owner, context, rev, storage = drawing(db, tmp_path)
    original = queue(db, owner, rev)
    assert (
        run_job(sessions, original, DrawingProvider(fail_stage=3), storage)["status"]
        == "failed"
    )
    db.expire_all()
    assert len(db.get(ExtractionJob, original).progress_detail["checkpoints"]) == 2
    retry = queue(db, owner, rev, retry_job_id=original)
    provider = DrawingProvider()
    assert run_job(sessions, retry, provider, storage)["status"] == "completed"
    assert [r.schema_name for r in provider.requests] == [
        "engineering_drawing_welds_v2"
    ]
    db.expire_all()
    assert db.get(ExtractionJob, retry).total_tokens == 7
    assert len(db.get(ExtractionJob, retry).progress_detail["checkpoints"]) == 3
    with pytest.raises(HTTPException, match="已变化"):
        queue(db, owner, rev, retry_job_id=original)
    db.rollback()


def test_scoped_recognition_preserves_review_data_and_restores_evidence(
    db, sessions, tmp_path
):
    owner, context, rev, storage = drawing(db, tmp_path)
    service = EngineeringService(db)
    service.parse_revision(
        rev.id,
        {"parts": [{"ref": "old", "name": "Keep", "quantity": None}]},
        None,
        "manual",
        None,
        owner,
        context,
        storage,
    )
    original = db.query(Part).filter_by(revision_id=rev.id).one()
    assert original.quantity is None
    version, metadata = rev.data_version, deepcopy(rev.drawing_metadata)
    job_id = queue(
        db,
        owner,
        rev,
        page_numbers=[1],
        region=[0.2, 0.3, 0.8, 0.9],
        page_rotations={1: 180},
    )

    class RegionProvider(DrawingProvider):
        def structured_response(self, request):
            result = super().structured_response(request)
            for item in result.data.get("parts", []):
                item["evidence"] = {"page": 1, "bbox": [0, 0, 1, 1]}
            return result

    assert run_job(sessions, job_id, RegionProvider(), storage)["status"] == "completed"
    db.expire_all()
    job = db.get(ExtractionJob, job_id)
    assert job.progress_detail["proposal_only"]
    assert job.progress_detail["proposal"]["parts"][0]["evidence"][
        "bbox"
    ] == pytest.approx([0.2, 0.3, 0.8, 0.9], abs=0.002)
    assert db.get(ProductRevision, rev.id).data_version == version
    assert db.get(ProductRevision, rev.id).drawing_metadata == metadata
    assert db.query(Part).filter_by(revision_id=rev.id).one().id == original.id
    assert db.query(Part).filter_by(revision_id=rev.id).one().quantity is None


def test_cancel_running_drawing_releases_revision_and_late_result_preserves_new_job(
    db, sessions, tmp_path
):
    from app.services.ai_extraction_queue_service import AIExtractionQueueService

    owner, context, rev, storage = drawing(db, tmp_path)
    old_id = queue(db, owner, rev)
    replacement = []

    class CancellingProvider(DrawingProvider):
        def structured_response(self, request):
            if not replacement:
                db.expire_all()
                AIExtractionQueueService(db).cancel_job(db.get(ExtractionJob, old_id))
                db.refresh(rev)
                assert rev.parse_status == "failed"
                replacement.append(queue(db, owner, rev))
            return super().structured_response(request)

    assert (
        run_job(sessions, old_id, CancellingProvider(), storage)["status"]
        == "cancelled"
    )
    db.expire_all()
    assert db.get(ProductRevision, rev.id).parse_status == "processing"
    assert db.get(ExtractionJob, replacement[0]).status == "queued"
    assert (
        run_job(sessions, replacement[0], DrawingProvider(), storage)["status"]
        == "completed"
    )


def test_title_fallback_restores_both_full_page_and_crop_regions(
    db, sessions, tmp_path
):
    owner, context, rev, storage = drawing(db, tmp_path)
    job_id = queue(db, owner, rev, page_rotations={1: 180})

    class FallbackProvider(DrawingProvider):
        def structured_response(self, request):
            result = super().structured_response(request)
            if request.schema_name == "engineering_drawing_title_v2":
                result.data["product"] = {}
                result.data["unresolved_regions"] = [
                    {
                        "message": "full",
                        "evidence": {"page": 1, "bbox": [0, 0.1, 0.2, 0.2]},
                    }
                ]
            elif request.schema_name == "engineering_drawing_title_full_v2":
                result.data["unresolved_regions"] = [
                    {"message": "crop", "evidence": {"page": 1, "bbox": [0, 0, 1, 1]}}
                ]
            return result

    assert (
        run_job(sessions, job_id, FallbackProvider(), storage)["status"] == "completed"
    )
    db.expire_all()
    regions = db.get(ProductRevision, rev.id).drawing_metadata["recognition_coverage"][
        "unresolved_regions"
    ]
    assert regions[0]["evidence"]["bbox"] == pytest.approx([0.8, 0.8, 1, 0.9])
    assert regions[1]["evidence"]["bbox"] == pytest.approx(
        [0, 0, 0.44, 0.54], abs=0.002
    )

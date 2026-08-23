"""Celery tasks for persistent smart-import extraction jobs."""
import logging
from datetime import UTC, datetime
from types import SimpleNamespace

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.data_access import WorkspaceContext
from app.models.smart_import import ExtractionJob, ImportBatch, SourceDocument
from app.models.user import User
from app.schemas.smart_import import AIExtractionRequest
from app.services.ai_credential_service import AIProviderConfigService
from app.services.ai_extraction_service import (
    AIExtractionRunError,
    AIExtractionService,
    build_provider,
)
from app.services.ai_extraction_queue_service import AIExtractionQueueService
from app.services.document_storage_service import get_document_storage
from app.services.document_parser_service import DefaultDocumentParser
from app.services.smart_import_service import SmartImportService
from app.services.operations_service import OperationsService
from app.tasks.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(name="smart_import.parse")
def run_smart_import_parse(job_id: str) -> dict:
    """Parse a private source document in the worker without serializing file data."""
    db = SessionLocal()
    try:
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
        if not job:
            return {"job_id": job_id, "status": "missing"}
        if job.status == "cancelled":
            return {"job_id": job.id, "status": "cancelled"}
        if (
            job.status != "queued"
            or (job.schema_snapshot or {}).get("job_kind") != "parse"
        ):
            return {"job_id": job.id, "status": job.status}
        user = db.query(User).filter(User.id == job.user_id).first()
        if not user:
            _mark_setup_failure(db, job, "task_user_missing", "任务用户不存在")
            return {"job_id": job.id, "status": "failed"}
        context = WorkspaceContext(
            user_id=user.id,
            workspace_type=job.workspace_type,
            company_id=job.company_id,
            factory_id=job.factory_id,
        )
        job.status = "processing"
        job.attempt_count = (job.attempt_count or 0) + 1
        job.started_at = datetime.now(UTC).replace(tzinfo=None)
        job.progress = 10
        job.progress_detail = {
            "job_kind": "parse",
            "phase": "parsing",
            "pages": {"completed": 0, "total": 0},
            "fields": {"completed": 0, "total": 0},
        }
        db.commit()
        document, pages = SmartImportService(db).parse_document(
            job.document_id,
            user,
            context,
            get_document_storage(),
            DefaultDocumentParser(),
        )
        db.refresh(job)
        if job.status == "cancelled":
            return {"job_id": job.id, "status": "cancelled"}
        job.status = "completed"
        job.progress = 100
        job.progress_detail = {
            "job_kind": "parse",
            "phase": "completed",
            "pages": {"completed": len(pages), "total": len(pages)},
            "fields": {"completed": 0, "total": 0},
        }
        job.completed_at = datetime.now(UTC).replace(tzinfo=None)
        batch = (
            db.query(ImportBatch).filter(ImportBatch.id == document.batch_id).first()
        )
        if batch:
            remaining = (
                db.query(SourceDocument)
                .filter(
                    SourceDocument.batch_id == batch.id,
                    SourceDocument.status.notin_(("ready", "failed", "archived")),
                )
                .count()
            )
            batch.status = "draft" if remaining == 0 else "processing"
        db.commit()
        return {
            "job_id": job.id,
            "document_id": document.id,
            "status": job.status,
            "page_count": len(pages),
        }
    except Exception:
        logger.exception("Smart-import parse task %s failed", job_id)
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
        if job and job.status not in {"failed", "cancelled", "completed"}:
            _mark_setup_failure(db, job, "parse_failed", "后台文档解析失败")
        return {"job_id": job_id, "status": "failed", "error_code": "parse_failed"}
    finally:
        try:
            measured = (
                db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
            )
            if measured:
                OperationsService(db).record_extraction_job(measured)
                db.commit()
        except Exception:
            logger.exception("Could not persist parse task metrics for %s", job_id)
            db.rollback()
        db.close()


@celery_app.task(name="smart_import.extract")
def run_smart_import_extraction(job_id: str) -> dict:
    """Execute a pre-authorized job without putting API keys in Celery payloads."""
    db = SessionLocal()
    provider = None
    try:
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
        if not job:
            return {"job_id": job_id, "status": "missing"}
        if job.status == "cancelled":
            return {"job_id": job.id, "status": "cancelled"}
        if job.status != "queued":
            return {"job_id": job.id, "status": job.status}
        user = db.query(User).filter(User.id == job.user_id).first()
        if not user:
            _mark_setup_failure(db, job, "task_user_missing", "任务用户不存在")
            return {"job_id": job.id, "status": "failed"}
        context = WorkspaceContext(
            user_id=user.id,
            workspace_type=job.workspace_type,
            company_id=job.company_id,
            factory_id=job.factory_id,
        )
        credentials = AIProviderConfigService(db)
        saved_config = None
        saved_key = None
        if job.provider_config_id:
            saved_config, saved_key = credentials.resolve_for_use(
                job.provider_config_id, user, context
            )
            request = AIExtractionRequest(
                mode="byok",
                provider_config_id=saved_config.id,
                outbound_consent_id=(job.schema_snapshot or {}).get(
                    "outbound_consent_id"
                ),
            )
        else:
            credentials.enforce_policy(job.mode, None, context)
            request = AIExtractionRequest(
                mode="offline" if job.mode == "offline" else "platform",
                outbound_consent_id=(job.schema_snapshot or {}).get(
                    "outbound_consent_id"
                ),
            )
            if job.mode == "offline":
                profile = OperationsService(db).get_deployment_profile(context)
                base_url = (
                    getattr(profile, "local_ai_base_url", None)
                    or settings.AI_OFFLINE_BASE_URL
                )
                model = (
                    getattr(profile, "local_ai_model", None)
                    or settings.AI_OFFLINE_MODEL
                )
                if not base_url or not model:
                    _mark_setup_failure(
                        db,
                        job,
                        "offline_model_not_configured",
                        "本地离线模型尚未配置",
                    )
                    return {"job_id": job.id, "status": "failed"}
                saved_config = SimpleNamespace(
                    provider=settings.AI_OFFLINE_PROVIDER,
                    base_url=base_url,
                    model=model,
                )
                saved_key = settings.AI_OFFLINE_API_KEY
        document = (
            db.query(SourceDocument)
            .filter(SourceDocument.id == job.document_id)
            .first()
        )
        if (
            document
            and document.document_type in {"drawing", "pqr"}
            and request.mode != "offline"
        ):
            OperationsService(db).require_consent(
                document.id,
                saved_config.base_url
                if saved_config
                else settings.AI_PLATFORM_BASE_URL,
                user,
                context,
                request.outbound_consent_id,
            )
        provider = build_provider(request, saved_config, saved_key)
        completed, entity, _ = AIExtractionService(
            db, get_document_storage(), provider
        ).run(
            document_id=job.document_id,
            schema_snapshot=job.schema_snapshot,
            template_id=job.template_id,
            mode=job.mode,
            run_ocr=job.run_ocr,
            user=user,
            context=context,
            provider_config_id=job.provider_config_id,
            existing_job=job,
        )
        return {
            "job_id": completed.id,
            "entity_id": entity.id,
            "status": completed.status,
        }
    except AIExtractionRunError as exc:
        logger.warning("Smart-import task %s stopped with code %s", job_id, exc.code)
        return {
            "job_id": job_id,
            "status": "cancelled" if exc.code == "task_cancelled" else "failed",
            "error_code": exc.code,
        }
    except Exception:
        logger.exception("Smart-import task %s failed before extraction", job_id)
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
        if job and job.status not in {"failed", "cancelled", "completed"}:
            _mark_setup_failure(db, job, "task_setup_failed", "后台任务初始化失败")
        return {"job_id": job_id, "status": "failed", "error_code": "task_setup_failed"}
    finally:
        if provider is not None:
            provider.close()
        try:
            _refresh_job_batch(db, job_id)
        except Exception:
            logger.exception("Could not refresh batch state for task %s", job_id)
        try:
            measured = (
                db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
            )
            if measured:
                OperationsService(db).record_extraction_job(measured)
                db.commit()
        except Exception:
            logger.exception("Could not persist extraction task metrics for %s", job_id)
            db.rollback()
        db.close()


def _mark_setup_failure(db, job: ExtractionJob, code: str, message: str) -> None:
    job.status = "failed"
    job.error_code = code
    job.error_message = message
    job.progress_detail = {**(job.progress_detail or {}), "phase": "failed"}
    job.completed_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()


def _refresh_job_batch(db, job_id: str) -> None:
    job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
    if not job:
        return
    document = (
        db.query(SourceDocument).filter(SourceDocument.id == job.document_id).first()
    )
    if not document:
        return
    batch = db.query(ImportBatch).filter(ImportBatch.id == document.batch_id).first()
    if batch:
        AIExtractionQueueService(db).refresh_batch(batch)

"""Scheduled lifecycle jobs for private document artifacts."""
import logging

from app.core.database import SessionLocal
from app.services.document_artifact_service import DocumentArtifactRetentionService
from app.services.document_storage_service import get_document_storage
from app.tasks.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(
    name="documents.purge_expired_artifacts",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def purge_expired_document_artifacts() -> dict[str, int | bool]:
    db = SessionLocal()
    try:
        count = DocumentArtifactRetentionService(
            db, get_document_storage()
        ).purge_expired()
        logger.info("Expired document artifact cleanup completed: count=%s", count)
        return {"success": True, "purged_count": count}
    except Exception:
        db.rollback()
        logger.exception("Expired document artifact cleanup failed")
        raise
    finally:
        db.close()

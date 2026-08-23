"""P8 periodic quota, anomaly, queue and failure-rate alert detection."""
import logging

from app.core.database import SessionLocal
from app.core.data_access import WorkspaceContext
from app.models.company import Company
from app.models.user import User
from app.services.operations_service import OperationsService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="operations.detect_alerts")
def detect_operations_alerts() -> dict:
    db = SessionLocal()
    detected = 0
    failed = 0
    try:
        for company in db.query(Company).filter(Company.is_active.is_(True)).all():
            owner = db.query(User).filter(User.id == company.owner_id).first()
            if not owner:
                continue
            context = WorkspaceContext(
                user_id=owner.id,
                workspace_type="enterprise",
                company_id=company.id,
            )
            try:
                detected += len(
                    OperationsService(db).detect_usage_anomalies(owner, context)
                )
            except Exception:
                db.rollback()
                failed += 1
                logger.exception("P8 alert detection failed for company %s", company.id)
        return {"detected": detected, "failed_companies": failed}
    finally:
        db.close()

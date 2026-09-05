from app.core.database import SessionLocal
from app.services.payment_notification_service import deliver_pending_payment_notifications
from app.tasks.celery_app import celery_app


@celery_app.task(name="payments.deliver_notifications", autoretry_for=(Exception,),
                 retry_backoff=True, retry_kwargs={"max_retries": 3})
def deliver_payment_notifications():
    with SessionLocal() as db:
        return deliver_pending_payment_notifications(db)

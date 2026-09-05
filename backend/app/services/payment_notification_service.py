"""Retry notification delivery independently from payment settlement."""
from datetime import datetime, timedelta

from app.models.payment_delivery import PaymentNotification
from app.models.user import User
from app.services.notification_service import NotificationService


def deliver_pending_payment_notifications(db, limit=50):
    delivered = 0
    for _ in range(limit):
        item = db.query(PaymentNotification).filter(
            PaymentNotification.delivered_at.is_(None),
            PaymentNotification.next_attempt_at <= datetime.utcnow(),
        ).order_by(PaymentNotification.id).with_for_update(skip_locked=True).first()
        if item is None:
            db.rollback()
            break
        try:
            # Keep the row lock while rolling back a failed notification attempt.
            with db.begin_nested():
                user = db.query(User).filter(User.id == item.user_id).first()
                if user is None:
                    raise RuntimeError("notification_user_missing")
                NotificationService(db).deliver_user_notification(
                    user, title=item.title, content=item.content, category="membership",
                    announcement_type=item.announcement_type, commit=False, strict_delivery=True,
                )
                db.flush()
            item.delivered_at = datetime.utcnow()
            item.last_error = None
            delivered += 1
        except Exception as exc:
            item.last_error = type(exc).__name__[:80]
            item.next_attempt_at = datetime.utcnow() + timedelta(minutes=min(1440, 2 ** min(item.attempts + 1, 11)))
        item.attempts += 1
        db.commit()
    return delivered

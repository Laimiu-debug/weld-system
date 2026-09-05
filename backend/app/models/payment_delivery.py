"""Settlement receipt and durable notification outbox."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from app.core.database import Base


class PaymentActivation(Base):
    __tablename__ = "payment_activations"
    transaction_id = Column(Integer, ForeignKey("subscription_transactions.id"), primary_key=True)
    applied_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PaymentNotification(Base):
    __tablename__ = "payment_notifications"
    id = Column(Integer, primary_key=True)
    event_key = Column(String(150), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    announcement_type = Column(String(20), nullable=False, default="info")
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    delivered_at = Column(DateTime)
    last_error = Column(String(80))

"""
User feedback model for product improvement suggestions.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserFeedback(Base):
    """用户意见反馈"""

    __tablename__ = "user_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    contact = Column(String(200), nullable=True)

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    admin_note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_user_feedbacks_read_created", "is_read", "created_at"),
    )

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<UserFeedback(id={self.id}, user_id={self.user_id}, title={self.title!r})>"

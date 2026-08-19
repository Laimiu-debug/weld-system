"""
User notification read status model for the welding system backend.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserNotificationReadStatus(Base):
    """用户通知已读状态模型"""

    __tablename__ = "user_notification_read_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    announcement_id = Column(Integer, ForeignKey("system_announcements.id"), nullable=False, index=True)
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)  # 软删除
    read_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_unrs_user_unread", "user_id", "is_read", "is_deleted"),
        Index("ix_unrs_user_announcement", "user_id", "announcement_id"),
    )

    # 关系
    user = relationship("User", backref="notification_read_status")
    announcement = relationship("SystemAnnouncement", backref="read_status")

    def __repr__(self):
        return f"<UserNotificationReadStatus(user_id={self.user_id}, announcement_id={self.announcement_id}, is_read={self.is_read})>"


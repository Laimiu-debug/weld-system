"""
System announcement model for the welding system backend.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class SystemAnnouncement(Base):
    """系统公告模型"""

    __tablename__ = "system_announcements"

    id = Column(Integer, primary_key=True, index=True)

    # 公告信息
    title = Column(String(255), nullable=False)                   # 标题
    content = Column(Text, nullable=False)                       # 内容
    announcement_type = Column(String(50), nullable=True)       # 类型: info, warning, maintenance
    priority = Column(String(20), default="normal")             # 优先级: low, normal, high, urgent

    # 显示设置
    is_published = Column(Boolean, default=False)               # 是否发布
    is_pinned = Column(Boolean, default=False)                  # 是否置顶
    is_auto_generated = Column(Boolean, default=False)          # 是否为系统自动生成
    target_audience = Column(String(50), default="all")         # 目标受众: all, free, pro, enterprise

    # 时间设置
    publish_at = Column(DateTime, nullable=True)                 # 发布时间
    expire_at = Column(DateTime, nullable=True)                  # 过期时间

    # 统计
    view_count = Column(Integer, default=0)                     # 查看次数

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<SystemAnnouncement(id={self.id}, title={self.title}, type={self.announcement_type})>"
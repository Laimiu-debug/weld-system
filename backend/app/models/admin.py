"""
Admin model for the welding system backend.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Admin(Base):
    """Admin model for admin portal authentication."""

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)

    # Admin credentials (standalone authentication)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # 关联的用户ID（可选，如果管理员也是用户）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 管理员信息
    is_super_admin = Column(Boolean, default=False)            # 是否超级管理员
    admin_level = Column(String(20), default="admin")          # 级别: super_admin, admin
    permissions = Column(JSONB, nullable=True)                  # 权限列表（JSON格式）

    # 状态
    is_active = Column(Boolean, default=True)

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 登录相关
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="admin_profile", foreign_keys=[user_id])

    def __repr__(self):
        return f"<Admin(id={self.id}, username={self.username}, admin_level={self.admin_level})>"
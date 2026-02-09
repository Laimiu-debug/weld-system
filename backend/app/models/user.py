"""
User model for the welding system backend.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True)
    contact = Column(String)  # 可以是邮箱或手机号
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    phone = Column(String)
    company = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)                   # 是否管理员

    # 会员系统字段
    member_tier = Column(String, default="free")               # 会员等级
    membership_type = Column(String, default="personal")       # 会员类型: personal, enterprise
    subscription_status = Column(String, default="inactive")    # 订阅状态: active, expired, cancelled, inactive
    subscription_start_date = Column(DateTime, nullable=True)   # 订阅开始时间
    subscription_end_date = Column(DateTime, nullable=True)     # 订阅结束时间
    subscription_expires_at = Column(DateTime, nullable=True)   # 订阅过期时间
    auto_renewal = Column(Boolean, default=False)               # 自动续费

    # 使用配额字段
    wps_quota_used = Column(Integer, default=0)                 # 已使用的WPS配额
    pqr_quota_used = Column(Integer, default=0)                 # 已使用的PQR配额
    ppqr_quota_used = Column(Integer, default=0)                # 已使用的pPQR配额
    storage_quota_used = Column(Integer, default=0)             # 已使用的存储配额(MB)

    # 功能权限字段
    permissions = Column(String, nullable=True)                # 功能权限（JSON字符串）

    # 登录相关
    last_login_at = Column(DateTime, nullable=True)             # 最后登录时间
    last_login_ip = Column(String, nullable=True)               # 最后登录IP

    # 个人资料字段
    avatar_url = Column(String, nullable=True)                  # 头像URL

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    admin_profile = relationship("Admin", back_populates="user", uselist=False, cascade="all, delete-orphan",
                              foreign_keys="Admin.user_id")
    # roles: Mapped[list["Role"]] = relationship(
    #     "Role",
    #     secondary="user_role_association",
    #     back_populates="users"
    # )
    # wps_files = relationship("WPS", back_populates="owner", foreign_keys="WPS.owner_id")
    # pqr_files = relationship("PQR", back_populates="owner", foreign_keys="PQR.owner_id")
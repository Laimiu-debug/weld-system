"""
Verification Code model for the welding system backend.
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base


class VerificationCode(Base):
    """Verification Code model for email/SMS verification."""

    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    account = Column(String, index=True, nullable=False)  # 邮箱或手机号
    account_type = Column(String, nullable=False)  # 'email' or 'phone'
    code = Column(String, nullable=False)  # 6位验证码
    purpose = Column(String, nullable=False)  # 'login', 'register', 'reset_password'
    is_used = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)  # 尝试次数
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<VerificationCode(account={self.account}, purpose={self.purpose})>"

    @property
    def is_expired(self):
        """Check if verification code is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Check if verification code is valid (not expired, not used, attempts < 3)."""
        return not self.is_used and not self.is_expired and self.attempts < 3
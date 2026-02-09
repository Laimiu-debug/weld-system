"""
Verification code service for the welding system backend.
"""
import random
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.verification_code import VerificationCode
from app.schemas.verification_code import VerificationCodeCreate, VerificationCodeRequest


class VerificationService:
    """Verification code service."""

    @staticmethod
    def generate_code(length: int = 6) -> str:
        """Generate random numeric verification code."""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])

    @staticmethod
    def detect_account_type(account: str) -> Optional[str]:
        """Detect account type from account string."""
        if '@' in account and '.' in account.split('@')[1]:
            return 'email'
        elif account.isdigit() and len(account) == 11 and account.startswith('1'):
            return 'phone'
        return None

    @staticmethod
    def create_verification_code(
        db: Session,
        account: str,
        account_type: str,
        purpose: str = "login",
        expires_minutes: int = 10
    ) -> VerificationCode:
        """Create a new verification code."""
        # 生成6位验证码
        code = VerificationService.generate_code(6)
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

        # 使之前的相同类型验证码失效
        db.query(VerificationCode).filter(
            VerificationCode.account == account,
            VerificationCode.account_type == account_type,
            VerificationCode.purpose == purpose,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.utcnow()
        ).update({"is_used": True})

        # 创建新验证码
        verification_code = VerificationCode(
            account=account,
            account_type=account_type,
            code=code,
            purpose=purpose,
            expires_at=expires_at
        )

        db.add(verification_code)
        db.commit()
        db.refresh(verification_code)

        return verification_code

    @staticmethod
    def verify_code(
        db: Session,
        account: str,
        code: str,
        account_type: str,
        purpose: str = "login"
    ) -> Optional[VerificationCode]:
        """Verify verification code."""
        verification_code = db.query(VerificationCode).filter(
            VerificationCode.account == account,
            VerificationCode.code == code,
            VerificationCode.account_type == account_type,
            VerificationCode.purpose == purpose,
            VerificationCode.is_used == False
        ).first()

        if not verification_code:
            return None

        # 检查是否过期
        if verification_code.is_expired:
            return None

        # 检查尝试次数
        if verification_code.attempts >= 3:
            return None

        # 增加尝试次数
        verification_code.attempts += 1
        db.commit()

        # 如果验证码正确，标记为已使用
        if verification_code.code == code:
            verification_code.is_used = True
            verification_code.used_at = datetime.utcnow()
            db.commit()
            db.refresh(verification_code)

        return verification_code

    @staticmethod
    def get_valid_code(
        db: Session,
        account: str,
        account_type: str,
        purpose: str = "login"
    ) -> Optional[VerificationCode]:
        """Get valid verification code for account."""
        return db.query(VerificationCode).filter(
            VerificationCode.account == account,
            VerificationCode.account_type == account_type,
            VerificationCode.purpose == purpose,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.utcnow()
        ).first()

    @staticmethod
    def cleanup_expired_codes(db: Session) -> int:
        """Clean up expired verification codes."""
        expired_count = db.query(VerificationCode).filter(
            VerificationCode.expires_at < datetime.utcnow() - timedelta(days=1)
        ).delete()
        db.commit()
        return expired_count

    @staticmethod
    def can_send_code(
        db: Session,
        account: str,
        account_type: str,
        purpose: str = "login"
    ) -> bool:
        """Check if can send new verification code (rate limiting)."""
        # 检查是否有未过期的验证码
        existing_code = VerificationService.get_valid_code(db, account, account_type, purpose)
        if existing_code:
            # 如果还有未过期的验证码，检查是否已经过了60秒
            time_diff = datetime.utcnow() - existing_code.created_at
            if time_diff.total_seconds() < 60:
                return False
        return True


# Create global verification service instance
verification_service = VerificationService()
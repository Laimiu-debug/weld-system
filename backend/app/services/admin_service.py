"""
Admin service for admin authentication and management.
"""
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.admin import Admin
from app.models.user import User
from app.core.security import get_password_hash, verify_password


class AdminService:
    """Admin service class."""

    def get(self, db: Session, id: int) -> Optional[Admin]:
        """Get admin by ID."""
        return db.query(Admin).filter(Admin.id == id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[Admin]:
        """Get admin by email."""
        return db.query(Admin).filter(Admin.email == email).first()

    def get_by_username(self, db: Session, username: str) -> Optional[Admin]:
        """Get admin by username."""
        return db.query(Admin).filter(Admin.username == username).first()

    def authenticate(self, db: Session, username: str, password: str) -> Optional[Admin]:
        """Authenticate admin by username/email and password."""

        # 先尝试用用户名或邮箱查找管理员
        admin = db.query(Admin).filter(
            (Admin.username == username) | (Admin.email == username)
        ).first()

        if not admin:
            return None

        # 验证密码
        if not verify_password(password, admin.hashed_password):
            return None

        return admin

    def create(self, db: Session, obj_in: dict) -> Admin:
        """Create new admin from existing user."""
        from app.models.user import User

        # Get the user
        user = db.query(User).filter(User.email == obj_in["email"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # Check if admin already exists for this user
        existing_admin = db.query(Admin).filter(Admin.user_id == user.id).first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户已经是管理员"
            )

        # Hash password if provided (should use user's password)
        if "password" in obj_in:
            user.hashed_password = get_password_hash(obj_in.pop("password"))
            db.commit()

        # Create admin record
        admin_data = {
            "user_id": user.id,
            "admin_level": obj_in.get("admin_level", "admin"),
            "is_active": obj_in.get("is_active", True),
            "created_by": obj_in.get("created_by")
        }

        admin = Admin(**admin_data)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    def update(self, db: Session, db_obj: Admin, obj_in: dict) -> Admin:
        """Update admin."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_last_login(self, db: Session, admin: Admin) -> Admin:
        """Update last login time."""
        admin.last_login_at = datetime.utcnow()
        admin.updated_at = datetime.utcnow()

        # Standalone admin - no user relationship to update

        db.commit()
        db.refresh(admin)
        return admin

    def is_active(self, admin: Admin) -> bool:
        """Check if admin is active."""
        return admin.is_active

    def is_super_admin(self, admin: Admin) -> bool:
        """Check if admin is super admin."""
        return admin.admin_level == "super_admin"


# Create service instance
admin_service = AdminService()
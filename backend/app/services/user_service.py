"""
User service for the welding system backend.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """User service class."""

    def get(self, db: Session, *, id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == id).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    def get_by_contact(self, db: Session, *, contact: str) -> Optional[User]:
        """Get user by contact (email or phone)."""
        return db.query(User).filter(User.contact == contact).first()

    def get_by_phone(self, db: Session, *, phone: str) -> Optional[User]:
        """Get user by phone."""
        return db.query(User).filter(User.phone == phone).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Get multiple users."""
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create user."""
        # 自动判断contact是邮箱还是手机号
        contact = obj_in.contact
        phone = None
        email = obj_in.email

        if contact:
            # 简单判断：如果是数字，认为是手机号；否则认为是邮箱
            if contact.isdigit() or (len(contact) == 11 and contact.startswith('1')):
                phone = contact
                # 如果是手机号，email字段应该使用传入的email（通常是虚拟邮箱）
                email = obj_in.email
            else:
                # 如果是邮箱格式，更新email字段
                if '@' in contact and '.' in contact:
                    email = contact

        db_obj = User(
            email=email,
            username=obj_in.username,
            contact=contact,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.username,  # 使用username作为full_name
            phone=phone or obj_in.phone,
            company=obj_in.company,
            is_active=True,
            is_verified=True,  # 临时设置为True，跳过邮箱验证
            # TODO: 实现邮箱验证功能后改回False
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: UserUpdate
    ) -> User:
        """Update user."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> User:
        """Remove user."""
        obj = db.query(User).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[User]:
        """Authenticate user."""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """Check if user is superuser."""
        return user.is_superuser

    def get_user_permissions(self, db: Session, user_id: int) -> List[str]:
        """Get user permissions."""
        from app.services.role_service import role_service
        return list(role_service.get_user_permissions(db, user_id=user_id))

    def has_permission(self, db: Session, user_id: int, resource: str, action: str) -> bool:
        """Check if user has specific permission."""
        from app.services.role_service import role_service
        return role_service.check_user_permission(db, user_id=user_id, resource=resource, action=action)

    def assign_default_role(self, db: Session, user_id: int) -> User:
        """Assign default role to new user."""
        from app.services.role_service import role_service
        default_role = role_service.get_default_role(db)
        if default_role:
            return role_service.assign_role_to_user(db, user_id=user_id, role_id=default_role.id)
        return self.get(db, id=user_id)


# Create global user service instance
user_service = UserService()
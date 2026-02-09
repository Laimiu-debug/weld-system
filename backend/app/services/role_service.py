"""
Role and permission service for the welding system backend.
"""
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.models.role import Role, Permission, role_permission_association, user_role_association
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate, PermissionCreate, PermissionUpdate


class PermissionService:
    """Permission service class."""

    def get(self, db: Session, *, id: int) -> Optional[Permission]:
        """Get permission by ID."""
        return db.query(Permission).filter(Permission.id == id).first()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Permission]:
        """Get permission by name."""
        return db.query(Permission).filter(Permission.name == name).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Permission]:
        """Get multiple permissions."""
        return db.query(Permission).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: PermissionCreate) -> Permission:
        """Create permission."""
        db_obj = Permission(
            name=obj_in.name,
            description=obj_in.description,
            resource=obj_in.resource,
            action=obj_in.action,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Permission,
        obj_in: PermissionUpdate
    ) -> Permission:
        """Update permission."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Permission:
        """Remove permission."""
        obj = db.query(Permission).get(id)
        db.delete(obj)
        db.commit()
        return obj


class RoleService:
    """Role service class."""

    def get(self, db: Session, *, id: int) -> Optional[Role]:
        """Get role by ID."""
        return db.query(Role).filter(Role.id == id).first()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        """Get role by name."""
        return db.query(Role).filter(Role.name == name).first()

    def get_default_role(self, db: Session) -> Optional[Role]:
        """Get default role."""
        return db.query(Role).filter(Role.is_default == True).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Role]:
        """Get multiple roles."""
        return db.query(Role).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: RoleCreate) -> Role:
        """Create role."""
        db_obj = Role(
            name=obj_in.name,
            description=obj_in.description,
            is_active=obj_in.is_active,
        )

        # Add permissions if provided
        if obj_in.permission_ids:
            permissions = db.query(Permission).filter(
                Permission.id.in_(obj_in.permission_ids)
            ).all()
            db_obj.permissions = permissions

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Role,
        obj_in: RoleUpdate
    ) -> Role:
        """Update role."""
        update_data = obj_in.model_dump(exclude_unset=True)
        permission_ids = update_data.pop("permission_ids", None)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        # Update permissions if provided
        if permission_ids is not None:
            permissions = db.query(Permission).filter(
                Permission.id.in_(permission_ids)
            ).all()
            db_obj.permissions = permissions

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Role:
        """Remove role."""
        obj = db.query(Role).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def assign_role_to_user(self, db: Session, *, user_id: int, role_id: int) -> User:
        """Assign role to user."""
        user = db.query(User).filter(User.id == user_id).first()
        role = db.query(Role).filter(Role.id == role_id).first()

        if not user or not role:
            raise ValueError("User or Role not found")

        if role not in user.roles:
            user.roles.append(role)
            db.commit()
            db.refresh(user)

        return user

    def remove_role_from_user(self, db: Session, *, user_id: int, role_id: int) -> User:
        """Remove role from user."""
        user = db.query(User).filter(User.id == user_id).first()
        role = db.query(Role).filter(Role.id == role_id).first()

        if not user or not role:
            raise ValueError("User or Role not found")

        if role in user.roles:
            user.roles.remove(role)
            db.commit()
            db.refresh(user)

        return user

    def assign_multiple_roles_to_user(
        self, db: Session, *, user_id: int, role_ids: List[int]
    ) -> User:
        """Assign multiple roles to user."""
        user = db.query(User).filter(User.id == user_id).first()
        roles = db.query(Role).filter(Role.id.in_(role_ids)).all()

        if not user:
            raise ValueError("User not found")

        # Clear existing roles and add new ones
        user.roles = roles
        db.commit()
        db.refresh(user)

        return user

    def get_user_permissions(self, db: Session, *, user_id: int) -> Set[str]:
        """Get all permissions for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return set()

        permissions = set()
        for role in user.roles:
            if role.is_active:
                for permission in role.permissions:
                    # Format: "resource:action" e.g., "wps:create"
                    permissions.add(f"{permission.resource}:{permission.action}")

        return permissions

    def check_user_permission(
        self, db: Session, *, user_id: int, resource: str, action: str
    ) -> bool:
        """Check if user has permission for specific resource and action."""
        user_permissions = self.get_user_permissions(db, user_id=user_id)
        return f"{resource}:{action}" in user_permissions

    def initialize_default_roles(self, db: Session) -> None:
        """Initialize default roles and permissions."""
        # Create default permissions
        default_permissions = [
            # User management
            ("user:create", "Create users", "user", "create"),
            ("user:read", "Read users", "user", "read"),
            ("user:update", "Update users", "user", "update"),
            ("user:delete", "Delete users", "user", "delete"),

            # WPS management
            ("wps:create", "Create WPS", "wps", "create"),
            ("wps:read", "Read WPS", "wps", "read"),
            ("wps:update", "Update WPS", "wps", "update"),
            ("wps:delete", "Delete WPS", "wps", "delete"),
            ("wps:export", "Export WPS", "wps", "export"),

            # PQR management
            ("pqr:create", "Create PQR", "pqr", "create"),
            ("pqr:read", "Read PQR", "pqr", "read"),
            ("pqr:update", "Update PQR", "pqr", "update"),
            ("pqr:delete", "Delete PQR", "pqr", "delete"),
            ("pqr:export", "Export PQR", "pqr", "export"),

            # Role management
            ("role:create", "Create roles", "role", "create"),
            ("role:read", "Read roles", "role", "read"),
            ("role:update", "Update roles", "role", "update"),
            ("role:delete", "Delete roles", "role", "delete"),
            ("role:assign", "Assign roles", "role", "assign"),
        ]

        for name, desc, resource, action in default_permissions:
            existing = self.permission_service.get_by_name(db, name=name)
            if not existing:
                self.permission_service.create(db, obj_in=PermissionCreate(
                    name=name,
                    description=desc,
                    resource=resource,
                    action=action
                ))

        # Create default roles
        default_roles = [
            ("admin", "System Administrator", True, [
                "user:create", "user:read", "user:update", "user:delete",
                "wps:create", "wps:read", "wps:update", "wps:delete", "wps:export",
                "pqr:create", "pqr:read", "pqr:update", "pqr:delete", "pqr:export",
                "role:create", "role:read", "role:update", "role:delete", "role:assign"
            ]),
            ("engineer", "Welding Engineer", False, [
                "wps:create", "wps:read", "wps:update", "wps:delete", "wps:export",
                "pqr:create", "pqr:read", "pqr:update", "pqr:delete", "pqr:export"
            ]),
            ("viewer", "Read-only User", False, [
                "wps:read", "pqr:read"
            ]),
        ]

        for name, desc, is_default, permission_names in default_roles:
            existing = self.get_by_name(db, name=name)
            if not existing:
                permission_ids = []
                for perm_name in permission_names:
                    perm = self.permission_service.get_by_name(db, name=perm_name)
                    if perm:
                        permission_ids.append(perm.id)

                self.create(db, obj_in=RoleCreate(
                    name=name,
                    description=desc,
                    is_default=is_default,
                    permission_ids=permission_ids
                ))


# Create global service instances
permission_service = PermissionService()
role_service = RoleService()

# Add reference to permission_service in role_service
role_service.permission_service = permission_service
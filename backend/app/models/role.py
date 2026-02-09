"""
Role models for the welding system backend.
"""
from typing import List
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey

from app.core.database import Base


# Role-Permission association table
role_permission_association = Table(
    "role_permission_association",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)

# User-Role association table
user_role_association = Table(
    "user_role_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class Permission(Base):
    """Permission model."""

    __tablename__ = "permissions"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = Column(String(255))
    resource: Mapped[str] = Column(String(50), nullable=False)  # e.g., "wps", "pqr", "user"
    action: Mapped[str] = Column(String(50), nullable=False)  # e.g., "create", "read", "update", "delete"
    created_at: Mapped[DateTime] = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[DateTime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permission_association,
        back_populates="permissions"
    )


class Role(Base):
    """Role model."""

    __tablename__ = "roles"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = Column(String(255))
    is_active: Mapped[bool] = Column(Boolean, default=True)
    is_default: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[DateTime] = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[DateTime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_role_association,
        back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permission_association,
        back_populates="roles"
    )


# Import User here to avoid circular imports
from app.models.user import User

# Add the roles relationship to User
User.roles = relationship(
    "Role",
    secondary=user_role_association,
    back_populates="users"
)
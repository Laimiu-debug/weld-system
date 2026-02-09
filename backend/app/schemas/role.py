"""
Role schemas for the welding system backend.
"""
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PermissionBase(BaseModel):
    """Base permission schema."""
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    """Permission creation schema."""
    pass


class PermissionUpdate(BaseModel):
    """Permission update schema."""
    description: Optional[str] = None


class PermissionResponse(PermissionBase):
    """Permission response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleBase(BaseModel):
    """Base role schema."""
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Role creation schema."""
    is_active: Optional[bool] = True
    permission_ids: Optional[List[int]] = None


class RoleUpdate(BaseModel):
    """Role update schema."""
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class RoleResponse(RoleBase):
    """Role response schema."""
    id: int
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserRoleAssignment(BaseModel):
    """User role assignment schema."""
    user_id: int
    role_ids: List[int]


class UserRoleResponse(BaseModel):
    """User role response schema."""
    id: int
    email: str
    full_name: Optional[str] = None
    roles: List[RoleResponse] = []

    model_config = ConfigDict(from_attributes=True)
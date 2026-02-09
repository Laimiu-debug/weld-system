"""
Admin schemas for API serialization.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class AdminBase(BaseModel):
    """Admin base schema."""
    email: EmailStr
    username: str
    full_name: str
    is_active: bool = True
    is_super_admin: bool = False
    admin_level: str = "admin"


class AdminCreate(AdminBase):
    """Admin create schema."""
    password: str


class AdminUpdate(BaseModel):
    """Admin update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_super_admin: Optional[bool] = None
    admin_level: Optional[str] = None
    password: Optional[str] = None


class AdminInDBBase(AdminBase):
    """Admin in DB base schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Admin(AdminInDBBase):
    """Admin response schema."""
    pass


class AdminLogin(BaseModel):
    """Admin login request schema."""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """Admin login response schema."""
    access_token: str
    token_type: str
    admin: Admin
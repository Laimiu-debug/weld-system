"""
User schemas for the welding system backend.
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: Optional[str] = None
    contact: Optional[str] = None  # 可以是邮箱或手机号
    phone: Optional[str] = None
    company: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str
    invite_token: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    is_verified: bool
    is_superuser: Optional[bool] = False
    member_tier: Optional[str] = None
    permissions: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    auto_renewal: Optional[bool] = None
    last_login_at: Optional[datetime] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', 'updated_at', 'subscription_start_date', 'subscription_end_date', 'last_login_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat() if value else None


class UserInDB(UserResponse):
    """User in database schema."""
    hashed_password: str


class LoginRequest(BaseModel):
    """Login request schema."""
    account: str  # Can be email or phone
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""
    message: str
    user_info: Optional[dict] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: Optional[str] = None


class EmailTokenRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UserPreferences(BaseModel):
    """Personal system preferences for the user portal."""
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    dateFormat: str = "YYYY-MM-DD"
    timeFormat: str = "HH:mm:ss"
    theme: str = "light"
    primaryColor: str = "#1F5EFF"
    compactMode: bool = False
    sidebarCollapsed: bool = False
    workDays: List[str] = Field(
        default_factory=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    )
    workStartTime: str = "09:00"
    workEndTime: str = "18:00"
    autoSave: bool = True
    autoSaveInterval: int = 30
    notificationSound: bool = True
    desktopNotifications: bool = True
    pageSize: int = 20
    decimalPlaces: int = 2
    currency: str = "CNY"
    measurementUnit: str = "metric"
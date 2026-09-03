"""
User schemas for the welding system backend.
"""
from typing import Any, Dict, Optional, List
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer, Field, field_validator


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


class ResetPasswordWithCodeRequest(BaseModel):
    """用邮箱 6 位验证码重置密码."""
    email: EmailStr
    verification_code: str
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
    # 安全偏好
    loginNotifications: bool = True
    sessionTimeout: bool = True
    autoLogout: bool = False
    autoLogoutMinutes: int = 30
    # 通知偏好
    emailNotifications: bool = True
    pushNotifications: bool = True
    smsNotifications: bool = False
    quietHoursEnabled: bool = False
    quietHoursStart: str = "22:00"
    quietHoursEnd: str = "08:00"
    systemUpdates: bool = True
    securityAlerts: bool = True
    maintenance: bool = True
    wpsUpdates: bool = True
    pqrApprovals: bool = True
    qualityAlerts: bool = True
    equipmentMaintenance: bool = True
    materialAlerts: bool = True
    welderCertifications: bool = True
    productionDeadlines: bool = True
    emailDigestFrequency: str = "immediate"
    # AI 数据外发授权：由用户在“我的设置”中明确保存，声明版本变化时失效。
    aiDataOutboundAuthorized: bool = False
    aiDataOutboundNoticeVersion: str = ""
    # 焊工证书记审规则按体系保存到用户记录，未配置时禁止快捷记审。
    welderRenewalRules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class SecuritySettingsUpdate(BaseModel):
    """Security preference updates from the security settings page."""
    loginNotifications: Optional[bool] = None
    sessionTimeout: Optional[bool] = None
    autoLogout: Optional[bool] = None
    autoLogoutMinutes: Optional[int] = Field(default=None, ge=5, le=240)


class LoginHistoryItem(BaseModel):
    id: int
    time: Optional[str] = None
    ip: Optional[str] = None
    device: Optional[str] = None
    status: str = "success"
    message: Optional[str] = None


class SecurityOverview(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    is_verified: bool = False
    last_login_at: Optional[str] = None
    last_login_ip: Optional[str] = None
    loginNotifications: bool = True
    sessionTimeout: bool = True
    autoLogout: bool = False
    autoLogoutMinutes: int = 30
    recent_logins: List[LoginHistoryItem] = Field(default_factory=list)
    security_score: int = 0


class PhoneBindSendCodeRequest(BaseModel):
    phone: str = Field(..., description="要绑定的手机号")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        import re
        phone = (v or "").strip()
        if not re.fullmatch(r"1[3-9]\d{9}", phone):
            raise ValueError("请输入有效的中国大陆手机号")
        return phone


class PhoneBindConfirmRequest(BaseModel):
    phone: str = Field(..., description="要绑定的手机号")
    verification_code: str = Field(..., description="6位短信验证码")
    current_password: Optional[str] = Field(
        None, description="换绑时需提供当前登录密码"
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        import re
        phone = (v or "").strip()
        if not re.fullmatch(r"1[3-9]\d{9}", phone):
            raise ValueError("请输入有效的中国大陆手机号")
        return phone

    @field_validator("verification_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("验证码必须是6位数字")
        return v

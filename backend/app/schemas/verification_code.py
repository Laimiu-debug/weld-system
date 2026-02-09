"""
Verification Code schemas for the welding system backend.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VerificationCodeBase(BaseModel):
    """Base verification code schema."""
    account: str = Field(..., description="邮箱或手机号")
    account_type: str = Field(..., description="账号类型：email 或 phone")
    purpose: str = Field(..., description="验证码用途：login, register, reset_password")

    @field_validator('account_type')
    @classmethod
    def validate_account_type(cls, v):
        if v not in ['email', 'phone']:
            raise ValueError('account_type 必须是 email 或 phone')
        return v

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v):
        if v not in ['login', 'register', 'reset_password']:
            raise ValueError('purpose 必须是 login, register 或 reset_password')
        return v


class VerificationCodeCreate(VerificationCodeBase):
    """Schema for creating verification code."""
    code: str = Field(..., description="6位验证码")
    expires_at: datetime = Field(..., description="过期时间")


class VerificationCodeRequest(BaseModel):
    """Schema for verification code request."""
    account: str = Field(..., description="邮箱或手机号")
    account_type: str = Field(..., description="账号类型：email 或 phone")
    purpose: str = Field(default="login", description="验证码用途")

    @field_validator('account_type')
    @classmethod
    def validate_account_type(cls, v):
        if v not in ['email', 'phone']:
            raise ValueError('account_type 必须是 email 或 phone')
        return v


class VerificationCodeVerify(BaseModel):
    """Schema for verifying verification code."""
    account: str = Field(..., description="邮箱或手机号")
    verification_code: str = Field(..., description="6位验证码")
    account_type: str = Field(..., description="账号类型：email 或 phone")

    @field_validator('verification_code')
    @classmethod
    def validate_code(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('验证码必须是6位数字')
        return v

    @field_validator('account_type')
    @classmethod
    def validate_account_type(cls, v):
        if v not in ['email', 'phone']:
            raise ValueError('account_type 必须是 email 或 phone')
        return v


class VerificationCodeResponse(BaseModel):
    """Schema for verification code response."""
    message: str = Field(..., description="响应消息")
    expires_in: Optional[int] = Field(None, description="验证码有效期（秒）")


class LoginWithVerificationCode(BaseModel):
    """Schema for login with verification code."""
    account: str = Field(..., description="邮箱或手机号")
    verification_code: str = Field(..., description="6位验证码")
    account_type: str = Field(..., description="账号类型：email 或 phone")

    @field_validator('verification_code')
    @classmethod
    def validate_code(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('验证码必须是6位数字')
        return v

    @field_validator('account_type')
    @classmethod
    def validate_account_type(cls, v):
        if v not in ['email', 'phone']:
            raise ValueError('account_type 必须是 email 或 phone')
        return v
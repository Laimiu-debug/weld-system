"""
Token schemas for the welding system backend.
"""
from typing import Optional

from pydantic import BaseModel
from app.schemas.user import UserResponse


class TokenBase(BaseModel):
    """Base token schema."""
    token_type: str = "bearer"


class Token(TokenBase):
    """Token response schema."""
    access_token: str
    refresh_token: str
    expires_in: int


class TokenWithUser(Token):
    """Token response schema with user information."""
    user: UserResponse


class TokenRefresh(BaseModel):
    """Token refresh request schema."""
    refresh_token: str


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: Optional[str] = None
    type: Optional[str] = None
    exp: Optional[int] = None
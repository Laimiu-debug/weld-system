"""Shared API envelope models for OpenAPI and new endpoints."""
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from app.core.observability import get_request_id

T = TypeVar("T")


class APIErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None


class APIError(BaseModel):
    detail: APIErrorDetail


class APISuccess(BaseModel, Generic[T]):
    success: bool = True
    message: str = "ok"
    data: T
    request_id: Optional[str] = None


class APIPage(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1)


def success_payload(data: T, message: str = "ok") -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
        "request_id": get_request_id(),
    }

"""Typed success envelopes for incrementally migrated business endpoints."""
from typing import Generic, TypeVar, Literal
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: T | None = None
    message: str | None = None
    request_id: str | None = None


class AttachmentUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    url: str

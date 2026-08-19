"""Shared document access checks for ID-based read/export endpoints."""
from typing import Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.data_access import DataAccessAction, DataAccessMiddleware
from app.models.user import User

T = TypeVar("T")


def require_document_access(
    db: Session,
    model: Type[T],
    document_id: int,
    user: User,
    not_found_detail: str,
    action: str = DataAccessAction.VIEW,
) -> T:
    """Load a document by ID and enforce workspace/tenant access.

    Missing documents return 404. Cross-tenant or unauthorized access
    returns 403 and never yields the document body.
    """
    document = db.query(model).filter(model.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_detail,
        )

    allowed = DataAccessMiddleware(db).check_access(user, document, action)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：您无权访问该文档",
        )
    return document

"""
User feedback endpoints — submit (user) and collect (admin).
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.api.admin_deps import get_current_active_admin
from app.core.database import get_db
from app.core.rate_limit import enforce_rate_limit
from app.models.admin import Admin
from app.models.feedback import UserFeedback
from app.models.user import User

router = APIRouter()
admin_router = APIRouter()


class FeedbackCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    contact: Optional[str] = Field(None, max_length=200)


class FeedbackAdminUpdate(BaseModel):
    admin_note: Optional[str] = Field(None, max_length=5000)


def _to_user_item(fb: UserFeedback) -> dict:
    return {
        "id": fb.id,
        "title": fb.title,
        "content": fb.content,
        "contact": fb.contact,
        "is_read": bool(fb.is_read),
        "created_at": fb.created_at.isoformat() if fb.created_at else None,
        "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
    }


def _to_admin_item(fb: UserFeedback) -> dict:
    user = fb.user
    return {
        **_to_user_item(fb),
        "user_id": fb.user_id,
        "user_email": user.email if user else None,
        "user_name": (user.full_name or user.username or user.email) if user else None,
        "read_at": fb.read_at.isoformat() if fb.read_at else None,
        "admin_note": fb.admin_note,
    }


@router.post("")
@router.post("/")
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """用户提交意见反馈。"""
    enforce_rate_limit(f"feedback-user:{current_user.id}", limit=10, window_seconds=3600)
    title = payload.title.strip()
    content = payload.content.strip()
    contact = (payload.contact or "").strip() or None
    if not title or not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="标题和内容不能为空")

    feedback = UserFeedback(
        user_id=current_user.id,
        title=title,
        content=content,
        contact=contact,
        is_read=False,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {
        "success": True,
        "message": "反馈已提交，感谢您的建议",
        "data": _to_user_item(feedback),
    }


@router.get("/mine")
def list_my_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """用户查看自己的反馈列表。"""
    query = db.query(UserFeedback).filter(UserFeedback.user_id == current_user.id)
    total = query.count()
    items = (
        query.order_by(UserFeedback.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "success": True,
        "data": {
            "items": [_to_user_item(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@admin_router.get("")
@admin_router.get("/")
def admin_list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin),
) -> Any:
    """管理端反馈列表。"""
    query = db.query(UserFeedback)
    if is_read is not None:
        query = query.filter(UserFeedback.is_read == is_read)
    total = query.count()
    unread_count = db.query(UserFeedback).filter(UserFeedback.is_read == False).count()  # noqa: E712
    items = (
        query.order_by(UserFeedback.is_read.asc(), UserFeedback.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "success": True,
        "data": {
            "items": [_to_admin_item(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "unread_count": unread_count,
        },
    }


@admin_router.post("/{feedback_id}/mark-read")
def admin_mark_read(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin),
) -> Any:
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    if not feedback.is_read:
        feedback.is_read = True
        feedback.read_at = datetime.utcnow()
        feedback.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(feedback)
    return {"success": True, "message": "已标记为已读", "data": _to_admin_item(feedback)}


@admin_router.patch("/{feedback_id}")
def admin_update_feedback(
    feedback_id: int,
    payload: FeedbackAdminUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin),
) -> Any:
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    if payload.admin_note is not None:
        feedback.admin_note = payload.admin_note.strip() or None
    feedback.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(feedback)
    return {"success": True, "message": "已更新", "data": _to_admin_item(feedback)}


@admin_router.delete("/{feedback_id}")
def admin_delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin),
) -> Any:
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    db.delete(feedback)
    db.commit()
    return {"success": True, "message": "已删除"}

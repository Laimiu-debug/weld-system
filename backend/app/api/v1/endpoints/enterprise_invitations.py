"""Enterprise invitation endpoints."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints.enterprise_deps import check_enterprise_membership
from app.models.user import User
from app.schemas.api import success_payload
from app.services.invitation_service import InvitationService

router = APIRouter()


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = "employee"
    factory_id: Optional[int] = None
    department_id: Optional[str] = None
    department: Optional[str] = None
    company_role_id: Optional[int] = None
    permissions: Dict[str, bool] = {}
    message: Optional[str] = None
    expires_at: Optional[str] = None

    @field_validator("factory_id", "company_role_id", mode="before")
    @classmethod
    def empty_id_to_none(cls, value):
        if value == "" or value is None:
            return None
        return value


class InvitationAccept(BaseModel):
    token: str


@router.get("/invitations/preview")
def preview_invitation(
    token: str = Query(..., min_length=8),
    db: Session = Depends(get_db),
) -> Any:
    service = InvitationService(db)
    return success_payload(service.preview(token), "ok")


@router.post("/invitations/accept")
def accept_invitation(
    body: InvitationAccept,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    service = InvitationService(db)
    data = service.accept_invitation(body.token, current_user)
    return success_payload(data, "已加入企业")


@router.post("/invitations")
def create_invitation(
    body: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    current_user = check_enterprise_membership(current_user)
    service = InvitationService(db)
    data = service.create_invitation(current_user, body.model_dump())
    message = "邀请已发送" if data.get("email_sent") else "邀请已创建，邮件未发出，请复制邀请链接"
    return success_payload(data, message)


@router.get("/invitations")
def list_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
) -> Any:
    current_user = check_enterprise_membership(current_user)
    service = InvitationService(db)
    items, total = service.list_invitations(
        current_user,
        status_filter=status,
        page=page,
        page_size=page_size,
    )
    return success_payload(
        {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size else 0,
        }
    )


@router.post("/invitations/{invitation_id}/cancel")
def cancel_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    current_user = check_enterprise_membership(current_user)
    service = InvitationService(db)
    return success_payload(service.cancel_invitation(current_user, invitation_id), "邀请已取消")


@router.post("/invitations/{invitation_id}/resend")
def resend_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    current_user = check_enterprise_membership(current_user)
    service = InvitationService(db)
    data = service.resend_invitation(current_user, invitation_id)
    message = "邀请已重新发送" if data.get("email_sent") else "邀请已更新，邮件未发出"
    return success_payload(data, message)

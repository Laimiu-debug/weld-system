"""Enterprise email invitation service."""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.module_permissions import (
    ALLOWED_INVITE_ROLES,
    ensure_can_manage_invitations,
    serialize_permissions_for_user,
    validate_invite_role,
    validate_invite_targets,
)
from app.models.company import Company, CompanyEmployee, CompanyInvitation, Factory
from app.models.user import User
from app.services.email_service import email_service
from app.services.enterprise_service import EnterpriseService

logger = logging.getLogger(__name__)


def _parse_optional_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class InvitationService:
    def __init__(self, db: Session):
        self.db = db
        self.enterprise = EnterpriseService(db)

    def get_company_for_user(self, user: User) -> Company:
        company = self.enterprise.get_company_by_owner(user.id)
        if company:
            return company
        membership = (
            self.db.query(CompanyEmployee)
            .filter(
                CompanyEmployee.user_id == user.id,
                CompanyEmployee.status == "active",
            )
            .first()
        )
        if membership:
            company = self.enterprise.get_company_by_id(membership.company_id)
            if company:
                return company
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到企业信息",
        )

    def create_invitation(self, current_user: User, payload: Dict[str, Any]) -> Dict[str, Any]:
        company = ensure_can_manage_invitations(self.db, current_user)
        email = str(payload.get("email") or "").strip().lower()
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请填写邮箱")

        role = validate_invite_role(payload.get("role"))
        company_role_id, factory_id = validate_invite_targets(
            self.db,
            company,
            company_role_id=_parse_optional_int(payload.get("company_role_id")),
            factory_id=_parse_optional_int(payload.get("factory_id")),
        )

        current_employee_count = (
            self.db.query(CompanyEmployee)
            .filter(
                CompanyEmployee.company_id == company.id,
                CompanyEmployee.status == "active",
            )
            .count()
        )
        pending_count = (
            self.db.query(CompanyInvitation)
            .filter(
                CompanyInvitation.company_id == company.id,
                CompanyInvitation.status == "pending",
                CompanyInvitation.expires_at > datetime.utcnow(),
            )
            .count()
        )
        if current_employee_count + pending_count >= (company.max_employees or 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"已达到员工配额上限（{company.max_employees}人）",
            )

        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            already = (
                self.db.query(CompanyEmployee)
                .filter(
                    CompanyEmployee.company_id == company.id,
                    CompanyEmployee.user_id == existing_user.id,
                    CompanyEmployee.status == "active",
                )
                .first()
            )
            if already:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已是企业员工",
                )

        pending = (
            self.db.query(CompanyInvitation)
            .filter(
                CompanyInvitation.company_id == company.id,
                CompanyInvitation.email == email,
                CompanyInvitation.status == "pending",
            )
            .all()
        )
        for old in pending:
            old.status = "cancelled"
            old.updated_at = datetime.utcnow()

        expires_at = payload.get("expires_at")
        if isinstance(expires_at, str) and expires_at:
            try:
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                expires_at = datetime.utcnow() + timedelta(days=7)
        if not isinstance(expires_at, datetime):
            expires_at = datetime.utcnow() + timedelta(days=7)

        department = payload.get("department") or payload.get("department_id") or payload.get("department_name")
        token = secrets.token_urlsafe(32)
        invitation_code = f"INV-{secrets.token_hex(4).upper()}"

        invitation = CompanyInvitation(
            company_id=company.id,
            email=email,
            token=token,
            invitation_code=invitation_code,
            role=role,
            company_role_id=company_role_id,
            factory_id=factory_id,
            department=str(department) if department else None,
            permissions=payload.get("permissions") or {},
            message=payload.get("message"),
            status="pending",
            expires_at=expires_at,
            invited_by=current_user.id,
        )
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)

        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
        invite_url = f"{frontend}/register?invite={token}"
        email_sent = email_service.send_invitation_email(
            to_email=email,
            company_name=company.name,
            invite_url=invite_url,
            invitation_code=invitation_code,
            message=invitation.message,
            expires_at=expires_at,
        )
        data = self.serialize(invitation)
        data["invite_url"] = invite_url
        data["email_sent"] = email_sent
        return data

    def list_invitations(
        self,
        current_user: User,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        company = ensure_can_manage_invitations(self.db, current_user)
        self._expire_stale(company.id)
        query = self.db.query(CompanyInvitation).filter(CompanyInvitation.company_id == company.id)
        if status_filter:
            query = query.filter(CompanyInvitation.status == status_filter)
        total = query.count()
        items = (
            query.order_by(CompanyInvitation.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [self.serialize(item) for item in items], total

    def cancel_invitation(self, current_user: User, invitation_id: int) -> Dict[str, Any]:
        invitation = self._owned_invitation(current_user, invitation_id)
        if invitation.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能取消待接受的邀请")
        invitation.status = "cancelled"
        invitation.updated_at = datetime.utcnow()
        self.db.commit()
        return self.serialize(invitation)

    def resend_invitation(self, current_user: User, invitation_id: int) -> Dict[str, Any]:
        invitation = self._owned_invitation(current_user, invitation_id)
        if invitation.status not in {"pending", "expired"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该邀请无法重新发送")
        invitation.token = secrets.token_urlsafe(32)
        invitation.invitation_code = f"INV-{secrets.token_hex(4).upper()}"
        invitation.status = "pending"
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        invitation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(invitation)

        company = self.enterprise.get_company_by_id(invitation.company_id)
        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
        invite_url = f"{frontend}/register?invite={invitation.token}"
        email_sent = email_service.send_invitation_email(
            to_email=invitation.email,
            company_name=company.name if company else "焊序企业",
            invite_url=invite_url,
            invitation_code=invitation.invitation_code,
            message=invitation.message,
            expires_at=invitation.expires_at,
        )
        data = self.serialize(invitation)
        data["invite_url"] = invite_url
        data["email_sent"] = email_sent
        return data

    def preview(self, token: str) -> Dict[str, Any]:
        invitation = self._get_by_token(token)
        self._ensure_pending(invitation)
        company = self.enterprise.get_company_by_id(invitation.company_id)
        return {
            "email": invitation.email,
            "company_name": company.name if company else None,
            "role": invitation.role,
            "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
            "status": invitation.status,
        }

    def require_pending(self, token: str, email: str) -> CompanyInvitation:
        invitation = self._get_by_token(token)
        self._ensure_pending(invitation)
        if invitation.email.lower() != email.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="注册邮箱必须与邀请邮箱一致",
            )
        return invitation

    def accept_invitation(self, token: str, user: User) -> Dict[str, Any]:
        invitation = self.require_pending(token, user.email)
        existing = (
            self.db.query(CompanyEmployee)
            .filter(
                CompanyEmployee.company_id == invitation.company_id,
                CompanyEmployee.user_id == user.id,
                CompanyEmployee.status == "active",
            )
            .first()
        )
        if existing:
            invitation.status = "accepted"
            invitation.accepted_at = datetime.utcnow()
            invitation.accepted_user_id = user.id
            self.db.commit()
            return self.serialize(invitation)

        company = self.enterprise.get_company_by_id(invitation.company_id)
        # Never elevate invitees to admin via invitation payload
        safe_role = invitation.role if invitation.role in ALLOWED_INVITE_ROLES else "employee"

        employee = CompanyEmployee(
            company_id=invitation.company_id,
            user_id=user.id,
            role=safe_role,
            company_role_id=invitation.company_role_id,
            factory_id=invitation.factory_id,
            department=invitation.department,
            permissions=invitation.permissions or {},
            status="active",
            invited_at=invitation.created_at,
            joined_at=datetime.utcnow(),
            created_by=invitation.invited_by,
        )
        self.db.add(employee)
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_user_id = user.id
        if company:
            user.membership_type = "enterprise"
            # Keep company tier for quota/billing display; UI permissions come from CompanyRole.
            user.member_tier = company.membership_tier
            self.db.flush()
            user.permissions = serialize_permissions_for_user(self.db, user)
        self.db.commit()
        return self.serialize(invitation)

    def serialize(self, invitation: CompanyInvitation) -> Dict[str, Any]:
        factory_name = None
        if invitation.factory_id:
            factory = self.db.query(Factory).filter(Factory.id == invitation.factory_id).first()
            factory_name = factory.name if factory else None
        return {
            "id": str(invitation.id),
            "email": invitation.email,
            "invitation_code": invitation.invitation_code,
            "role": invitation.role,
            "factory_id": str(invitation.factory_id) if invitation.factory_id else None,
            "factory_name": factory_name,
            "department_id": invitation.department,
            "department_name": invitation.department,
            "status": invitation.status,
            "permissions": invitation.permissions or {},
            "message": invitation.message,
            "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
            "accepted_at": invitation.accepted_at.isoformat() if invitation.accepted_at else None,
            "created_at": invitation.created_at.isoformat() if invitation.created_at else None,
        }

    def _owned_invitation(self, current_user: User, invitation_id: int) -> CompanyInvitation:
        company = ensure_can_manage_invitations(self.db, current_user)
        invitation = (
            self.db.query(CompanyInvitation)
            .filter(
                CompanyInvitation.id == invitation_id,
                CompanyInvitation.company_id == company.id,
            )
            .first()
        )
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邀请不存在")
        return invitation

    def _get_by_token(self, token: str) -> CompanyInvitation:
        invitation = self.db.query(CompanyInvitation).filter(CompanyInvitation.token == token).first()
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邀请不存在或已失效")
        return invitation

    def _ensure_pending(self, invitation: CompanyInvitation) -> None:
        if invitation.status == "cancelled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请已取消")
        if invitation.status == "accepted":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请已被接受")
        if invitation.expires_at <= datetime.utcnow() or invitation.status == "expired":
            invitation.status = "expired"
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请已过期")

    def _expire_stale(self, company_id: int) -> None:
        (
            self.db.query(CompanyInvitation)
            .filter(
                CompanyInvitation.company_id == company_id,
                CompanyInvitation.status == "pending",
                CompanyInvitation.expires_at <= datetime.utcnow(),
            )
            .update({"status": "expired"}, synchronize_session=False)
        )
        self.db.commit()

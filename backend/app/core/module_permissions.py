"""Module-level permission checks for personal roles and enterprise CompanyRole."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.models.company import Company, CompanyEmployee, CompanyRole, Factory
from app.models.user import User

ALLOWED_INVITE_ROLES = frozenset({"employee", "manager"})

_ACTION_TO_ROLE_KEY = {
    "read": "view",
    "view": "view",
    "create": "create",
    "update": "edit",
    "edit": "edit",
    "delete": "delete",
    "export": "view",
    "approve": "approve",
}

_RESOURCE_TO_MODULE = {
    "wps": "wps_management",
    "pqr": "pqr_management",
    "ppqr": "ppqr_management",
    "materials": "materials_management",
    "material": "materials_management",
    "welders": "welders_management",
    "welder": "welders_management",
    "equipment": "equipment_management",
    "production": "production_management",
    "quality": "quality_management",
    "employees": "employee_management",
    "employee": "employee_management",
    "factories": "factory_management",
    "factory": "factory_management",
    "reports": "reports_management",
}

_DEFAULT_EMPLOYEE_ACTIONS = frozenset({"read", "view", "create"})


def _parse_permissions(raw: Any) -> Dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def get_active_membership(
    db: Session, user: User, company_id: Optional[int] = None
) -> Optional[CompanyEmployee]:
    query = db.query(CompanyEmployee).filter(
        CompanyEmployee.user_id == user.id,
        CompanyEmployee.status == "active",
    )
    if company_id is not None:
        query = query.filter(CompanyEmployee.company_id == company_id)
    return query.first()


def get_owned_company(db: Session, user: User) -> Optional[Company]:
    return (
        db.query(Company)
        .filter(Company.owner_id == user.id, Company.is_active == True)  # noqa: E712
        .first()
    )


def resolve_company_for_user(db: Session, user: User) -> Company:
    owned = get_owned_company(db, user)
    if owned:
        return owned
    membership = get_active_membership(db, user)
    if membership:
        company = db.query(Company).filter(Company.id == membership.company_id).first()
        if company:
            return company
    raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="未找到企业信息")


def _module_allowed_from_role(permissions: Dict[str, Any], module: str, action: str) -> bool:
    role_key = _ACTION_TO_ROLE_KEY.get(action, action)
    module_perms = permissions.get(module)
    if isinstance(module_perms, bool):
        return module_perms
    if isinstance(module_perms, dict):
        return bool(module_perms.get(role_key, False))
    return False


def user_has_module_permission(db: Session, user: User, resource: str, action: str) -> bool:
    if getattr(user, "is_superuser", False) or getattr(user, "is_admin", False):
        return True

    module = _RESOURCE_TO_MODULE.get(resource, f"{resource}_management")

    owned = get_owned_company(db, user)
    if owned:
        return True

    membership = get_active_membership(db, user)
    if membership:
        if membership.role == "admin":
            return True
        if membership.company_role_id:
            role = (
                db.query(CompanyRole)
                .filter(
                    CompanyRole.id == membership.company_role_id,
                    CompanyRole.company_id == membership.company_id,
                    CompanyRole.is_active == True,  # noqa: E712
                )
                .first()
            )
            if role:
                return _module_allowed_from_role(role.permissions or {}, module, action)
            return False
        return action in _DEFAULT_EMPLOYEE_ACTIONS

    from app.services.user_service import user_service

    return user_service.has_permission(db, user.id, resource, action)


def ensure_module_permission(db: Session, user: User, resource: str, action: str) -> None:
    if not user_has_module_permission(db, user, resource, action):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail=f"权限不足：无法{action} {resource}",
        )


def user_can_manage_employees(db: Session, user: User, company: Company) -> bool:
    if getattr(user, "is_superuser", False) or getattr(user, "is_admin", False):
        return True
    if company.owner_id == user.id:
        return True
    membership = get_active_membership(db, user, company.id)
    if not membership:
        return False
    if membership.role == "admin":
        return True
    if membership.company_role_id:
        role = (
            db.query(CompanyRole)
            .filter(
                CompanyRole.id == membership.company_role_id,
                CompanyRole.company_id == company.id,
                CompanyRole.is_active == True,  # noqa: E712
            )
            .first()
        )
        if role:
            return _module_allowed_from_role(
                role.permissions or {}, "employee_management", "create"
            )
    return False


def ensure_can_manage_invitations(db: Session, user: User) -> Company:
    company = resolve_company_for_user(db, user)
    if not user_can_manage_employees(db, user, company):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="权限不足：仅企业所有者或具备员工管理权限的成员可管理邀请",
        )
    return company


def validate_invite_role(role: Optional[str]) -> str:
    normalized = (role or "employee").strip().lower()
    if normalized not in ALLOWED_INVITE_ROLES:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="邀请角色仅允许 employee 或 manager，不能指定 admin",
        )
    return normalized


def validate_invite_targets(
    db: Session,
    company: Company,
    *,
    company_role_id: Optional[int],
    factory_id: Optional[int],
) -> Tuple[Optional[int], Optional[int]]:
    if company_role_id is not None:
        role = (
            db.query(CompanyRole)
            .filter(
                CompanyRole.id == company_role_id,
                CompanyRole.company_id == company.id,
                CompanyRole.is_active == True,  # noqa: E712
            )
            .first()
        )
        if not role:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="指定的企业角色不属于本公司或不存在",
            )
    if factory_id is not None:
        factory = (
            db.query(Factory)
            .filter(Factory.id == factory_id, Factory.company_id == company.id)
            .first()
        )
        if not factory:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="指定的工厂不属于本公司或不存在",
            )
    return company_role_id, factory_id


def flatten_company_role_permissions(role_permissions: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not role_permissions:
        return out
    for module, value in role_permissions.items():
        if isinstance(value, bool):
            out[module] = value
        elif isinstance(value, dict):
            out[module] = value
    return out


def build_effective_permissions_payload(db: Session, user: User) -> Dict[str, Any]:
    base = _parse_permissions(getattr(user, "permissions", None))
    owned = get_owned_company(db, user)
    if owned:
        base.update(
            {
                "employee_management": True,
                "factory_management": True,
                "multi_factory_management": True,
                "department_management": True,
                "role_management": True,
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "materials_management": True,
                "welders_management": True,
                "equipment_management": True,
                "production_management": True,
                "quality_management": True,
                "reports_management": True,
            }
        )
        return base

    membership = get_active_membership(db, user)
    if membership and membership.company_role_id:
        role = (
            db.query(CompanyRole)
            .filter(
                CompanyRole.id == membership.company_role_id,
                CompanyRole.is_active == True,  # noqa: E712
            )
            .first()
        )
        if role:
            base.update(flatten_company_role_permissions(role.permissions or {}))
            return base

    if membership and membership.role == "admin":
        base.update(
            {
                "employee_management": True,
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "materials_management": True,
                "welders_management": True,
                "equipment_management": True,
                "production_management": True,
                "quality_management": True,
            }
        )
    return base


def serialize_permissions_for_user(db: Session, user: User) -> str:
    return json.dumps(build_effective_permissions_payload(db, user), ensure_ascii=False)

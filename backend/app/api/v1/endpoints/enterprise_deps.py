"""Shared helpers for enterprise API routers."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.module_permissions import get_active_membership, get_owned_company
from app.models.user import User


def check_enterprise_membership(current_user: User = Depends(deps.get_current_active_user)) -> User:
    """Require an active enterprise owner or employee."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用",
        )
    return current_user


def require_enterprise_member(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> User:
    """Active user who owns a company or is an active employee."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用",
        )
    if get_owned_company(db, current_user) or get_active_membership(db, current_user):
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="需要企业所有者或在职员工身份",
    )

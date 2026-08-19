"""Shared helpers for enterprise API routers."""
from fastapi import HTTPException, status

from app.models.user import User


def check_enterprise_membership(current_user: User) -> User:
    """Require an active user before enterprise APIs."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用",
        )
    return current_user

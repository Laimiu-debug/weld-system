"""
Admin authentication endpoints.
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.schemas.admin import AdminLoginResponse
from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.services.admin_service import admin_service

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Admin login endpoint. Tokens are issued only by the server."""
    admin = admin_service.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin_service.is_active(admin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="管理员账户已被禁用",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(admin.id),
        expires_delta=access_token_expires
    )

    admin_service.update_last_login(db, admin)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": {
            "id": admin.id,
            "email": admin.email,
            "username": admin.username,
            "full_name": admin.full_name,
            "is_active": admin.is_active,
            "is_super_admin": admin.is_super_admin,
            "admin_level": admin.admin_level,
            "created_at": admin.created_at,
            "updated_at": admin.updated_at,
            "last_login_at": admin.last_login_at,
        },
    }


@router.post("/logout")
def admin_logout() -> Any:
    """Admin logout endpoint."""
    return {"message": "已成功退出登录"}

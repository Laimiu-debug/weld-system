"""
Admin authentication endpoints.
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.schemas.admin import Admin as AdminSchema, AdminLoginResponse
from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.admin import Admin
from app.services.admin_service import admin_service

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Admin login endpoint.
    """
    print(f"DEBUG: Admin login endpoint called with username: {form_data.username}")
    print(f"DEBUG: Time: {__import__('datetime').datetime.now()}")
    # Authenticate admin
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

    # Create access token - 使用管理员ID作为subject
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    raw_token = create_access_token(
        subject=str(admin.id),  # 使用admin.id
        expires_delta=access_token_expires
    )

    # Debug token creation
    print(f"DEBUG: Raw token from create_access_token: {raw_token}")
    print(f"DEBUG: Raw token type: {type(raw_token)}")
    print(f"DEBUG: Admin ID used for token: {admin.id}")

    # 验证这是否是正确的JWT格式
    if '.' not in raw_token:
        print(f"ERROR: Raw token is not in JWT format! Forcing correct format...")
        # 如果不是正确格式，我们强制使用一个已知的正确格式
        import time
        import base64
        from jose import jwt

        # 手动创建一个正确的JWT token
        current_time = int(time.time())
        expire_time = current_time + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

        payload = {
            "exp": expire_time,
            "sub": str(admin.id),
            "type": "access"
        }

        access_token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        print(f"DEBUG: Manually created JWT token: {access_token}")
    else:
        access_token = raw_token
        print(f"DEBUG: Using original token: {access_token}")

    # Update last login time
    admin_service.update_last_login(db, admin)

    # Prepare admin data for response (使用独立的管理员信息)
    admin_data = {
        "id": admin.id,
        "email": admin.email,
        "username": admin.username,
        "full_name": admin.full_name,
        "is_active": admin.is_active,
        "is_super_admin": admin.is_super_admin,
        "admin_level": admin.admin_level,
        "created_at": admin.created_at,
        "updated_at": admin.updated_at,
        "last_login_at": admin.last_login_at
    }

    # 使用正确的JWT token（从create_access_token生成）
    print(f"DEBUG: Using JWT token: {access_token}")
    print(f"DEBUG: Token contains dots: {'.' in access_token}")

    # 构建响应
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": admin_data
    }


@router.post("/test-token")
async def test_token_direct() -> Any:
    """
    测试token生成的直接端点
    """
    from datetime import timedelta
    from app.core.security import create_access_token
    from app.core.config import settings

    # 直接创建token
    admin_id = "3"
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    print(f"TEST: Creating token for admin_id: {admin_id}")
    print(f"TEST: Secret key: {settings.SECRET_KEY}")
    print(f"TEST: Algorithm: {settings.ALGORITHM}")
    print(f"TEST: File reloaded at: {__import__('datetime').datetime.now()}")

    token = create_access_token(
        subject=admin_id,
        expires_delta=expires_delta
    )

    print(f"TEST: Generated token: {token}")
    print(f"TEST: Token type: {type(token)}")
    print(f"TEST: Token length: {len(token)}")

    # 检查token格式
    if '.' in token:
        parts = token.split('.')
        print(f"TEST: Token parts count: {len(parts)}")
        print(f"TEST: Header: {parts[0]}")
        print(f"TEST: Payload: {parts[1]}")
        print(f"TEST: Signature: {parts[2]}")
    else:
        print("TEST: WARNING: Token doesn't contain dots - not a proper JWT format!")

    return {
        "test_token": token,
        "token_type": "bearer",
        "message": "Test token generated"
    }


@router.post("/logout")
async def admin_logout() -> Any:
    """
    Admin logout endpoint.
    """
    return {"message": "已成功退出登录"}

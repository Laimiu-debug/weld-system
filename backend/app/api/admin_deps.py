"""
Admin authentication dependencies.
"""
from typing import Generator, Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_token
from app.models.admin import Admin
from app.models.user import User
from app.services.admin_service import admin_service

# OAuth2密码流程，使用管理员专用的token URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/admin/auth/login"
)


async def get_current_admin(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Admin:
    """
    获取当前认证的管理员.

    Args:
        db: 数据库会话
        token: JWT访问令牌

    Returns:
        当前管理员对象

    Raises:
        HTTPException: 如果令牌无效或管理员不存在
    """
    # 验证令牌
    admin_id = verify_token(token, token_type="access")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 直接获取管理员信息
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin


async def get_current_active_admin(
    current_admin: Admin = Depends(get_current_admin)
) -> Admin:
    """
    获取当前活跃管理员.

    Args:
        current_admin: 当前管理员

    Returns:
        当前活跃管理员

    Raises:
        HTTPException: 如果管理员未激活
    """
    if not admin_service.is_active(current_admin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="管理员账户已被禁用"
        )
    return current_admin


async def get_current_super_admin(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Admin:
    """
    获取当前超级管理员.

    Args:
        current_admin: 当前活跃管理员

    Returns:
        当前超级管理员

    Raises:
        HTTPException: 如果管理员不是超级管理员
    """
    if not admin_service.is_super_admin(current_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_admin


def check_admin_permission(required_permission: str):
    """
    检查管理员权限的依赖工厂函数.

    Args:
        required_permission: 需要的权限

    Returns:
        权限检查依赖函数
    """
    async def permission_checker(
        current_admin: Admin = Depends(get_current_active_admin),
        db: Session = Depends(get_db)
    ) -> Admin:
        from app.services.permission_service import get_permission_service
        permission_service = get_permission_service(db)
        
        if not permission_service.has_permission(current_admin.id, required_permission, is_admin=True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {required_permission}"
            )

        return current_admin

    return permission_checker


def check_admin_permissions(required_permissions: List[str], require_all: bool = False):
    """
    检查管理员多个权限的依赖工厂函数.

    Args:
        required_permissions: 需要的权限列表
        require_all: 是否需要所有权限（默认为False，只需要任意一个）

    Returns:
        权限检查依赖函数
    """
    async def permissions_checker(
        current_admin: Admin = Depends(get_current_active_admin),
        db: Session = Depends(get_db)
    ) -> Admin:
        from app.services.permission_service import get_permission_service
        permission_service = get_permission_service(db)
        
        if require_all:
            # 需要所有权限
            if not permission_service.has_all_permissions(current_admin.id, required_permissions, is_admin=True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要所有权限: {', '.join(required_permissions)}"
                )
        else:
            # 只需要任意一个权限
            if not permission_service.has_any_permission(current_admin.id, required_permissions, is_admin=True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下任意权限: {', '.join(required_permissions)}"
                )

        return current_admin

    return permissions_checker
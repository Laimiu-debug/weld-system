"""
Common dependencies for the welding system backend API.
"""
from typing import Generator, Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.services.user_service import user_service

# OAuth2密码流程
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前认证用户.

    Args:
        db: 数据库会话
        token: JWT访问令牌

    Returns:
        当前用户对象

    Raises:
        HTTPException: 如果令牌无效或用户不存在
    """
    # 验证令牌
    user_id = verify_token(token, token_type="access")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户信息
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户.

    Args:
        current_user: 当前用户

    Returns:
        当前活跃用户

    Raises:
        HTTPException: 如果用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    获取当前已验证用户.

    Args:
        current_user: 当前活跃用户

    Returns:
        当前已验证用户

    Raises:
        HTTPException: 如果用户未验证邮箱
    """
    print(f"[DEBUG] get_current_verified_user called for user: {current_user.email}, is_verified: {current_user.is_verified}")

    # 开发环境豁免邮箱验证要求
    if settings.DEVELOPMENT:
        print(f"[DEBUG] Development environment, bypassing email verification for user: {current_user.email}")
        return current_user

    # 企业用户豁免邮箱验证要求
    if current_user.membership_type == "enterprise":
        print(f"[DEBUG] User {current_user.email} is enterprise user, bypassing email verification")
        return current_user

    if not current_user.is_verified:
        print(f"[DEBUG] User {current_user.email} is not verified, raising exception")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先验证邮箱地址"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_verified_user)
) -> User:
    """
    获取当前管理员用户.

    Args:
        current_user: 当前已验证用户

    Returns:
        当前管理员用户

    Raises:
        HTTPException: 如果用户不是管理员
    """
    print(f"[DEBUG] get_current_admin_user called for user: {current_user.email}")
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user


def check_user_permission(required_permission: str):
    """
    检查用户权限的依赖工厂函数.

    Args:
        required_permission: 需要的权限

    Returns:
        权限检查依赖函数
    """
    async def permission_checker(
        current_user: User = Depends(get_current_verified_user),
        db: Session = Depends(get_db)
    ) -> User:
        from app.services.permission_service import get_permission_service
        permission_service = get_permission_service(db)
        
        if not permission_service.has_permission(current_user.id, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {required_permission}"
            )

        return current_user

    return permission_checker


def check_user_permissions(required_permissions: List[str], require_all: bool = False):
    """
    检查用户多个权限的依赖工厂函数.

    Args:
        required_permissions: 需要的权限列表
        require_all: 是否需要所有权限（默认为False，只需要任意一个）

    Returns:
        权限检查依赖函数
    """
    async def permissions_checker(
        current_user: User = Depends(get_current_verified_user),
        db: Session = Depends(get_db)
    ) -> User:
        from app.services.permission_service import get_permission_service
        permission_service = get_permission_service(db)
        
        if require_all:
            # 需要所有权限
            if not permission_service.has_all_permissions(current_user.id, required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要所有权限: {', '.join(required_permissions)}"
                )
        else:
            # 只需要任意一个权限
            if not permission_service.has_any_permission(current_user.id, required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下任意权限: {', '.join(required_permissions)}"
                )

        return current_user

    return permissions_checker


def check_member_tier(min_tier: str):
    """
    检查会员等级的依赖工厂函数.

    Args:
        min_tier: 最低会员等级

    Returns:
        会员等级检查依赖函数
    """
    tier_hierarchy = {
        "free": 0,
        "pro": 1,
        "advanced": 2,
        "flagship": 3,
        "enterprise": 4
    }

    async def tier_checker(
        current_user: User = Depends(get_current_verified_user)
    ) -> User:
        user_tier = current_user.member_tier or "free"

        if (tier_hierarchy.get(user_tier, 0) <
            tier_hierarchy.get(min_tier, 0)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {min_tier} 会员等级或更高"
            )

        return current_user

    return tier_checker


class PaginationParams:
    """分页参数."""

    def __init__(
        self,
        page: int = 1,
        size: int = 20,
        max_size: int = 100
    ):
        self.page = max(1, page)
        self.size = min(max(1, size), max_size)
        self.offset = (self.page - 1) * self.size
        self.limit = self.size


def get_pagination_params(
    page: int = 1,
    size: int = 20
) -> PaginationParams:
    """
    获取分页参数.

    Args:
        page: 页码，默认为1
        size: 每页大小，默认为20

    Returns:
        分页参数对象
    """
    return PaginationParams(page=page, size=size)


class SearchParams:
    """搜索参数."""

    def __init__(
        self,
        q: Optional[str] = None,
        sort: Optional[str] = None,
        order: str = "asc"
    ):
        self.q = q
        self.sort = sort
        self.order = order if order.lower() in ["asc", "desc"] else "asc"


def get_search_params(
    q: Optional[str] = None,
    sort: Optional[str] = None,
    order: str = "asc"
) -> SearchParams:
    """
    获取搜索参数.

    Args:
        q: 搜索关键词
        sort: 排序字段
        order: 排序方向 (asc/desc)

    Returns:
        搜索参数对象
    """
    return SearchParams(q=q, sort=sort, order=order)
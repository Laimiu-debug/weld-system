"""
User management endpoints for the welding system backend.
"""
from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import user_service
from app.services.membership_service import MembershipService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """获取用户列表."""
    users = user_service.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """创建用户."""
    user = user_service.create(db, obj_in=user_in)
    return user


@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """获取当前用户信息."""
    # 从数据库重新查询最新的用户信息
    updated_user = user_service.get(db, id=current_user.id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return updated_user


@router.put("/me", response_model=UserResponse)
def update_user_me(
    user_in: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """更新当前用户信息."""
    user = user_service.get(db, id=current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    user = user_service.update(db, db_obj=user, obj_in=user_in)
    return user


@router.get("/me-membership")
def get_user_membership_info(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """获取当前用户的会员信息."""
    membership_service = MembershipService(db)
    membership_info = membership_service.get_user_membership_info(current_user.id)

    if not membership_info:
        limits = membership_service.get_membership_limits("free")
        features = membership_service.get_membership_features("free")
        member_tier = current_user.member_tier or "free"
        subscription_start_date = current_user.created_at.strftime('%Y-%m-%d') if hasattr(current_user, 'created_at') and current_user.created_at else None

        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "membership_tier": member_tier,
            "membership_type": current_user.membership_type or "personal",
            "subscription_status": "active",
            "subscription_start_date": subscription_start_date,
            "subscription_end_date": None,
            "auto_renewal": current_user.auto_renewal if hasattr(current_user, 'auto_renewal') else False,
            "features": features,
            "quotas": membership_service._build_quota_payload(current_user.id, limits),
        }

    return membership_info


@router.get("/me-usage")
def get_user_usage_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """获取当前用户的使用统计（按实际文档数）。"""
    membership_service = MembershipService(db)
    return membership_service.get_actual_usage_counts(current_user.id)


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int = Path(..., ge=1, description="用户ID,必须是正整数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """获取指定用户信息."""
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    user_id: int = Path(..., ge=1, description="用户ID,必须是正整数"),
    user_in: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """更新指定用户信息."""
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    user = user_service.update(db, db_obj=user, obj_in=user_in)
    return user
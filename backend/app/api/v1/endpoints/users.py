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
async def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """获取用户列表."""
    users = user_service.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserResponse)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """创建用户."""
    user = user_service.create(db, obj_in=user_in)
    return user


@router.get("/me", response_model=UserResponse)
async def read_user_me(
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
async def update_user_me(
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
async def get_user_membership_info(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """获取当前用户的会员信息."""
    print(f"[DEBUG] 获取会员信息: user_id={current_user.id}, email={current_user.email}")

    membership_service = MembershipService(db)
    membership_info = membership_service.get_user_membership_info(current_user.id)

    # 如果没有会员信息，返回默认的免费会员信息
    if not membership_info:
        print(f"[DEBUG] 用户没有会员记录，返回默认免费会员信息")

        # 获取默认的免费会员限制
        limits = membership_service.get_membership_limits("free")
        print(f"[DEBUG] 免费会员配额限制: {limits}")

        # 获取免费会员功能列表
        features = membership_service.get_membership_features("free")
        print(f"[DEBUG] 免费会员功能列表: {features}")

        # 获取用户会员等级
        member_tier = current_user.member_tier or "free"

        # 对于免费版，订阅开始日期是注册日期
        subscription_start_date = current_user.created_at.strftime('%Y-%m-%d') if hasattr(current_user, 'created_at') and current_user.created_at else None

        # 对于免费版，订阅状态是active（激活），结束日期是null（永久）
        subscription_status = "active"
        subscription_end_date = None  # 免费版永久有效

        response = {
            "user_id": current_user.id,
            "email": current_user.email,
            "membership_tier": member_tier,
            "membership_type": current_user.membership_type or "personal",
            "subscription_status": subscription_status,
            "subscription_start_date": subscription_start_date,
            "subscription_end_date": subscription_end_date,
            "auto_renewal": current_user.auto_renewal if hasattr(current_user, 'auto_renewal') else False,
            "features": features,
            "quotas": {
                "wps": {"used": current_user.wps_quota_used or 0, "limit": limits.get("wps", 10)},
                "pqr": {"used": current_user.pqr_quota_used or 0, "limit": limits.get("pqr", 10)},
                "ppqr": {"used": current_user.ppqr_quota_used or 0, "limit": limits.get("ppqr", 0)},
                "storage": {"used": current_user.storage_quota_used or 0, "limit": limits.get("storage", 100)},
            }
        }

        print(f"[DEBUG] 返回会员信息: {response}")
        return response

    print(f"[DEBUG] 返回数据库中的会员信息")
    return membership_info


@router.get("/me-usage")
async def get_user_usage_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """获取当前用户的使用统计."""
    print(f"[DEBUG] 获取使用统计: user_id={current_user.id}")

    usage_stats = {
        "wps": current_user.wps_quota_used or 0,
        "pqr": current_user.pqr_quota_used or 0,
        "ppqr": current_user.ppqr_quota_used or 0,
        "materials": 0,  # TODO: 实现材料统计
        "welders": 0,    # TODO: 实现焊工统计
        "equipment": 0,  # TODO: 实现设备统计
        "storage": current_user.storage_quota_used or 0
    }

    print(f"[DEBUG] 返回使用统计: {usage_stats}")
    return usage_stats


# 测试端点
@router.get("/test_membership")
async def test_membership_info() -> Any:
    """测试会员信息端点."""
    return {
        "success": True,
        "message": "Test membership endpoint working"
    }


@router.get("/test_usage")
async def test_usage_stats() -> Any:
    """测试使用统计端点."""
    return {
        "success": True,
        "message": "Test usage endpoint working"
    }


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int = Path(..., ge=1, description="用户ID,必须是正整数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """获取指定用户信息."""
    print(f"[DEBUG] read_user called with user_id: {user_id}")
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
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
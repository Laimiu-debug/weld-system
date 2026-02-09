"""
Admin management endpoints for the welding system backend.
管理员专用API端点
"""
from typing import Any, Dict, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.admin_deps import get_current_active_admin
from app.models.admin import Admin
from app.core.database import get_db
from app.services.admin_user_service import admin_user_service
from app.api.v1.schemas.payment import ManualPaymentConfirmRequest

router = APIRouter()


@router.get("/users", response_model=Dict[str, Any])
async def get_users_admin(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    membership_tier: Optional[str] = Query(None, description="会员等级筛选"),
    is_active: Optional[bool] = Query(None, description="用户状态筛选"),
    membership_type: Optional[str] = Query(None, description="会员类型筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    sort_field: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取所有用户列表（管理员专用）
    支持分页、搜索、筛选
    """
    try:
        result = admin_user_service.get_users_with_filters(
            db=db,
            page=page,
            page_size=page_size,
            search=search,
            membership_tier=membership_tier,
            is_active=is_active,
            membership_type=membership_type,
            start_date=start_date,
            end_date=end_date,
            sort_field=sort_field,
            sort_order=sort_order
        )

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user_detail_admin(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取指定用户详细信息（管理员专用）
    """
    try:
        user = admin_user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        user_data = admin_user_service.get_user_detail_data(db, user)

        return {
            "success": True,
            "data": user_data
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户详情失败: {str(e)}"
        )


@router.post("/users/{user_id}/adjust-membership")
async def adjust_user_membership_admin(
    user_id: str,
    adjustment_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    调整用户会员等级（管理员专用）
    """
    try:
        user = admin_user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 防止管理员操作自己
        if user.id == current_admin.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能调整自己的会员等级"
            )

        result = admin_user_service.adjust_user_membership(
            db=db,
            user=user,
            membership_tier=adjustment_data.get("membership_tier"),
            expires_at=adjustment_data.get("expires_at"),
            quotas=adjustment_data.get("quotas"),
            reason=adjustment_data.get("reason", ""),
            current_admin=current_admin
        )

        return {
            "success": True,
            "message": f"用户 {result['user_email']} 会员等级已从 {result['old_tier']} 调整为 {result['new_tier']}",
            "data": result
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"调整用户会员等级失败: {str(e)}"
        )


@router.post("/users/{user_id}/update-profile")
async def update_user_profile_admin(
    user_id: str,
    profile_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    更新用户基本信息（管理员专用）
    可更新: email, phone, company, full_name
    """
    try:
        user = admin_user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 更新用户基本信息
        if "email" in profile_data and profile_data["email"]:
            # 检查邮箱是否已被其他用户使用
            from app.models.user import User
            existing_user = db.query(User).filter(
                User.email == profile_data["email"],
                User.id != user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被其他用户使用"
                )
            user.email = profile_data["email"]

        if "phone" in profile_data:
            user.phone = profile_data["phone"]

        if "company" in profile_data:
            user.company = profile_data["company"]

        if "full_name" in profile_data:
            user.full_name = profile_data["full_name"]

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "message": "用户信息更新成功",
            "data": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "company": user.company,
                "full_name": user.full_name
            }
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户信息失败: {str(e)}"
        )


@router.post("/users/{user_id}/enable")
async def enable_user_admin(
    user_id: str,
    enable_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    启用用户（管理员专用）
    """
    try:
        user = admin_user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        result = admin_user_service.toggle_user_status(
            db=db,
            user=user,
            is_active=True,
            reason=enable_data.get("reason", "") if enable_data else "",
            current_admin=current_admin
        )

        return {
            "success": True,
            "message": f"用户 {result['user_email']} 已启用",
            "data": result
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启用用户失败: {str(e)}"
        )


@router.post("/users/{user_id}/disable")
async def disable_user_admin(
    user_id: str,
    disable_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    禁用用户（管理员专用）
    """
    try:
        user = admin_user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 防止管理员禁用自己
        if user.id == current_admin.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能禁用自己的账户"
            )

        result = admin_user_service.toggle_user_status(
            db=db,
            user=user,
            is_active=False,
            reason=disable_data.get("reason", ""),
            current_admin=current_admin
        )

        return {
            "success": True,
            "message": f"用户 {result['user_email']} 已禁用",
            "data": result
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"禁用用户失败: {str(e)}"
        )


@router.post("/users/{user_id}/verify-email")
async def verify_user_email_admin(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    验证用户邮箱（管理员专用）
    """
    try:
        user = admin_user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 设置邮箱为已验证
        user.is_verified = True
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "message": f"用户 {user.email} 的邮箱已验证",
            "data": {
                "user_id": str(user.id),
                "email": user.email,
                "is_verified": user.is_verified
            }
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证邮箱失败: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    删除用户（管理员专用）
    """
    try:
        user = admin_user_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 防止删除管理员自己
        if user.id == current_admin.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账号"
            )

        result = admin_user_service.delete_user(
            db=db,
            user=user,
            current_admin=current_admin
        )

        return {
            "success": True,
            "message": f"用户 {result['deleted_user']['email']} 已删除",
            "data": result
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )


@router.get("/statistics/users")
async def get_user_statistics_admin(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取用户统计数据（管理员专用）
    """
    try:
        stats = admin_user_service.get_user_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计数据失败: {str(e)}"
        )


@router.get("/test-enterprise")
async def test_enterprise_endpoint(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """Test endpoint to verify router is working"""
    return {"success": True, "message": "Enterprise router is working"}


@router.get("/enterprises")
async def get_enterprises_admin(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取企业用户列表（管理员专用）
    包括企业会员及其邀请的所有用户
    """
    try:
        result = admin_user_service.get_enterprise_users(
            db=db,
            page=page,
            page_size=page_size,
            search=search
        )

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取企业用户列表失败: {str(e)}"
        )


@router.get("/subscriptions")
async def get_subscriptions_admin(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取订阅管理用户列表（管理员专用）
    只显示非免费版和非企业版会员
    """
    try:
        result = admin_user_service.get_subscription_users(
            db=db,
            page=page,
            page_size=page_size,
            search=search
        )

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订阅用户列表失败: {str(e)}"
        )


@router.get("/statistics/subscriptions")
async def get_subscription_statistics_admin(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取订阅统计数据（管理员专用）
    """
    try:
        stats = admin_user_service.get_subscription_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订阅统计数据失败: {str(e)}"
        )


@router.get("/system/status")
async def get_system_status_admin(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取系统状态（管理员专用）
    """
    try:
        import psutil
        import os

        # 获取系统状态信息
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        # 获取活跃用户数（简化版本）
        active_users = 0  # 这里可以添加实际的逻辑来统计活跃用户

        system_status = {
            "status": "healthy" if cpu_usage < 80 and memory_usage < 80 else "warning",
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "active_users": active_users,
            "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
            "uptime": "N/A"  # 可以添加实际的系统运行时间
        }

        return {
            "success": True,
            "data": system_status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统状态失败: {str(e)}"
        )


@router.get("/logs/errors")
async def get_error_logs_admin(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取错误日志（管理员专用）
    """
    try:
        # 模拟错误日志数据（实际应用中应该从日志文件或数据库中读取）
        mock_error_logs = {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }

        return {
            "success": True,
            "data": mock_error_logs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取错误日志失败: {str(e)}"
        )


# ==================== 支付管理端点 ====================

@router.get("/payments/pending", response_model=Dict[str, Any])
async def get_pending_payments_admin(
    status_filter: str = Query('pending_confirm', description="状态筛选"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """获取待确认支付列表（管理员专用）"""
    from app.models.subscription import SubscriptionTransaction, Subscription, SubscriptionPlan
    from app.models.user import User

    # 查询订单
    query = db.query(SubscriptionTransaction).join(
        Subscription, SubscriptionTransaction.subscription_id == Subscription.id
    ).join(
        User, Subscription.user_id == User.id
    ).join(
        SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id
    )

    if status_filter != 'all':
        query = query.filter(SubscriptionTransaction.status == status_filter)

    transactions = query.order_by(
        SubscriptionTransaction.created_at.desc()
    ).all()

    result = []
    for t in transactions:
        subscription = t.subscription
        user = subscription.user
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == subscription.plan_id
        ).first()

        # 从 description 中提取用户提交的交易号
        user_transaction_id = ""
        if t.description and "用户提交交易号:" in t.description:
            user_transaction_id = t.description.split("用户提交交易号:")[1].strip()

        result.append({
            "order_id": t.transaction_id,
            "user_id": user.id,
            "user_name": user.username,
            "user_email": user.email,
            "plan_id": subscription.plan_id,
            "plan_name": plan.name if plan else subscription.plan_id,
            "amount": float(t.amount),
            "payment_method": t.payment_method,
            "transaction_id": user_transaction_id,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        })

    return {
        "success": True,
        "data": result
    }


@router.post("/payments/confirm", response_model=Dict[str, Any])
async def confirm_manual_payment_admin(
    request: ManualPaymentConfirmRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """管理员确认手动支付"""
    from app.models.subscription import SubscriptionTransaction, Subscription, SubscriptionPlan
    from app.models.user import User
    from dateutil.relativedelta import relativedelta

    # 查找订单
    transaction = db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.transaction_id == request.order_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    if transaction.status != 'pending_confirm':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单状态不正确，当前状态: {transaction.status}"
        )

    # 更新订单状态
    transaction.status = 'success'
    transaction.transaction_date = datetime.utcnow()
    transaction.updated_at = datetime.utcnow()

    # 激活订阅
    subscription = db.query(Subscription).filter(
        Subscription.id == transaction.subscription_id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )

    # 获取套餐信息
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == subscription.plan_id
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )

    # 计算订阅时间
    now = datetime.utcnow()

    # 获取用户当前信息
    user = db.query(User).filter(User.id == subscription.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 计算订阅结束时间
    # 订阅开始时间总是从现在开始
    start_date = now

    # 根据计费周期计算结束时间
    if subscription.billing_cycle == 'monthly':
        end_date = start_date + relativedelta(months=1)
    elif subscription.billing_cycle == 'quarterly':
        end_date = start_date + relativedelta(months=3)
    elif subscription.billing_cycle == 'yearly':
        end_date = start_date + relativedelta(years=1)
    else:
        end_date = start_date + relativedelta(months=1)

    # 更新订阅信息
    subscription.status = 'active'
    subscription.start_date = start_date
    subscription.end_date = end_date
    subscription.last_payment_date = now
    subscription.updated_at = now

    # 先提交订阅状态更新
    db.commit()

    # 使用会员等级计算服务更新用户会员信息
    # 这样可以正确处理多订单场景（自动选择最高等级）
    from app.services.membership_tier_service import MembershipTierService
    tier_service = MembershipTierService(db)
    tier_result = tier_service.update_user_tier(user.id)

    print(f"[管理员确认支付] 用户 {user.id} 会员等级更新: {tier_result['old_tier']} -> {tier_result['new_tier']}")

    # TODO: 发送邮件通知用户

    return {
        "success": True,
        "message": "支付已确认，会员已开通",
        "data": {
            "user_id": user.id if user else None,
            "member_tier": tier_result['new_tier'],
            "old_tier": tier_result['old_tier'],
            "subscription_end_date": end_date.isoformat(),
            "has_next_subscription": tier_result['next_subscription'] is not None
        }
    }


@router.post("/payments/reject", response_model=Dict[str, Any])
async def reject_manual_payment_admin(
    request: ManualPaymentConfirmRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """管理员拒绝手动支付"""
    from app.models.subscription import SubscriptionTransaction

    # 查找订单
    transaction = db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.transaction_id == request.order_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 更新订单状态
    transaction.status = 'rejected'
    transaction.updated_at = datetime.utcnow()

    db.commit()

    # TODO: 发送邮件通知用户

    return {
        "success": True,
        "message": "支付已拒绝"
    }

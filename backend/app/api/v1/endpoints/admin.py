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
from app.schemas.api import success_payload

router = APIRouter()


@router.get("/users", response_model=Dict[str, Any])
def get_users_admin(
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

        return success_payload(result)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )


@router.get("/admins")
def list_admins(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """获取管理端账号列表（不含密码）。"""
    result = admin_user_service.list_admins(db)
    return success_payload(result)


@router.get("/users/{user_id}", response_model=Dict[str, Any])
def get_user_detail_admin(
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

        return success_payload(user_data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID格式"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户详情失败"
        )


@router.post("/users/{user_id}/adjust-membership")
def adjust_user_membership_admin(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="调整用户会员等级失败"
        )


@router.post("/users/{user_id}/update-profile")
def update_user_profile_admin(
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
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )


@router.post("/users/{user_id}/enable")
def enable_user_admin(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启用用户失败"
        )


@router.post("/users/{user_id}/disable")
def disable_user_admin(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="禁用用户失败"
        )


@router.post("/users/{user_id}/verify-email")
def verify_user_email_admin(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证邮箱失败"
        )


@router.delete("/users/{user_id}")
def delete_user_admin(
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
    except ValueError as e:
        msg = str(e) if str(e) else "无效的用户ID格式"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )


@router.get("/statistics/users")
def get_user_statistics_admin(
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

        return success_payload(stats)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户统计数据失败"
        )


@router.get("/test-enterprise")
def test_enterprise_endpoint(
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """Test endpoint to verify router is working"""
    return {"success": True, "message": "Enterprise router is working"}


@router.get("/enterprises")
def get_enterprises_admin(
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

        return success_payload(result)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取企业用户列表失败"
        )


@router.get("/enterprises/{company_id}")
def get_enterprise_detail_admin(
    company_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin),
) -> Any:
    """按 ID 获取企业详情（管理员专用）"""
    try:
        result = admin_user_service.get_enterprise_by_id(db, company_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="企业不存在",
            )
        return success_payload(result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e) or "无效的企业ID",
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取企业详情失败",
        )


@router.get("/subscriptions")
def get_subscriptions_admin(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    membership_type: Optional[str] = Query(None, description="会员类型: personal/enterprise"),
    membership_tier: Optional[str] = Query(None, description="会员等级筛选"),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取订阅管理用户列表（管理员专用）
    显示所有非免费付费用户（含个人与企业高等级）
    """
    try:
        result = admin_user_service.get_subscription_users(
            db=db,
            page=page,
            page_size=page_size,
            search=search,
            membership_type=membership_type,
            membership_tier=membership_tier,
        )

        return success_payload(result)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订阅用户列表失败"
        )


@router.get("/statistics/subscriptions")
def get_subscription_statistics_admin(
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

        return success_payload(stats)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订阅统计数据失败"
        )


@router.get("/system/status")
def get_system_status_admin(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取系统状态（管理员专用）— 使用 SystemService 真实数据
    """
    try:
        from app.services.system_service import SystemService

        system_service = SystemService(db)
        return success_payload(system_service.get_system_status())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统状态失败"
        )


@router.get("/logs/errors")
def get_error_logs_admin(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    level: Optional[str] = Query(None, description="日志级别筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取错误日志（管理员专用）— 读取 system_logs 表
    """
    try:
        from app.services.system_service import SystemService

        system_service = SystemService(db)
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        logs = system_service.get_error_logs(
            page=page,
            page_size=page_size,
            level=level,
            start_date=start_datetime,
            end_date=end_datetime,
        )
        return success_payload(logs)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取错误日志失败"
        )


# ==================== 支付管理端点 ====================

def _payment_stats(db: Session) -> Dict[str, Any]:
    """全量订单统计（不受列表筛选影响）"""
    from app.models.subscription import SubscriptionTransaction
    from sqlalchemy import func

    rows = db.query(
        SubscriptionTransaction.status,
        func.count(SubscriptionTransaction.id),
        func.coalesce(func.sum(SubscriptionTransaction.amount), 0),
    ).group_by(SubscriptionTransaction.status).all()

    by_status = {status: {"count": count, "amount": float(amount or 0)} for status, count, amount in rows}
    pending = by_status.get("pending_confirm", {"count": 0, "amount": 0.0})
    confirmed = by_status.get("success", {"count": 0, "amount": 0.0})
    rejected = by_status.get("rejected", {"count": 0, "amount": 0.0})

    return {
        "total_pending": pending["count"],
        "total_confirmed": confirmed["count"],
        "total_rejected": rejected["count"],
        "total_amount_pending": pending["amount"],
        "total_amount_confirmed": confirmed["amount"],
    }


def _billing_delta(billing_cycle: Optional[str]):
    from dateutil.relativedelta import relativedelta

    if billing_cycle == "quarterly":
        return relativedelta(months=3)
    if billing_cycle == "yearly":
        return relativedelta(years=1)
    return relativedelta(months=1)


def _extract_user_transaction_id(description: Optional[str]) -> str:
    if description and "用户提交交易号:" in description:
        return description.split("用户提交交易号:")[1].strip()
    return ""


@router.get("/payments/pending", response_model=Dict[str, Any])
def get_pending_payments_admin(
    status_filter: str = Query('pending_confirm', description="状态筛选"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """获取支付订单列表（管理员专用）"""
    from app.models.subscription import SubscriptionTransaction, Subscription, SubscriptionPlan
    from app.models.user import User
    from sqlalchemy.orm import aliased

    plan_alias = aliased(SubscriptionPlan)

    query = (
        db.query(SubscriptionTransaction, Subscription, User, plan_alias)
        .join(Subscription, SubscriptionTransaction.subscription_id == Subscription.id)
        .join(User, Subscription.user_id == User.id)
        .outerjoin(plan_alias, Subscription.plan_id == plan_alias.id)
    )

    if status_filter != 'all':
        query = query.filter(SubscriptionTransaction.status == status_filter)

    rows = query.order_by(SubscriptionTransaction.created_at.desc()).all()

    result = []
    for t, subscription, user, plan in rows:
        result.append({
            "order_id": t.transaction_id,
            "user_id": user.id,
            "user_name": user.username or user.full_name or user.email,
            "user_email": user.email,
            "plan_id": subscription.plan_id,
            "plan_name": plan.name if plan else subscription.plan_id,
            "amount": float(t.amount or 0),
            "currency": t.currency or "CNY",
            "payment_method": t.payment_method,
            "transaction_id": _extract_user_transaction_id(t.description),
            "description": t.description,
            "status": t.status,
            "billing_cycle": subscription.billing_cycle,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            "transaction_date": t.transaction_date.isoformat() if t.transaction_date else None,
        })

    return success_payload({
        "items": result,
        "stats": _payment_stats(db),
        "total": len(result),
    })


@router.post("/payments/confirm", response_model=Dict[str, Any])
def confirm_manual_payment_admin(
    request: ManualPaymentConfirmRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """管理员确认手动支付（剩余时长可叠加）"""
    from app.models.subscription import SubscriptionTransaction, Subscription, SubscriptionPlan
    from app.models.user import User

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

    transaction.status = 'success'
    transaction.transaction_date = datetime.utcnow()
    transaction.updated_at = datetime.utcnow()

    subscription = db.query(Subscription).filter(
        Subscription.id == transaction.subscription_id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )

    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == subscription.plan_id
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )

    now = datetime.utcnow()
    user = db.query(User).filter(User.id == subscription.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 续费叠加：从「现在」与「当前有效到期」中取较晚者再加一个计费周期
    period_base = now
    if subscription.end_date and subscription.end_date > now:
        period_base = subscription.end_date
    else:
        other_active = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == user.id,
                Subscription.id != subscription.id,
                Subscription.plan_id == subscription.plan_id,
                Subscription.status == "active",
                Subscription.end_date > now,
            )
            .order_by(Subscription.end_date.desc())
            .first()
        )
        if other_active and other_active.end_date:
            period_base = other_active.end_date

    end_date = period_base + _billing_delta(subscription.billing_cycle)
    start_date = (
        subscription.start_date
        if subscription.start_date and subscription.status == "active"
        else now
    )

    subscription.status = 'active'
    subscription.start_date = start_date
    subscription.end_date = end_date
    subscription.last_payment_date = now
    subscription.updated_at = now

    db.commit()

    from app.services.membership_tier_service import MembershipTierService
    tier_service = MembershipTierService(db)
    tier_result = tier_service.update_user_tier(user.id)

    return {
        "success": True,
        "message": "支付已确认，会员已开通",
        "data": {
            "user_id": user.id if user else None,
            "member_tier": tier_result['new_tier'],
            "old_tier": tier_result['old_tier'],
            "subscription_end_date": end_date.isoformat(),
            "period_base": period_base.isoformat(),
            "has_next_subscription": tier_result['next_subscription'] is not None
        }
    }


@router.post("/payments/reject", response_model=Dict[str, Any])
def reject_manual_payment_admin(
    request: ManualPaymentConfirmRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """管理员拒绝手动支付（仅待确认）"""
    from app.models.subscription import SubscriptionTransaction, Subscription

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
            detail=f"仅可拒绝待确认订单，当前状态: {transaction.status}"
        )

    transaction.status = 'rejected'
    transaction.updated_at = datetime.utcnow()

    subscription = db.query(Subscription).filter(
        Subscription.id == transaction.subscription_id
    ).first()
    if subscription and subscription.status in ("pending", "pending_confirm"):
        subscription.status = "cancelled"
        subscription.updated_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": "支付已拒绝",
        "data": {"order_id": request.order_id},
    }

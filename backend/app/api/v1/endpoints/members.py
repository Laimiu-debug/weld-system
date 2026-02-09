"""
Member management endpoints for the welding system backend.
"""
from typing import Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.schemas.membership import (
    Subscription as SubscriptionSchema,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionPlan as SubscriptionPlanSchema,
    SubscriptionTransaction as TransactionSchema,
    MembershipUpgradeRequest,
    MembershipUpgradeResponse
)
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionTransaction
from app.core.database import get_db

router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanSchema])
async def get_subscription_plans(
    db: Session = Depends(get_db)
) -> Any:
    """获取所有可用的订阅计划 (公开接口,无需认证)."""
    import json

    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.sort_order).all()

    # 转换为JSON响应格式，确保features是数组
    result = []
    for plan in plans:
        plan_dict = {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "monthly_price": float(plan.monthly_price),
            "quarterly_price": float(plan.quarterly_price),
            "yearly_price": float(plan.yearly_price),
            "currency": plan.currency,
            "max_wps_files": plan.max_wps_files,
            "max_pqr_files": plan.max_pqr_files,
            "max_ppqr_files": plan.max_ppqr_files,
            "max_materials": plan.max_materials,
            "max_welders": plan.max_welders,
            "max_equipment": plan.max_equipment,
            "max_factories": plan.max_factories,
            "max_employees": plan.max_employees,
            "features": json.loads(plan.features) if isinstance(plan.features, str) else plan.features,
            "sort_order": plan.sort_order,
            "is_active": plan.is_active,
            "is_recommended": plan.is_recommended,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        }
        result.append(plan_dict)

    return result


@router.get("/current", response_model=Optional[SubscriptionSchema])
async def get_current_subscription(
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """获取当前用户的订阅信息."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active",
        Subscription.end_date > datetime.utcnow()
    ).first()

    if not subscription:
        return None

    return subscription


@router.post("/upgrade", response_model=MembershipUpgradeResponse)
async def upgrade_membership(
    upgrade_data: MembershipUpgradeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """升级会员等级."""
    from app.services.payment_service import PaymentService

    payment_service = PaymentService(db)

    try:
        # 创建支付订单
        order_data = payment_service.create_payment_order(
            user_id=current_user.id,
            plan_id=upgrade_data.plan_id,
            billing_cycle=upgrade_data.billing_cycle,
            payment_method=upgrade_data.payment_method
        )
        
        # 处理支付
        payment_response = payment_service.process_payment(
            order_id=order_data["order_id"],
            payment_method=upgrade_data.payment_method
        )
        
        # 获取订阅计划信息
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == upgrade_data.plan_id).first()
        
        return MembershipUpgradeResponse(
            success=True,
            subscription_id=order_data["subscription_id"],
            message="支付订单创建成功，请完成支付",
            new_plan=plan.name,
            next_billing_date=order_data["end_date"],
            amount_paid=order_data["amount"],
            payment_url=payment_response.payment_url,
            qr_code=payment_response.qr_code
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"升级会员失败: {str(e)}"
        )


@router.get("/history")
async def get_subscription_history(
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """获取用户订阅历史."""
    from app.models.subscription import SubscriptionTransaction

    try:
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).order_by(Subscription.created_at.desc()).all()

        # 转换为API响应格式
        history_items = []
        for subscription in subscriptions:
            # 获取该订阅的所有交易记录
            transactions = db.query(SubscriptionTransaction).filter(
                SubscriptionTransaction.subscription_id == subscription.id
            ).order_by(SubscriptionTransaction.created_at.desc()).all()

            # 格式化交易记录
            transaction_list = []
            for tx in transactions:
                transaction_list.append({
                    "id": tx.id,
                    "transaction_id": tx.transaction_id,
                    "amount": float(tx.amount) if tx.amount else 0,
                    "currency": tx.currency or "CNY",
                    "payment_method": tx.payment_method,
                    "status": tx.status,
                    "transaction_date": tx.transaction_date.isoformat() if tx.transaction_date else None,
                    "description": tx.description,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                })

            history_items.append({
                "id": subscription.id,
                "plan_id": subscription.plan_id,
                "status": subscription.status,
                "billing_cycle": subscription.billing_cycle,
                "price": float(subscription.price) if subscription.price else 0,
                "currency": subscription.currency or "CNY",
                "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
                "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
                "trial_end_date": subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
                "auto_renew": subscription.auto_renew,
                "payment_method": subscription.payment_method,
                "last_payment_date": subscription.last_payment_date.isoformat() if subscription.last_payment_date else None,
                "next_billing_date": subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
                "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
                "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
                "transactions": transaction_list,  # 添加交易记录列表
            })

        return {
            "success": True,
            "data": history_items,
            "message": "获取订阅历史成功"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"获取订阅历史失败: {str(e)}"
        }


@router.post("/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """取消订阅."""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )

    if subscription.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能取消活跃的订阅"
        )

    subscription.status = "cancelled"
    subscription.auto_renew = False

    db.commit()

    return {"message": "订阅已取消"}


@router.post("/{subscription_id}/renew")
async def renew_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """续费订阅."""
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )

    # 获取订阅计划
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅计划不存在"
        )

    # 计算新价格和期限
    if subscription.billing_cycle == "monthly":
        price = plan.monthly_price
        duration_months = 1
    elif subscription.billing_cycle == "quarterly":
        price = plan.quarterly_price
        duration_months = 3
    else:  # yearly
        price = plan.yearly_price
        duration_months = 12

    # 延长订阅期限
    old_end_date = subscription.end_date
    if old_end_date < datetime.utcnow():
        new_end_date = datetime.utcnow() + timedelta(days=duration_months * 30)
    else:
        new_end_date = old_end_date + timedelta(days=duration_months * 30)

    subscription.end_date = new_end_date
    subscription.next_billing_date = new_end_date - timedelta(days=7)

    # 创建交易记录
    import uuid
    transaction = SubscriptionTransaction(
        subscription_id=subscription.id,
        transaction_id=f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}",
        amount=price,
        currency="CNY",
        payment_method=subscription.payment_method,
        status="pending",
        description=f"续费 {plan.name} - {subscription.billing_cycle}"
    )

    db.add(transaction)
    db.commit()

    # 模拟支付处理
    transaction.status = "success"
    transaction.transaction_date = datetime.utcnow()
    subscription.last_payment_date = datetime.utcnow()

    db.commit()

    return {
        "message": "续费成功",
        "new_end_date": new_end_date,
        "amount_paid": price
    }


@router.get("/subscription-summary")
async def get_subscription_summary(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户订阅摘要信息

    包括：
    - 当前会员等级
    - 当前生效的订阅
    - 次高等级订阅（如果存在）
    - 所有有效订阅列表
    """
    from app.services.membership_tier_service import MembershipTierService

    tier_service = MembershipTierService(db)
    summary = tier_service.get_user_subscription_summary(current_user.id)

    return {
        "success": True,
        "data": summary
    }


@router.get("/subscription-history")
async def get_subscription_history(
    include_expired: bool = True,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户的所有订阅历史

    参数：
    - include_expired: 是否包含已过期的订阅（默认为True）

    返回所有订阅记录，按创建时间降序排列
    """
    from app.services.membership_tier_service import MembershipTierService

    tier_service = MembershipTierService(db)
    subscriptions = tier_service.get_all_subscriptions_for_user(
        current_user.id,
        include_expired=include_expired
    )

    return {
        "success": True,
        "data": subscriptions,
        "total": len(subscriptions)
    }


@router.post("/refresh-tier")
async def refresh_membership_tier(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    手动刷新用户的会员等级

    根据所有有效订阅重新计算并更新用户的会员等级
    这个接口可以用于：
    - 用户怀疑会员等级不正确时手动刷新
    - 管理员操作后的同步
    """
    from app.services.membership_tier_service import MembershipTierService

    tier_service = MembershipTierService(db)
    result = tier_service.update_user_tier(current_user.id)

    return {
        "success": True,
        "message": "会员等级已刷新",
        "data": {
            "old_tier": result['old_tier'],
            "new_tier": result['new_tier'],
            "changed": result['changed'],
            "current_subscription": result['current_subscription'].plan_id if result['current_subscription'] else None,
            "next_subscription": result['next_subscription'].plan_id if result['next_subscription'] else None
        }
    }
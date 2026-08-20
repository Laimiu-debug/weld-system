"""
Membership management endpoints for the welding system backend.
会员管理API端点
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.admin_deps import get_current_active_admin
from app.models.admin import Admin
from app.models.user import User
from app.models.subscription import SubscriptionPlan, SubscriptionTransaction
from app.services.membership_service import MembershipService
from app.services.system_service import SystemService
from app.services.subscription_plan_seed import parse_plan_features
from app.core.database import get_db

router = APIRouter()


@router.get("/subscription-plans")
def get_subscription_plans_admin(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取订阅计划列表（管理员专用）
    返回所有计划，包括已停用的
    """
    # 获取所有订阅计划（包括停用的）
    plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.sort_order).all()

    result = []
    for plan in plans:
        result.append({
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "monthly_price": plan.monthly_price,
            "quarterly_price": plan.quarterly_price,
            "yearly_price": plan.yearly_price,
            "currency": plan.currency,
            "max_wps_files": plan.max_wps_files,
            "max_pqr_files": plan.max_pqr_files,
            "max_ppqr_files": plan.max_ppqr_files,
            "max_materials": plan.max_materials,
            "max_welders": plan.max_welders,
            "max_equipment": plan.max_equipment,
            "max_factories": plan.max_factories,
            "max_employees": plan.max_employees,
            "features": parse_plan_features(plan.features),
            "sort_order": plan.sort_order,
            "is_recommended": plan.is_recommended,
            "is_active": plan.is_active,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        })

    return {
        "success": True,
        "data": result
    }


@router.post("/subscription-plans")
def create_subscription_plan_admin(
    plan_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    创建订阅计划（管理员专用，需要超级管理员权限）
    """
    if current_admin.admin_level != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )

    plan = SubscriptionPlan(
        id=plan_data.get("id"),
        name=plan_data.get("name"),
        description=plan_data.get("description"),
        monthly_price=plan_data.get("monthly_price", 0),
        quarterly_price=plan_data.get("quarterly_price", 0),
        yearly_price=plan_data.get("yearly_price", 0),
        currency=plan_data.get("currency", "CNY"),
        max_wps_files=plan_data.get("max_wps_files", 0),
        max_pqr_files=plan_data.get("max_pqr_files", 0),
        max_ppqr_files=plan_data.get("max_ppqr_files", 0),
        max_materials=plan_data.get("max_materials", 0),
        max_welders=plan_data.get("max_welders", 0),
        max_equipment=plan_data.get("max_equipment", 0),
        max_factories=plan_data.get("max_factories", 0),
        max_employees=plan_data.get("max_employees", 0),
        features=",".join(plan_data.get("features", [])),
        sort_order=plan_data.get("sort_order", 0),
        is_recommended=plan_data.get("is_recommended", False)
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    # 记录操作日志
    system_service = SystemService(db)
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {current_admin.email} 创建了订阅计划: {plan.name}",
        user_id=current_admin.user_id if current_admin.user_id else None,
        details={"plan_id": plan.id}
    )

    return {
        "success": True,
        "message": "订阅计划创建成功",
        "data": {
            "id": plan.id,
            "name": plan.name
        }
    }


@router.put("/subscription-plans/{plan_id}")
def update_subscription_plan_admin(
    plan_id: str,
    plan_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    更新订阅计划（管理员专用，需要超级管理员权限）
    """
    if current_admin.admin_level != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅计划不存在"
        )

    # 更新字段
    if "name" in plan_data:
        plan.name = plan_data["name"]
    if "description" in plan_data:
        plan.description = plan_data["description"]
    if "monthly_price" in plan_data:
        plan.monthly_price = plan_data["monthly_price"]
    if "quarterly_price" in plan_data:
        plan.quarterly_price = plan_data["quarterly_price"]
    if "yearly_price" in plan_data:
        plan.yearly_price = plan_data["yearly_price"]
    if "max_wps_files" in plan_data:
        plan.max_wps_files = plan_data["max_wps_files"]
    if "max_pqr_files" in plan_data:
        plan.max_pqr_files = plan_data["max_pqr_files"]
    if "max_ppqr_files" in plan_data:
        plan.max_ppqr_files = plan_data["max_ppqr_files"]
    if "max_materials" in plan_data:
        plan.max_materials = plan_data["max_materials"]
    if "max_welders" in plan_data:
        plan.max_welders = plan_data["max_welders"]
    if "max_equipment" in plan_data:
        plan.max_equipment = plan_data["max_equipment"]
    if "features" in plan_data:
        plan.features = ",".join(plan_data["features"])
    if "sort_order" in plan_data:
        plan.sort_order = plan_data["sort_order"]
    if "is_recommended" in plan_data:
        plan.is_recommended = plan_data["is_recommended"]
    if "is_active" in plan_data:
        plan.is_active = plan_data["is_active"]

    plan.updated_at = datetime.utcnow()
    db.commit()

    # 记录操作日志
    system_service = SystemService(db)
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {current_admin.email} 更新了订阅计划: {plan.name}",
        user_id=current_admin.user_id if current_admin.user_id else None,
        details={"plan_id": plan.id}
    )

    return {
        "success": True,
        "message": "订阅计划更新成功",
        "data": {
            "id": plan.id,
            "name": plan.name
        }
    }


@router.post("/subscription-plans/batch-discount")
def batch_set_discount_admin(
    discount_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    批量设置订阅计划折扣（管理员专用，需要超级管理员权限）

    支持两种折扣方式：
    1. 按百分比折扣：discount_percent (0-100)
    2. 按固定金额降价：discount_amount

    请求体示例：
    {
        "plan_ids": ["personal_pro", "personal_advanced"],
        "discount_type": "percent",  // "percent" 或 "amount"
        "monthly_discount": 10,      // 百分比或金额
        "quarterly_discount": 15,
        "yearly_discount": 20
    }
    """
    if current_admin.admin_level != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )

    plan_ids = discount_data.get("plan_ids", [])
    discount_type = discount_data.get("discount_type", "percent")  # "percent" 或 "amount"
    monthly_discount = discount_data.get("monthly_discount", 0)
    quarterly_discount = discount_data.get("quarterly_discount", 0)
    yearly_discount = discount_data.get("yearly_discount", 0)

    if not plan_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择至少一个订阅计划"
        )

    updated_plans = []
    for plan_id in plan_ids:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if not plan:
            continue

        # 保存原价格用于日志
        original_prices = {
            "monthly": plan.monthly_price,
            "quarterly": plan.quarterly_price,
            "yearly": plan.yearly_price
        }

        # 应用折扣
        if discount_type == "percent":
            # 按百分比折扣
            if monthly_discount > 0:
                plan.monthly_price = round(plan.monthly_price * (1 - monthly_discount / 100), 2)
            if quarterly_discount > 0:
                plan.quarterly_price = round(plan.quarterly_price * (1 - quarterly_discount / 100), 2)
            if yearly_discount > 0:
                plan.yearly_price = round(plan.yearly_price * (1 - yearly_discount / 100), 2)
        else:
            # 按固定金额降价
            if monthly_discount > 0:
                plan.monthly_price = max(0, round(plan.monthly_price - monthly_discount, 2))
            if quarterly_discount > 0:
                plan.quarterly_price = max(0, round(plan.quarterly_price - quarterly_discount, 2))
            if yearly_discount > 0:
                plan.yearly_price = max(0, round(plan.yearly_price - yearly_discount, 2))

        plan.updated_at = datetime.utcnow()
        updated_plans.append({
            "plan_id": plan.id,
            "plan_name": plan.name,
            "original_prices": original_prices,
            "new_prices": {
                "monthly": plan.monthly_price,
                "quarterly": plan.quarterly_price,
                "yearly": plan.yearly_price
            }
        })

    db.commit()

    # 记录操作日志
    system_service = SystemService(db)
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {current_admin.email} 批量调整了 {len(updated_plans)} 个订阅计划的价格",
        user_id=current_admin.user_id if current_admin.user_id else None,
        details={
            "discount_type": discount_type,
            "updated_plans": updated_plans
        }
    )

    return {
        "success": True,
        "message": f"成功调整 {len(updated_plans)} 个订阅计划的价格",
        "data": {
            "updated_count": len(updated_plans),
            "updated_plans": updated_plans
        }
    }


@router.delete("/subscription-plans/{plan_id}")
def delete_subscription_plan_admin(
    plan_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    删除订阅计划（管理员专用，需要超级管理员权限）
    """
    if current_admin.admin_level != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅计划不存在"
        )

    plan_name = plan.name
    db.delete(plan)
    db.commit()

    # 记录操作日志
    system_service = SystemService(db)
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {current_admin.email} 删除了订阅计划: {plan_name}",
        user_id=current_admin.user_id if current_admin.user_id else None,
        details={"plan_id": plan_id}
    )

    return {
        "success": True,
        "message": f"订阅计划 '{plan_name}' 已删除",
        "data": {
            "deleted_plan_id": plan_id
        }
    }


@router.get("/subscriptions")
def get_subscriptions_admin(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="订阅状态筛选"),
    plan_id: Optional[str] = Query(None, description="计划ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取订阅列表（管理员专用）
    """
    from app.models.subscription import Subscription

    query = db.query(Subscription).join(User, Subscription.user_id == User.id)

    # 应用筛选
    if status:
        query = query.filter(Subscription.status == status)
    if plan_id:
        query = query.filter(Subscription.plan_id == plan_id)
    if start_date:
        query = query.filter(Subscription.start_date >= start_date)
    if end_date:
        query = query.filter(Subscription.end_date <= end_date)

    # 总数统计
    total = query.count()

    # 分页查询
    offset = (page - 1) * page_size
    subscriptions = query.order_by(Subscription.created_at.desc()).offset(offset).limit(page_size).all()

    # 转换为响应格式
    subscription_items = []
    for subscription in subscriptions:
        subscription_items.append({
            "id": subscription.id,
            "user_id": subscription.user_id,
            "user_email": subscription.user.email,
            "plan_id": subscription.plan_id,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "price": subscription.price,
            "currency": subscription.currency,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
            "auto_renew": subscription.auto_renew,
            "payment_method": subscription.payment_method,
            "last_payment_date": subscription.last_payment_date.isoformat() if subscription.last_payment_date else None,
            "next_billing_date": subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
        })

    return {
        "success": True,
        "data": {
            "items": subscription_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.get("/subscriptions/{subscription_id}")
def get_subscription_detail_admin(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取订阅详情（管理员专用）
    """
    from app.models.subscription import Subscription

    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )

    # 获取交易记录
    transactions = db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.subscription_id == subscription_id
    ).order_by(SubscriptionTransaction.transaction_date.desc()).all()

    transaction_items = []
    for transaction in transactions:
        transaction_items.append({
            "id": transaction.id,
            "transaction_id": transaction.transaction_id,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "payment_method": transaction.payment_method,
            "status": transaction.status,
            "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
            "description": transaction.description,
        })

    return {
        "success": True,
        "data": {
            "id": subscription.id,
            "user_id": subscription.user_id,
            "user_email": subscription.user.email,
            "plan_id": subscription.plan_id,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "price": subscription.price,
            "currency": subscription.currency,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
            "trial_end_date": subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            "auto_renew": subscription.auto_renew,
            "payment_method": subscription.payment_method,
            "last_payment_date": subscription.last_payment_date.isoformat() if subscription.last_payment_date else None,
            "next_billing_date": subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
            "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None,
            "transactions": transaction_items
        }
    }


@router.post("/users/{user_id}/upgrade-membership")
def upgrade_user_membership_admin(
    user_id: int,
    upgrade_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    升级用户会员等级（管理员专用）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    membership_service = MembershipService(db)
    new_tier = upgrade_data.get("membership_tier")
    reason = upgrade_data.get("reason", "")

    if not new_tier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须指定会员等级"
        )

    success = membership_service.upgrade_membership(
        user_id=user_id,
        new_tier=new_tier,
        admin_id=current_admin.user_id,
        reason=reason
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="会员等级升级失败"
        )

    # 记录操作日志
    system_service = SystemService(db)
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {current_admin.email} 将用户 {user.email} 会员等级升级为 {new_tier}",
        user_id=current_admin.user_id if current_admin.user_id else None,
        details={
            "target_user_id": user_id,
            "old_tier": user.member_tier,
            "new_tier": new_tier,
            "reason": reason
        }
    )

    return {
        "success": True,
        "message": f"用户 {user.email} 会员等级已升级为 {new_tier}",
        "data": {
            "user_id": user_id,
            "old_tier": user.member_tier,
            "new_tier": new_tier
        }
    }


@router.get("/expiring-subscriptions")
def get_expiring_subscriptions_admin(
    days_ahead: int = Query(7, ge=1, le=30, description="提前天数"),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    获取即将过期的订阅（管理员专用）
    """
    membership_service = MembershipService(db)
    expiring_subscriptions = membership_service.get_expiring_subscriptions(days_ahead)

    return {
        "success": True,
        "data": {
            "expiring_subscriptions": expiring_subscriptions,
            "days_ahead": days_ahead,
            "count": len(expiring_subscriptions)
        }
    }


@router.post("/subscriptions/{subscription_id}/process-renewal")
def process_subscription_renewal_admin(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_active_admin)
) -> Any:
    """
    手动处理订阅续费（管理员专用）
    """
    from app.models.subscription import Subscription

    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )

    membership_service = MembershipService(db)
    success = membership_service.process_subscription_renewal(subscription.user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="订阅续费处理失败"
        )

    # 记录操作日志
    system_service = SystemService(db)
    system_service.create_system_log(
        log_level="info",
        log_type="admin",
        message=f"管理员 {current_admin.email} 手动处理了用户 {subscription.user.email} 的订阅续费",
        user_id=current_admin.user_id if current_admin.user_id else None,
        details={
            "subscription_id": subscription_id,
            "user_id": subscription.user_id
        }
    )

    return {
        "success": True,
        "message": "订阅续费处理成功",
        "data": {
            "subscription_id": subscription_id,
            "user_id": subscription.user_id
        }
    }
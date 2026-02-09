"""
Payment API endpoints for the welding system backend.
"""
from typing import Any, Dict
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.api.v1.schemas.payment import (
    PaymentRequest, PaymentResponse, PaymentCallback, PaymentStatus,
    ManualPaymentRequest, ManualPaymentConfirmRequest
)
from app.services.payment_service import PaymentService
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class PaymentCreateRequest(BaseModel):
    """支付创建请求"""
    plan_id: str
    billing_cycle: str  # monthly, quarterly, yearly
    payment_method: str  # alipay, wechat, bank
    auto_renew: bool = False


class PricePreviewRequest(BaseModel):
    """价格预览请求"""
    plan_id: str
    billing_cycle: str  # monthly, quarterly, yearly


@router.post("/preview-price", response_model=Dict[str, Any])
async def preview_upgrade_price(
    request: PricePreviewRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """预览升级价格（包含补差价计算）"""
    from app.models.subscription import SubscriptionPlan
    from app.models.user import User

    payment_service = PaymentService(db)

    # 获取订阅计划
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == request.plan_id,
        SubscriptionPlan.is_active == True
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅计划不存在"
        )

    # 获取用户信息
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 计算新套餐原价
    if request.billing_cycle == "monthly":
        original_price = plan.monthly_price
        duration_months = 1
    elif request.billing_cycle == "quarterly":
        original_price = plan.quarterly_price
        duration_months = 3
    elif request.billing_cycle == "yearly":
        original_price = plan.yearly_price
        duration_months = 12
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的计费周期"
        )

    # 计算实际支付金额（考虑补差价）
    actual_price = payment_service._calculate_upgrade_price(
        user=user,
        new_plan_id=request.plan_id,
        new_plan_price=original_price,
        billing_cycle=request.billing_cycle,
        duration_months=duration_months
    )

    # 计算折扣金额
    discount = original_price - actual_price

    # 判断是否为升级
    current_tier = user.member_tier or 'free'
    is_upgrade = current_tier != request.plan_id and current_tier not in ['free', 'personal_free']

    return {
        "success": True,
        "data": {
            "plan_id": request.plan_id,
            "plan_name": plan.name,
            "billing_cycle": request.billing_cycle,
            "original_price": original_price,
            "actual_price": actual_price,
            "discount": discount,
            "is_upgrade": is_upgrade,
            "current_tier": current_tier,
            "has_active_subscription": user.subscription_end_date and user.subscription_end_date > datetime.utcnow() if user.subscription_end_date else False
        }
    }


@router.post("/create", response_model=Dict[str, Any])
async def create_payment(
    payment_data: PaymentCreateRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """创建支付订单"""
    logger.info(f"Creating payment order for user {current_user.id}, plan_id={payment_data.plan_id}, billing_cycle={payment_data.billing_cycle}, payment_method={payment_data.payment_method}")
    payment_service = PaymentService(db)

    try:
        # 创建支付订单
        order_data = payment_service.create_payment_order(
            user_id=current_user.id,
            plan_id=payment_data.plan_id,
            billing_cycle=payment_data.billing_cycle,
            payment_method=payment_data.payment_method
        )

        # 处理支付
        payment_response = payment_service.process_payment(
            order_id=order_data["transaction_id"],  # 使用 transaction_id 而不是 order_id
            payment_method=payment_data.payment_method
        )

        return {
            "success": True,
            "message": "支付订单创建成功",
            "data": {
                "order_id": order_data["order_id"],
                "subscription_id": order_data["subscription_id"],
                "transaction_id": order_data["transaction_id"],
                "amount": order_data["amount"],
                "plan_name": order_data["plan_name"],
                "billing_cycle": order_data["billing_cycle"],
                "payment_method": order_data["payment_method"],
                "payment_url": payment_response.payment_url,
                "qr_code": payment_response.qr_code,
                "start_date": order_data["start_date"],
                "end_date": order_data["end_date"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to create payment order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建支付订单失败: {str(e)}"
        )


@router.get("/status/{order_id}", response_model=Dict[str, Any])
async def get_payment_status(
    order_id: str,
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """获取支付状态"""
    payment_service = PaymentService(db)
    
    try:
        status = payment_service.get_payment_status(order_id)
        
        return {
            "success": True,
            "data": {
                "order_id": status.order_id,
                "status": status.status,
                "amount": status.amount,
                "paid_at": status.paid_at,
                "transaction_id": status.transaction_id,
                "failure_reason": status.failure_reason
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取支付状态失败: {str(e)}"
        )


@router.post("/callback/{payment_method}", response_model=Dict[str, Any])
async def payment_callback(
    payment_method: str,
    request: Request,
    db: Session = Depends(deps.get_db)
) -> Any:
    """处理支付回调"""
    payment_service = PaymentService(db)
    
    try:
        # 获取回调数据
        if payment_method == "alipay":
            # 支付宝回调数据
            callback_data = await request.form()
            callback_dict = dict(callback_data)
            
            # 构造回调对象
            callback = PaymentCallback(
                order_id=callback_dict.get("out_trade_no", ""),
                transaction_id=callback_dict.get("trade_no", ""),
                amount=float(callback_dict.get("total_amount", 0)),
                currency=callback_dict.get("currency", "CNY"),
                payment_method="alipay",
                status="success" if callback_dict.get("trade_status") == "TRADE_SUCCESS" else "failed",
                paid_at=datetime.now(),
                signature=callback_dict.get("sign", "")
            )
        elif payment_method == "wechat":
            # 微信支付回调数据
            body = await request.body()
            callback_dict = xmltodict.parse(body.decode("utf-8"))["xml"]
            
            # 构造回调对象
            callback = PaymentCallback(
                order_id=callback_dict.get("out_trade_no", ""),
                transaction_id=callback_dict.get("transaction_id", ""),
                amount=float(callback_dict.get("total_fee", 0)) / 100,
                currency="CNY",
                payment_method="wechat",
                status="success" if callback_dict.get("result_code") == "SUCCESS" else "failed",
                paid_at=datetime.now(),
                signature=callback_dict.get("sign", "")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的支付方式"
            )
        
        # 处理支付回调
        result = payment_service.handle_payment_callback(callback)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"处理支付回调失败: {str(e)}"
        )


@router.post("/refund/{transaction_id}", response_model=Dict[str, Any])
async def refund_payment(
    transaction_id: str,
    refund_amount: float = Form(...),
    reason: str = Form(...),
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """申请退款"""
    payment_service = PaymentService(db)
    
    try:
        # 验证交易所有权
        from app.models.subscription import SubscriptionTransaction
        transaction = db.query(SubscriptionTransaction).filter(
            SubscriptionTransaction.transaction_id == transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易记录不存在"
            )
        
        subscription = transaction.subscription
        if subscription.user_id != current_user.id and not getattr(current_user, "is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此交易"
            )
        
        # 处理退款
        result = payment_service.refund_payment(
            transaction_id=transaction_id,
            refund_amount=refund_amount,
            reason=reason
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"申请退款失败: {str(e)}"
        )


# 导入xmltodict用于微信支付回调解析
try:
    import xmltodict
except ImportError:
    xmltodict = None


# ==================== 手动支付相关接口 ====================

@router.post("/manual-confirm", response_model=Dict[str, Any])
async def submit_manual_payment(
    request: ManualPaymentRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """提交手动支付凭证"""
    from app.models.subscription import SubscriptionTransaction, Subscription

    # 查找订单
    transaction = db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.transaction_id == request.order_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 验证订单所有权
    subscription = db.query(Subscription).filter(
        Subscription.id == transaction.subscription_id
    ).first()

    if not subscription or subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此订单"
        )

    if transaction.status not in ['pending', 'failed']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单状态不正确，当前状态: {transaction.status}"
        )

    # 保存支付凭证
    # 注意：这里我们使用 description 字段来存储用户提交的交易号
    # 因为 transaction_id 字段已经被用作订单号
    transaction.description = f"用户提交交易号: {request.transaction_id}"
    transaction.payment_method = request.payment_method
    transaction.status = 'pending_confirm'  # 待确认
    transaction.updated_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": "支付凭证已提交，请等待管理员确认（通常1-24小时内）"
    }


@router.get("/pending", response_model=Dict[str, Any])
async def get_pending_payments(
    status_filter: str = 'pending_confirm',
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """获取待确认支付列表（管理员）"""
    from app.models.subscription import SubscriptionTransaction, Subscription, SubscriptionPlan
    from app.models.user import User

    # 验证管理员权限
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

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

    return result


@router.post("/admin/confirm-payment", response_model=Dict[str, Any])
async def confirm_manual_payment(
    request: ManualPaymentConfirmRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """管理员确认手动支付"""
    from app.models.subscription import SubscriptionTransaction, Subscription

    # 验证管理员权限
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

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

    if subscription:
        subscription.status = 'active'
        subscription.last_payment_date = datetime.utcnow()
        subscription.updated_at = datetime.utcnow()

    db.commit()

    # TODO: 发送邮件通知用户

    return {
        "success": True,
        "message": "支付已确认，会员已开通"
    }


@router.post("/admin/reject-payment", response_model=Dict[str, Any])
async def reject_manual_payment(
    request: ManualPaymentConfirmRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """管理员拒绝手动支付"""
    from app.models.subscription import SubscriptionTransaction

    # 验证管理员权限
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

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
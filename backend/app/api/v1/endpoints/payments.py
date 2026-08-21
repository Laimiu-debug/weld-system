"""
Payment API endpoints for the welding system backend.
"""
from datetime import datetime
from typing import Any, Dict, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.api.v1.schemas.payment import (
    PaymentCallback,
    ManualPaymentRequest, ManualPaymentConfirmRequest
)
from app.core.config import settings
from app.core.rate_limit import client_ip, enforce_rate_limit
from app.models.subscription import SubscriptionTransaction, Subscription, SubscriptionPlan
from app.models.user import User
from app.services.payment_service import PaymentService

try:
    import xmltodict
except ImportError:
    xmltodict = None

logger = logging.getLogger(__name__)

router = APIRouter()


class PaymentCreateRequest(BaseModel):
    """支付创建请求"""
    plan_id: str
    billing_cycle: str  # monthly, quarterly, yearly
    payment_method: str  # alipay, wechat, bank
    auto_renew: bool = False
    purpose: str = "upgrade"
    existing_subscription_id: Optional[int] = None


class PricePreviewRequest(BaseModel):
    """价格预览请求"""
    plan_id: str
    billing_cycle: str  # monthly, quarterly, yearly


@router.post("/preview-price", response_model=Dict[str, Any])
def preview_upgrade_price(
    request: PricePreviewRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """预览升级价格（包含补差价计算）"""
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
def create_payment(
    payment_data: PaymentCreateRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """创建支付订单"""
    enforce_rate_limit(f"pay-create:{client_ip(request)}", limit=10, window_seconds=60)
    enforce_rate_limit(f"pay-create-user:{current_user.id}", limit=10, window_seconds=60)
    logger.info(
        "Creating payment order for user %s, plan_id=%s, billing_cycle=%s, payment_method=%s, purpose=%s",
        current_user.id,
        payment_data.plan_id,
        payment_data.billing_cycle,
        payment_data.payment_method,
        payment_data.purpose,
    )
    payment_service = PaymentService(db)

    try:
        order_data = payment_service.create_payment_order(
            user_id=current_user.id,
            plan_id=payment_data.plan_id,
            billing_cycle=payment_data.billing_cycle,
            payment_method=payment_data.payment_method,
            auto_renew=payment_data.auto_renew,
            purpose=payment_data.purpose,
            existing_subscription_id=payment_data.existing_subscription_id,
        )

        payment_response = payment_service.process_payment(
            order_id=order_data["transaction_id"],
            payment_method=payment_data.payment_method,
            client_ip=client_ip(request),
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
                "purpose": order_data.get("purpose"),
                "payment_url": payment_response.payment_url,
                "qr_code": payment_response.qr_code,
                "start_date": order_data["start_date"],
                "end_date": order_data["end_date"],
                "auto_renew": order_data.get("auto_renew", payment_data.auto_renew),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create payment order: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建支付订单失败: {str(e)}"
        )


@router.get("/status/{order_id}", response_model=Dict[str, Any])
def get_payment_status(
    order_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """获取支付状态"""
    payment_service = PaymentService(db)
    viewer_id = None if getattr(current_user, "is_admin", False) else current_user.id
    try:
        payment_status = payment_service.get_payment_status(order_id, user_id=viewer_id)

        return {
            "success": True,
            "data": {
                "order_id": payment_status.order_id,
                "status": payment_status.status,
                "amount": payment_status.amount,
                "paid_at": payment_status.paid_at,
                "transaction_id": payment_status.transaction_id,
                "failure_reason": payment_status.failure_reason
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取支付状态失败: {str(e)}"
        )


@router.post("/mock-complete/{order_id}", response_model=Dict[str, Any])
def mock_complete_payment(
    order_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """仅开发环境且 mock 支付网关下模拟支付成功，便于本地联调。"""
    if not settings.DEVELOPMENT or getattr(settings, "PAYMENT_PROVIDER", "mock") != "mock":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="当前支付环境不支持模拟完成",
        )
    payment_service = PaymentService(db)
    transaction = payment_service._find_transaction(order_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if transaction.subscription.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此订单")
    result = payment_service.activate_paid_transaction(transaction)
    return {
        "success": True,
        "message": "模拟支付已完成",
        "data": result,
    }


@router.post("/callback/{payment_method}", response_model=Dict[str, Any])
async def payment_callback(
    payment_method: str,
    request: Request,
    db: Session = Depends(deps.get_db)
) -> Any:
    """处理支付回调。商户订单号 out_trade_no 对应我方 transaction_id。"""
    enforce_rate_limit(f"pay-callback:{client_ip(request)}", limit=60, window_seconds=60)
    payment_service = PaymentService(db)

    try:
        if payment_method == "alipay":
            callback_data = await request.form()
            callback_dict = dict(callback_data)
            callback = PaymentCallback(
                order_id=callback_dict.get("out_trade_no", ""),
                transaction_id=callback_dict.get("out_trade_no", "") or callback_dict.get("trade_no", ""),
                amount=float(callback_dict.get("total_amount", 0)),
                currency=callback_dict.get("currency", "CNY"),
                payment_method="alipay",
                status="success" if callback_dict.get("trade_status") == "TRADE_SUCCESS" else "failed",
                paid_at=datetime.now(),
                signature=callback_dict.get("sign", ""),
                extra_data=callback_dict,
            )
        elif payment_method == "wechat":
            if xmltodict is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="微信支付回调解析不可用",
                )
            body = await request.body()
            callback_dict = xmltodict.parse(body.decode("utf-8"))["xml"]
            callback = PaymentCallback(
                order_id=callback_dict.get("out_trade_no", ""),
                transaction_id=callback_dict.get("out_trade_no", "") or callback_dict.get("transaction_id", ""),
                amount=float(callback_dict.get("total_fee", 0)) / 100,
                currency="CNY",
                payment_method="wechat",
                status="success" if callback_dict.get("result_code") == "SUCCESS" else "failed",
                paid_at=datetime.now(),
                signature=callback_dict.get("sign", ""),
                extra_data=callback_dict,
            )
        elif payment_method == "mock":
            payload = await request.json()
            callback = PaymentCallback(
                order_id=payload.get("order_id") or payload.get("out_trade_no", ""),
                transaction_id=payload.get("order_id") or payload.get("transaction_id", ""),
                amount=float(payload.get("amount", 0) or 0),
                currency=payload.get("currency", "CNY"),
                payment_method="mock",
                status=payload.get("status", "success"),
                paid_at=datetime.now(),
                signature=payload.get("signature", ""),
                extra_data=payload,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的支付方式"
            )

        result = payment_service.handle_payment_callback(callback)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"处理支付回调失败: {str(e)}"
        )


@router.post("/refund/{transaction_id}", response_model=Dict[str, Any])
def refund_payment(
    transaction_id: str,
    refund_amount: float = Form(...),
    reason: str = Form(...),
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """申请退款"""
    payment_service = PaymentService(db)
    
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"申请退款失败: {str(e)}"
        )


# ==================== 手动支付相关接口 ====================

@router.post("/manual-confirm", response_model=Dict[str, Any])
def submit_manual_payment(
    request: ManualPaymentRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """提交手动支付凭证"""
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

    original_description = transaction.description or ""
    if "用户提交交易号:" in original_description:
        prefix = original_description.split("用户提交交易号:")[0].rstrip("; ").strip()
        transaction.description = f"{prefix};用户提交交易号: {request.transaction_id}".strip("; ")
    else:
        suffix = f"用户提交交易号: {request.transaction_id}"
        transaction.description = f"{original_description};{suffix}" if original_description else suffix
    transaction.payment_method = request.payment_method
    transaction.status = 'pending_confirm'  # 待确认
    transaction.updated_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": "支付凭证已提交，请等待管理员确认（通常1-24小时内）"
    }


@router.get("/pending", response_model=Dict[str, Any])
def get_pending_payments(
    status_filter: str = 'pending_confirm',
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """获取待确认支付列表（管理员）"""
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
def confirm_manual_payment(
    request: ManualPaymentConfirmRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """管理员确认手动支付"""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    payment_service = PaymentService(db)
    transaction = db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.transaction_id == request.order_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    if transaction.status not in ('pending_confirm', 'pending'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单状态不正确，当前状态: {transaction.status}"
        )

    payment_service.activate_paid_transaction(transaction)

    return {
        "success": True,
        "message": "支付已确认，会员已开通"
    }


@router.post("/admin/reject-payment", response_model=Dict[str, Any])
def reject_manual_payment(
    request: ManualPaymentConfirmRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
) -> Any:
    """管理员拒绝手动支付"""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    payment_service = PaymentService(db)
    transaction = db.query(SubscriptionTransaction).filter(
        SubscriptionTransaction.transaction_id == request.order_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    transaction.status = 'rejected'
    transaction.updated_at = datetime.utcnow()
    db.commit()

    user_id = transaction.subscription.user_id if transaction.subscription else None
    if user_id:
        payment_service._notify_user(
            user_id,
            "支付凭证未通过",
            "管理员未确认您提交的支付凭证，请核对后重新提交或联系客服。",
            "warning",
        )

    return {
        "success": True,
        "message": "支付已拒绝"
    }
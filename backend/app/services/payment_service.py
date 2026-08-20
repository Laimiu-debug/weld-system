"""
Payment service for handling payment processing.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends

from app.api.v1.schemas.payment import (
    PaymentResponse, PaymentCallback, PaymentStatus
)
from app.models.subscription import Subscription, SubscriptionTransaction, SubscriptionPlan
from app.models.user import User
from app.core.config import settings
from app.services.payment_gateway import get_payment_gateway
from app.services.membership_tier_service import MembershipTierService
from app.services.notification_service import NotificationService
from app.api import deps


class PaymentService:
    """支付服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_payment_order(
        self,
        user_id: int,
        plan_id: str,
        billing_cycle: str,
        payment_method: str,
        auto_renew: bool = False,
        purpose: str = "upgrade",
        existing_subscription_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """创建支付订单。purpose=upgrade 新建待激活订阅；purpose=renew 挂到现有订阅。"""
        plan = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active == True
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订阅计划不存在"
            )

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        if billing_cycle == "monthly":
            new_plan_price = plan.monthly_price
            duration_months = 1
        elif billing_cycle == "quarterly":
            new_plan_price = plan.quarterly_price
            duration_months = 3
        elif billing_cycle == "yearly":
            new_plan_price = plan.yearly_price
            duration_months = 12
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的计费周期"
            )

        if purpose == "renew":
            price = new_plan_price
        else:
            price = self._calculate_upgrade_price(
                user=user,
                new_plan_id=plan_id,
                new_plan_price=new_plan_price,
                billing_cycle=billing_cycle,
                duration_months=duration_months
            )

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_months * 30)
        action_label = "续费" if purpose == "renew" else "升级到"

        if purpose == "renew":
            if not existing_subscription_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="续费必须指定现有订阅",
                )
            subscription = self.db.query(Subscription).filter(
                Subscription.id == existing_subscription_id,
                Subscription.user_id == user_id,
            ).first()
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="订阅不存在",
                )
            if subscription.end_date and subscription.end_date > start_date:
                end_date = subscription.end_date + timedelta(days=duration_months * 30)
            subscription.auto_renew = auto_renew
            subscription.payment_method = payment_method
            subscription.updated_at = datetime.utcnow()
        else:
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                status="pending",
                billing_cycle=billing_cycle,
                price=price,
                currency="CNY",
                start_date=start_date,
                end_date=end_date,
                auto_renew=auto_renew,
                payment_method=payment_method
            )
            self.db.add(subscription)
            self.db.flush()

        transaction_id = f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
        transaction = SubscriptionTransaction(
            subscription_id=subscription.id,
            transaction_id=transaction_id,
            amount=price,
            currency="CNY",
            payment_method=payment_method,
            status="pending",
            description=f"{action_label} {plan.name} - {billing_cycle};purpose={purpose};duration_months={duration_months}"
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        self.db.refresh(subscription)

        return {
            "order_id": transaction.transaction_id,
            "subscription_id": subscription.id,
            "transaction_id": transaction.transaction_id,
            "amount": price,
            "plan_name": plan.name,
            "plan_id": plan.id,
            "billing_cycle": billing_cycle,
            "payment_method": payment_method,
            "purpose": purpose,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "auto_renew": auto_renew,
        }

    def process_payment(
        self,
        order_id: str,
        payment_method: str,
        client_ip: str = "127.0.0.1"
    ) -> PaymentResponse:
        """
        处理支付 - 调用真实支付网关

        Args:
            order_id: 订单ID (实际上是 transaction_id)
            payment_method: 支付方式 (alipay, wechat, bank)
            client_ip: 客户端IP
        """
        # 获取交易记录 - order_id 实际上是 transaction_id
        transaction = self.db.query(SubscriptionTransaction).filter(
            SubscriptionTransaction.transaction_id == order_id
        ).first()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )

        # 获取订阅信息
        subscription = transaction.subscription
        plan = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == subscription.plan_id
        ).first()

        if payment_method == "bank":
            return PaymentResponse(
                success=True,
                payment_url=None,
                qr_code=None,
                order_id=transaction.transaction_id,
                transaction_id=transaction.transaction_id,
                message="请按对公账户完成转账后提交凭证",
                amount=transaction.amount,
                payment_method=payment_method,
                created_at=datetime.now()
            )

        channel_map = {
            'alipay': 'alipay_qr',
            'wechat': 'wx_pub_qr',
            'bank': 'alipay_qr'
        }
        channel = channel_map.get(payment_method, 'alipay_qr')

        try:
            gateway = get_payment_gateway()
            result = gateway.create_payment({
                'order_id': transaction.transaction_id,
                'amount': transaction.amount,
                'channel': channel,
                'subject': f"{plan.name if plan else '会员'}订阅",
                'body': transaction.description or plan.name if plan else "会员订阅",
                'client_ip': client_ip
            })
        except Exception as exc:
            return PaymentResponse(
                success=True,
                payment_url=None,
                qr_code=None,
                order_id=transaction.transaction_id,
                transaction_id=transaction.transaction_id,
                message=f"在线支付暂不可用，请使用转账凭证：{exc}",
                amount=transaction.amount,
                payment_method=payment_method,
                created_at=datetime.now()
            )

        if not result.get('success'):
            return PaymentResponse(
                success=True,
                payment_url=None,
                qr_code=None,
                order_id=transaction.transaction_id,
                transaction_id=transaction.transaction_id,
                message=result.get('error') or "请改用转账凭证完成支付",
                amount=transaction.amount,
                payment_method=payment_method,
                created_at=datetime.now()
            )

        credential = result.get('credential') or {}
        qr_code_url = (
            result.get('qr_code')
            or result.get('payment_url')
            or credential.get(channel)
            or ""
        )

        return PaymentResponse(
            success=True,
            payment_url=qr_code_url,
            qr_code=qr_code_url,
            order_id=transaction.transaction_id,
            transaction_id=transaction.transaction_id,
            message="支付订单创建成功",
            amount=transaction.amount,
            payment_method=payment_method,
            created_at=datetime.now()
        )

    def handle_payment_callback(
        self,
        callback_data: PaymentCallback
    ) -> Dict[str, Any]:
        """处理支付回调。商户订单号是我们的 transaction_id。"""
        if not self._verify_payment_signature(callback_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的支付签名"
            )

        transaction = self._find_transaction(
            callback_data.order_id or callback_data.transaction_id
        )
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易记录不存在"
            )

        if transaction.status == "success":
            return {
                "success": True,
                "message": "订单已处理",
                "transaction_id": transaction.transaction_id,
                "status": transaction.status,
            }

        if callback_data.status == "success":
            self.activate_paid_transaction(transaction)
        else:
            transaction.status = "failed"
            self.db.commit()
            self._notify_user(
                transaction.subscription.user_id,
                "支付未完成",
                "会员订单支付失败或已取消，请重新发起支付。",
                "warning",
            )

        return {
            "success": True,
            "message": "支付回调处理成功",
            "transaction_id": transaction.transaction_id,
            "status": transaction.status
        }

    def get_payment_status(self, order_id: str, user_id: Optional[int] = None) -> PaymentStatus:
        """按交易号查询真实支付状态。"""
        transaction = self._find_transaction(order_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        subscription = transaction.subscription
        if user_id is not None and subscription.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此订单"
            )
        return PaymentStatus(
            order_id=transaction.transaction_id,
            status=transaction.status if transaction.status != "pending_confirm" else "pending",
            amount=float(transaction.amount or 0),
            paid_at=transaction.transaction_date if transaction.status == "success" else None,
            transaction_id=transaction.transaction_id,
            failure_reason=None if transaction.status != "failed" else (transaction.description or "支付失败"),
        )

    def _find_transaction(self, order_id: str) -> Optional[SubscriptionTransaction]:
        if not order_id:
            return None
        return self.db.query(SubscriptionTransaction).filter(
            SubscriptionTransaction.transaction_id == order_id
        ).first()

    def activate_paid_transaction(self, transaction: SubscriptionTransaction) -> Dict[str, Any]:
        """支付成功后激活订阅、刷新会员等级并通知用户。幂等。"""
        subscription = transaction.subscription
        already_active = transaction.status == "success" and subscription.status == "active"
        if already_active:
            return {
                "already_active": True,
                "tier": None,
                "transaction_id": transaction.transaction_id,
                "subscription_id": subscription.id,
            }
        transaction.status = "success"
        transaction.transaction_date = transaction.transaction_date or datetime.utcnow()
        transaction.updated_at = datetime.utcnow()

        description = transaction.description or ""
        duration_months = 1
        if "duration_months=" in description:
            try:
                duration_months = int(description.split("duration_months=")[1].split(";")[0])
            except (ValueError, IndexError):
                duration_months = 1
        is_renewal = "purpose=renew" in description or description.startswith("续费")

        if is_renewal:
            base = subscription.end_date if subscription.end_date and subscription.end_date > datetime.utcnow() else datetime.utcnow()
            subscription.end_date = base + timedelta(days=duration_months * 30)
            subscription.status = "active"
        else:
            subscription.status = "active"

        subscription.last_payment_date = datetime.utcnow()
        subscription.next_billing_date = (subscription.end_date - timedelta(days=7)) if subscription.end_date else None
        subscription.updated_at = datetime.utcnow()

        user = self.db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            user.auto_renewal = bool(subscription.auto_renew)
            user.subscription_status = "active"
            user.subscription_start_date = subscription.start_date
            user.subscription_end_date = subscription.end_date
            user.updated_at = datetime.utcnow()

        self.db.commit()

        tier_result = MembershipTierService(self.db).update_user_tier(subscription.user_id)

        if not already_active:
            plan = self.db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
            plan_name = plan.name if plan else subscription.plan_id
            self._notify_user(
                subscription.user_id,
                "会员已开通" if not is_renewal else "会员续费成功",
                f"您的{plan_name}已生效，有效期至 {subscription.end_date.strftime('%Y-%m-%d') if subscription.end_date else '-'}。",
                "success",
            )

        return {
            "already_active": already_active,
            "tier": tier_result,
            "transaction_id": transaction.transaction_id,
            "subscription_id": subscription.id,
        }

    def create_renewal_order_if_needed(
        self,
        subscription: Subscription,
        notify: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """为现有订阅创建待支付续费单；已有未完成续费单则跳过。"""
        pending = self.db.query(SubscriptionTransaction).filter(
            SubscriptionTransaction.subscription_id == subscription.id,
            SubscriptionTransaction.status.in_(["pending", "pending_confirm"]),
        ).all()
        for item in pending:
            description = item.description or ""
            if "purpose=renew" in description or description.startswith("续费"):
                return None

        order = self.create_payment_order(
            user_id=subscription.user_id,
            plan_id=subscription.plan_id,
            billing_cycle=subscription.billing_cycle or "monthly",
            payment_method=subscription.payment_method or "alipay",
            auto_renew=True,
            purpose="renew",
            existing_subscription_id=subscription.id,
        )
        if notify:
            amount = order.get("amount") or 0
            self._notify_user(
                subscription.user_id,
                "请完成会员续费",
                f"您的会员即将到期。续费订单 {order['transaction_id']} 金额 ¥{amount}，支付完成前不会延长有效期。",
                "warning",
            )
        return order

    def _notify_user(self, user_id: int, title: str, content: str, announcement_type: str = "info") -> None:
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            NotificationService(self.db).deliver_user_notification(
                user,
                title=title,
                content=content,
                category="membership",
                announcement_type=announcement_type,
                priority="normal",
                expire_days=14,
            )
        except Exception:
            pass

    def _verify_payment_signature(self, callback_data: PaymentCallback) -> bool:
        """优先走支付网关验签；mock 环境放行。"""
        provider = getattr(settings, "PAYMENT_PROVIDER", "mock")
        if provider == "mock":
            return True
        if getattr(settings, "DEVELOPMENT", False) and not callback_data.signature:
            return True
        try:
            gateway = get_payment_gateway()
            extra = callback_data.extra_data or {
                "order_id": callback_data.order_id,
                "transaction_id": callback_data.transaction_id,
                "amount": callback_data.amount,
                "status": callback_data.status,
            }
            return bool(gateway.verify_callback(extra, callback_data.signature or ""))
        except Exception:
            return False

    def _generate_payment_url(self, order_id: str, payment_method: str) -> str:
        """生成支付URL"""
        base_url = settings.API_V1_STR
        payment_url = ""

        if payment_method == "alipay":
            payment_url = f"https://openapi.alipay.com/gateway.do?order_id={order_id}"
        elif payment_method == "wechat":
            payment_url = f"https://api.mch.weixin.qq.com/pay/unifiedorder?order_id={order_id}"
        elif payment_method == "bank":
            payment_url = f"{base_url}/payment/bank?order_id={order_id}"

        return payment_url

    def _generate_payment_qr_code(self, order_id: str, payment_method: str) -> str:
        """生成支付二维码"""
        # 模拟生成二维码
        # 实际应该调用支付网关API生成二维码
        qr_data = f"payment:{payment_method}:{order_id}"
        
        # 这里应该生成实际的二维码图片，返回URL或Base64编码
        return f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    def refund_payment(self, transaction_id: str, refund_amount: float, reason: str) -> Dict[str, Any]:
        """退款处理"""
        # 查找交易记录
        transaction = self.db.query(SubscriptionTransaction).filter(
            SubscriptionTransaction.transaction_id == transaction_id
        ).first()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易记录不存在"
            )

        if transaction.status != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能对已成功的交易进行退款"
            )

        if refund_amount > transaction.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="退款金额不能大于交易金额"
            )

        # 模拟退款处理
        # 实际应该调用支付网关API处理退款
        
        # 创建退款记录
        from app.models.subscription import SubscriptionRefund
        refund = SubscriptionRefund(
            transaction_id=transaction.id,
            amount=refund_amount,
            reason=reason,
            status="processing",
            refund_id=f"REFUND{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
        )

        self.db.add(refund)
        self.db.commit()
        self.db.refresh(refund)

        return {
            "success": True,
            "message": "退款申请已提交",
            "refund_id": refund.refund_id,
            "amount": refund_amount,
            "status": "processing"
        }

    def _calculate_upgrade_price(
        self,
        user,
        new_plan_id: str,
        new_plan_price: float,
        billing_cycle: str,
        duration_months: int
    ) -> float:
        """
        计算升级价格（考虑补差价）

        Args:
            user: 用户对象
            new_plan_id: 新套餐ID
            new_plan_price: 新套餐原价
            billing_cycle: 计费周期
            duration_months: 订阅时长（月）

        Returns:
            实际应支付金额
        """
        # 获取用户当前会员等级
        current_tier = user.member_tier or 'free'

        # 如果是免费版或没有会员等级，直接返回新套餐价格
        if current_tier in ['free', 'personal_free']:
            return new_plan_price

        # 如果升级到相同等级（续费），直接返回新套餐价格
        if current_tier == new_plan_id:
            return new_plan_price

        # 检查是否有有效的订阅结束日期
        if not user.subscription_end_date:
            # 没有结束日期，按新套餐价格计算
            return new_plan_price

        # 计算剩余天数
        now = datetime.utcnow()
        if user.subscription_end_date <= now:
            # 订阅已过期，按新套餐价格计算
            return new_plan_price

        remaining_days = (user.subscription_end_date - now).days

        # 如果剩余天数小于1天，按新套餐价格计算
        if remaining_days < 1:
            return new_plan_price

        # 获取当前套餐信息
        current_plan = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == current_tier
        ).first()

        if not current_plan:
            # 找不到当前套餐，按新套餐价格计算
            return new_plan_price

        # 获取当前套餐的价格（根据用户当前的计费周期）
        # 注意: membership_type 存储的是 'personal' 或 'enterprise'，不是计费周期
        # 我们需要从订阅记录中获取计费周期
        current_subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).order_by(Subscription.created_at.desc()).first()

        if current_subscription and current_subscription.billing_cycle:
            current_billing_cycle = current_subscription.billing_cycle
        else:
            # 如果找不到订阅记录，使用新的计费周期
            current_billing_cycle = billing_cycle

        if current_billing_cycle == "monthly":
            current_plan_price = current_plan.monthly_price
            current_duration_months = 1
        elif current_billing_cycle == "quarterly":
            current_plan_price = current_plan.quarterly_price
            current_duration_months = 3
        elif current_billing_cycle == "yearly":
            current_plan_price = current_plan.yearly_price
            current_duration_months = 12
        else:
            # 无法确定当前计费周期，按新套餐价格计算
            return new_plan_price

        # 计算当前套餐的日均价格
        current_daily_price = current_plan_price / (current_duration_months * 30)

        # 计算新套餐的日均价格
        new_daily_price = new_plan_price / (duration_months * 30)

        # 计算剩余价值（当前套餐剩余天数的价值）
        remaining_value = current_daily_price * remaining_days

        # 计算补差价
        # 实际支付 = 新套餐价格 - 剩余价值
        upgrade_price = new_plan_price - remaining_value

        # 确保价格不为负数（如果降级，按新套餐价格计算）
        if upgrade_price < 0:
            upgrade_price = new_plan_price

        # 确保价格至少为0.01元
        if upgrade_price < 0.01:
            upgrade_price = 0.01

        print(f"[DEBUG] 升级补差价计算:")
        print(f"  当前套餐: {current_tier}, 价格: {current_plan_price}, 周期: {current_billing_cycle}")
        print(f"  新套餐: {new_plan_id}, 价格: {new_plan_price}, 周期: {billing_cycle}")
        print(f"  剩余天数: {remaining_days}")
        print(f"  当前日均价: {current_daily_price:.2f}")
        print(f"  新套餐日均价: {new_daily_price:.2f}")
        print(f"  剩余价值: {remaining_value:.2f}")
        print(f"  实际支付: {upgrade_price:.2f}")

        return round(upgrade_price, 2)


def get_payment_service(db: Session = Depends(deps.get_db)) -> PaymentService:
    """获取支付服务实例"""
    return PaymentService(db)
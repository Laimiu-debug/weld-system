"""
Payment service for handling payment processing.
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends

from app.api.v1.schemas.payment import (
    PaymentRequest, PaymentResponse, PaymentCallback, PaymentStatus
)
from app.models.subscription import Subscription, SubscriptionTransaction, SubscriptionPlan
from app.models.user import User
from app.core.config import settings
from app.services.payment_gateway import get_payment_gateway
from app.api import deps


class PaymentService:
    """支付服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_payment_order(
        self,
        user_id: str,
        plan_id: str,
        billing_cycle: str,
        payment_method: str
    ) -> Dict[str, Any]:
        """创建支付订单"""
        from app.models.user import User

        # 获取订阅计划
        plan = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active == True
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订阅计划不存在"
            )

        # 获取用户当前信息
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 计算新套餐价格
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

        # 计算实际支付金额（考虑升级补差价）
        price = self._calculate_upgrade_price(
            user=user,
            new_plan_id=plan_id,
            new_plan_price=new_plan_price,
            billing_cycle=billing_cycle,
            duration_months=duration_months
        )

        # 生成订单ID
        order_id = f"ORDER{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

        # 计算订阅时间
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_months * 30)

        # 创建订阅记录
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status="pending",
            billing_cycle=billing_cycle,
            price=price,
            currency="CNY",
            start_date=start_date,
            end_date=end_date,
            auto_renew=False,
            payment_method=payment_method
        )

        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        # 创建交易记录
        transaction = SubscriptionTransaction(
            subscription_id=subscription.id,
            transaction_id=f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}",
            amount=price,
            currency="CNY",
            payment_method=payment_method,
            status="pending",
            description=f"升级到 {plan.name} - {billing_cycle}"
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return {
            "order_id": order_id,
            "subscription_id": subscription.id,
            "transaction_id": transaction.transaction_id,
            "amount": price,
            "plan_name": plan.name,
            "billing_cycle": billing_cycle,
            "payment_method": payment_method,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
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

        # 映射支付渠道
        channel_map = {
            'alipay': 'alipay_qr',  # 支付宝扫码
            'wechat': 'wx_pub_qr',   # 微信扫码
            'bank': 'alipay_qr'      # 银行转账暂用支付宝
        }

        channel = channel_map.get(payment_method, 'alipay_qr')

        # 调用支付网关
        gateway = get_payment_gateway()

        payment_data = {
            'order_id': transaction.transaction_id,
            'amount': transaction.amount,
            'channel': channel,
            'subject': f"升级到{plan.name}",
            'body': f"{plan.name} - {subscription.billing_cycle}",
            'client_ip': client_ip
        }

        result = gateway.create_payment(payment_data)

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建支付订单失败: {result.get('error', '未知错误')}"
            )

        # 更新交易记录
        if hasattr(transaction, 'gateway_transaction_id'):
            transaction.gateway_transaction_id = result.get('charge_id')

        self.db.commit()

        # 提取支付凭证
        credential = result.get('credential', {})
        qr_code_url = credential.get(channel, '')

        return PaymentResponse(
            success=True,
            payment_url=qr_code_url,
            qr_code=qr_code_url,
            order_id=order_id,
            message="支付订单创建成功",
            amount=transaction.amount,
            payment_method=payment_method,
            created_at=datetime.now()
        )

    def handle_payment_callback(
        self,
        callback_data: PaymentCallback
    ) -> Dict[str, Any]:
        """处理支付回调"""
        # 验证签名
        if not self._verify_payment_signature(callback_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的支付签名"
            )

        # 查找交易记录
        transaction = self.db.query(SubscriptionTransaction).filter(
            SubscriptionTransaction.transaction_id == callback_data.transaction_id
        ).first()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易记录不存在"
            )

        # 更新交易状态
        transaction.status = callback_data.status
        transaction.transaction_date = callback_data.paid_at

        # 更新订阅状态
        subscription = transaction.subscription
        if callback_data.status == "success":
            subscription.status = "active"
            subscription.last_payment_date = callback_data.paid_at
            subscription.next_billing_date = subscription.end_date - timedelta(days=7)

            # 使用会员等级计算服务更新用户会员等级
            # 这样可以正确处理多订单场景
            from app.services.membership_tier_service import MembershipTierService
            tier_service = MembershipTierService(self.db)

            # 先提交订阅状态更新
            self.db.commit()

            # 然后更新用户会员等级（会自动选择最高等级）
            tier_result = tier_service.update_user_tier(subscription.user_id)

            print(f"[支付成功] 用户 {subscription.user_id} 会员等级更新: {tier_result['old_tier']} -> {tier_result['new_tier']}")

        else:
            self.db.commit()

        return {
            "success": True,
            "message": "支付回调处理成功",
            "transaction_id": callback_data.transaction_id,
            "status": callback_data.status
        }

    def get_payment_status(self, order_id: str) -> PaymentStatus:
        """获取支付状态"""
        # 模拟查询支付状态
        # 实际应该调用支付网关API查询
        
        return PaymentStatus(
            order_id=order_id,
            status="pending",
            amount=0,  # 从数据库获取
            paid_at=None,
            transaction_id=None,
            failure_reason=None
        )

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

    def _verify_payment_signature(self, callback_data: PaymentCallback) -> bool:
        """验证支付签名"""
        # 模拟签名验证
        # 实际应该根据支付网关的规则验证签名
        
        # 构造待签名字符串
        sign_str = f"order_id={callback_data.order_id}&transaction_id={callback_data.transaction_id}&amount={callback_data.amount}&status={callback_data.status}&paid_at={callback_data.paid_at.isoformat()}"
        
        # 计算签名
        sign = hashlib.md5(f"{sign_str}&{settings.SECRET_KEY}".encode()).hexdigest()
        
        # 比对签名
        return sign == callback_data.signature

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
        from app.models.user import User
        from datetime import datetime

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
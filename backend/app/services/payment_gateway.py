"""
支付网关服务 - 统一支付接口
支持多种支付方式：支付宝、微信支付等
"""
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json
import uuid
from abc import ABC, abstractmethod

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings


class PaymentGatewayInterface(ABC):
    """支付网关接口"""
    
    @abstractmethod
    def create_payment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建支付订单"""
        pass
    
    @abstractmethod
    def query_payment(self, transaction_id: str) -> Dict[str, Any]:
        """查询支付状态"""
        pass
    
    @abstractmethod
    def verify_callback(self, data: Dict[str, Any], signature: str) -> bool:
        """验证回调签名"""
        pass
    
    @abstractmethod
    def create_refund(self, transaction_id: str, amount: float, reason: str) -> Dict[str, Any]:
        """创建退款"""
        pass


class PingppGateway(PaymentGatewayInterface):
    """Ping++ 支付网关实现"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'PAYMENT_API_KEY', None)
        self.app_id = getattr(settings, 'PAYMENT_APP_ID', None)
        
        if not self.api_key or not self.app_id:
            raise ValueError("Ping++ API密钥未配置")
    
    def create_payment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建Ping++支付订单
        
        Args:
            order_data: {
                'order_id': 订单号,
                'amount': 金额（元）,
                'channel': 支付渠道 (alipay_qr, wx_pub_qr等),
                'subject': 商品标题,
                'body': 商品描述,
                'client_ip': 客户端IP
            }
        """
        try:
            import pingpp
            pingpp.api_key = self.api_key
            
            # 金额转换为分
            amount_cents = int(float(order_data['amount']) * 100)
            
            charge = pingpp.Charge.create(
                order_no=order_data['order_id'],
                amount=amount_cents,
                app=dict(id=self.app_id),
                channel=order_data['channel'],
                currency='cny',
                client_ip=order_data.get('client_ip', '127.0.0.1'),
                subject=order_data['subject'],
                body=order_data.get('body', ''),
                extra=self._get_channel_extra(order_data['channel'])
            )
            
            return {
                'success': True,
                'charge_id': charge.id,
                'order_id': charge.order_no,
                'amount': charge.amount / 100,
                'credential': charge.credential,
                'created_at': charge.created
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def query_payment(self, charge_id: str) -> Dict[str, Any]:
        """查询支付状态"""
        try:
            import pingpp
            pingpp.api_key = self.api_key
            
            charge = pingpp.Charge.retrieve(charge_id)
            
            return {
                'success': True,
                'charge_id': charge.id,
                'order_id': charge.order_no,
                'amount': charge.amount / 100,
                'paid': charge.paid,
                'status': 'success' if charge.paid else 'pending',
                'paid_at': charge.time_paid if charge.paid else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_callback(self, raw_data: bytes, signature: str) -> bool:
        """验证Ping++回调签名"""
        try:
            import pingpp
            pub_key_path = getattr(settings, 'PINGPP_PUBLIC_KEY_PATH', None)
            
            if not pub_key_path:
                # 如果没有配置公钥路径，使用简单验证
                return True
            
            return pingpp.Webhook.verify_signature(raw_data, signature, pub_key_path)
            
        except Exception:
            return False
    
    def create_refund(self, charge_id: str, amount: float, reason: str) -> Dict[str, Any]:
        """创建退款"""
        try:
            import pingpp
            pingpp.api_key = self.api_key
            
            amount_cents = int(float(amount) * 100)
            
            refund = pingpp.Refund.create(
                charge=charge_id,
                amount=amount_cents,
                description=reason
            )
            
            return {
                'success': True,
                'refund_id': refund.id,
                'charge_id': refund.charge,
                'amount': refund.amount / 100,
                'status': refund.status,
                'created_at': refund.created
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_channel_extra(self, channel: str) -> Dict[str, Any]:
        """获取渠道特定参数"""
        extras = {
            'alipay_qr': {},
            'wx_pub_qr': {},
            'alipay_wap': {
                'success_url': getattr(settings, 'PAYMENT_RETURN_URL', '')
            },
            'wx_pub': {
                'open_id': ''  # 需要从前端传入
            }
        }
        return extras.get(channel, {})


class MockPaymentGateway(PaymentGatewayInterface):
    """模拟支付网关 - 用于开发测试"""
    
    def __init__(self):
        self.payments = {}  # 模拟支付记录
    
    def create_payment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建模拟支付订单"""
        charge_id = f"ch_mock_{uuid.uuid4().hex[:16]}"

        payment_info = {
            'charge_id': charge_id,
            'order_id': order_data['order_id'],
            'amount': order_data['amount'],
            'channel': order_data['channel'],
            'status': 'pending',
            'paid': False,
            'created_at': datetime.utcnow().isoformat()
        }

        self.payments[charge_id] = payment_info

        # 生成模拟支付URL - 使用一个真实的二维码生成服务
        # 这里使用 api.qrserver.com 的免费二维码生成服务
        payment_url = f"mock://payment/{charge_id}?amount={order_data['amount']}&order={order_data['order_id']}"
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={payment_url}"

        return {
            'success': True,
            'charge_id': charge_id,
            'order_id': order_data['order_id'],
            'amount': order_data['amount'],
            'credential': {
                'object': 'credential',
                order_data['channel']: qr_code_url
            },
            'created_at': payment_info['created_at']
        }
    
    def query_payment(self, charge_id: str) -> Dict[str, Any]:
        """查询模拟支付状态"""
        payment = self.payments.get(charge_id)
        
        if not payment:
            return {
                'success': False,
                'error': 'Payment not found'
            }
        
        return {
            'success': True,
            'charge_id': charge_id,
            'order_id': payment['order_id'],
            'amount': payment['amount'],
            'paid': payment['paid'],
            'status': 'success' if payment['paid'] else 'pending',
            'paid_at': payment.get('paid_at')
        }
    
    def verify_callback(self, data: Dict[str, Any], signature: str) -> bool:
        """验证模拟回调签名"""
        # 模拟环境总是返回True
        return True
    
    def create_refund(self, charge_id: str, amount: float, reason: str) -> Dict[str, Any]:
        """创建模拟退款"""
        payment = self.payments.get(charge_id)
        
        if not payment:
            return {
                'success': False,
                'error': 'Payment not found'
            }
        
        refund_id = f"re_mock_{uuid.uuid4().hex[:16]}"
        
        return {
            'success': True,
            'refund_id': refund_id,
            'charge_id': charge_id,
            'amount': amount,
            'status': 'succeeded',
            'created_at': datetime.utcnow().isoformat()
        }
    
    def simulate_payment_success(self, charge_id: str):
        """模拟支付成功 - 仅用于测试"""
        if charge_id in self.payments:
            self.payments[charge_id]['paid'] = True
            self.payments[charge_id]['status'] = 'success'
            self.payments[charge_id]['paid_at'] = datetime.utcnow().isoformat()


class ManualPaymentGateway(PaymentGatewayInterface):
    """手动收款码网关：前端展示站内收款码，用户提交凭证后由管理员确认。"""

    def create_payment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "success": True,
            "charge_id": f"manual_{uuid.uuid4().hex[:16]}",
            "order_id": order_data["order_id"],
            "amount": order_data["amount"],
            "use_manual_qr": True,
            "credential": {},
            "created_at": datetime.utcnow().isoformat(),
        }

    def query_payment(self, charge_id: str) -> Dict[str, Any]:
        return {
            "success": True,
            "charge_id": charge_id,
            "status": "pending",
            "paid": False,
        }

    def verify_callback(self, data: Dict[str, Any], signature: str) -> bool:
        return False

    def create_refund(self, transaction_id: str, amount: float, reason: str) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "MANUAL_REFUND_REQUIRED",
            "message": "手动收款请线下退款",
        }


class PaymentGatewayFactory:
    """支付网关工厂"""

    @staticmethod
    def create_gateway(provider: str = None) -> PaymentGatewayInterface:
        """
        创建支付网关实例

        Args:
            provider: 支付服务商 (pingpp, xunhu, manual, mock)
        """
        if provider is None:
            provider = getattr(settings, 'PAYMENT_PROVIDER', 'mock')

        if provider == 'pingpp':
            return PingppGateway()
        elif provider == 'xunhu':
            # 延迟导入避免循环依赖
            from app.services.payment_gateway_xunhu import XunhuPaymentGateway
            return XunhuPaymentGateway()
        elif provider == 'manual':
            return ManualPaymentGateway()
        elif provider == 'mock':
            return MockPaymentGateway()
        else:
            raise ValueError(f"不支持的支付服务商: {provider}")


# 全局支付网关实例
_gateway_instance = None


def get_payment_gateway() -> PaymentGatewayInterface:
    """获取支付网关实例（单例模式）"""
    global _gateway_instance
    
    if _gateway_instance is None:
        _gateway_instance = PaymentGatewayFactory.create_gateway()
    
    return _gateway_instance


"""
虎皮椒支付网关实现
适用于个人开发者，无需企业资质
官方文档：https://www.xunhupay.com/doc
"""

import hashlib
import time
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from app.core.config import settings
from app.services.payment_gateway import PaymentGatewayInterface


class XunhuPaymentGateway(PaymentGatewayInterface):
    """虎皮椒支付网关"""
    
    def __init__(self):
        self.appid = settings.XUNHU_APPID
        self.appsecret = settings.XUNHU_APPSECRET
        self.api_url = "https://api.xunhupay.com"
        
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """
        生成签名
        
        Args:
            params: 参数字典
            
        Returns:
            签名字符串
        """
        # 按键名排序
        sorted_params = sorted(params.items())
        
        # 拼接字符串
        sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
        sign_str += f"&key={self.appsecret}"
        
        # MD5加密
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    def _verify_sign(self, params: Dict[str, Any]) -> bool:
        """
        验证签名
        
        Args:
            params: 包含签名的参数字典
            
        Returns:
            签名是否有效
        """
        if 'hash' not in params:
            return False
            
        received_sign = params.pop('hash')
        calculated_sign = self._generate_sign(params)
        
        return received_sign == calculated_sign
    
    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建支付订单
        
        Args:
            payment_data: 支付数据
                - order_id: 订单号
                - amount: 金额（元）
                - channel: 支付渠道 (alipay/wechat)
                - subject: 商品标题
                - body: 商品描述
                - client_ip: 客户端IP
                
        Returns:
            支付结果
                - success: 是否成功
                - payment_url: 支付URL
                - qr_code: 二维码内容
                - charge_id: 支付流水号
        """
        try:
            # 映射支付渠道
            channel_map = {
                'alipay': 'alipay',
                'alipay_qr': 'alipay',
                'wechat': 'wechat',
                'wx_pub_qr': 'wechat',
            }
            
            channel = channel_map.get(payment_data.get('channel', 'alipay'), 'alipay')
            
            # 构建请求参数
            params = {
                'version': '1.1',
                'appid': self.appid,
                'trade_order_id': payment_data['order_id'],
                'total_fee': f"{payment_data['amount']:.2f}",  # 金额，单位：元
                'title': payment_data.get('subject', '会员升级'),
                'time': str(int(time.time())),
                'notify_url': settings.PAYMENT_NOTIFY_URL,
                'return_url': settings.PAYMENT_RETURN_URL,
                'type': channel,
                'nonce_str': self._generate_nonce_str(),
            }
            
            # 生成签名
            params['hash'] = self._generate_sign(params)
            
            # 构建支付URL
            payment_url = f"{self.api_url}/payment/do.html?{urlencode(params)}"
            
            return {
                'success': True,
                'payment_url': payment_url,
                'qr_code': payment_url,  # 虎皮椒返回的URL就是二维码内容
                'charge_id': payment_data['order_id'],
                'channel': channel,
                'message': '支付订单创建成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'创建支付订单失败: {str(e)}'
            }
    
    def query_payment(self, order_id: str) -> Dict[str, Any]:
        """
        查询支付状态
        
        Args:
            order_id: 订单号
            
        Returns:
            支付状态
                - success: 是否成功
                - status: 支付状态 (pending/success/failed)
                - paid: 是否已支付
                - amount: 支付金额
        """
        try:
            # 构建查询参数
            params = {
                'appid': self.appid,
                'out_trade_order': order_id,
                'time': str(int(time.time())),
                'nonce_str': self._generate_nonce_str(),
            }
            
            # 生成签名
            params['hash'] = self._generate_sign(params)
            
            # 发送查询请求
            response = requests.get(
                f"{self.api_url}/payment/query",
                params=params,
                timeout=10
            )
            
            result = response.json()
            
            if result.get('errcode') == 0:
                data = result.get('data', {})
                status = data.get('status', 'pending')
                
                # 状态映射
                status_map = {
                    'OD': 'pending',      # 未支付
                    'SUCCESS': 'success',  # 支付成功
                    'FAILED': 'failed',    # 支付失败
                }
                
                return {
                    'success': True,
                    'status': status_map.get(status, 'pending'),
                    'paid': status == 'SUCCESS',
                    'amount': float(data.get('total_fee', 0)),
                    'transaction_id': data.get('transaction_id', ''),
                    'pay_time': data.get('time_end', ''),
                }
            else:
                return {
                    'success': False,
                    'status': 'pending',
                    'paid': False,
                    'error': result.get('errmsg', '查询失败')
                }
                
        except Exception as e:
            return {
                'success': False,
                'status': 'pending',
                'paid': False,
                'error': str(e)
            }
    
    def verify_callback(self, callback_data: Dict[str, Any]) -> bool:
        """
        验证支付回调
        
        Args:
            callback_data: 回调数据
            
        Returns:
            回调是否有效
        """
        try:
            # 复制数据以避免修改原始数据
            data = callback_data.copy()
            
            # 验证签名
            return self._verify_sign(data)
            
        except Exception as e:
            print(f"验证回调失败: {str(e)}")
            return False
    
    def create_refund(self, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建退款
        
        注意：虎皮椒需要手动在后台操作退款
        
        Args:
            refund_data: 退款数据
                - order_id: 原订单号
                - refund_amount: 退款金额
                - reason: 退款原因
                
        Returns:
            退款结果
        """
        # 虎皮椒不支持API退款，需要在后台手动操作
        return {
            'success': False,
            'error': 'MANUAL_REFUND_REQUIRED',
            'message': '虎皮椒需要在后台手动操作退款，请登录虎皮椒后台处理'
        }
    
    def _generate_nonce_str(self) -> str:
        """生成随机字符串"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))


# 工厂函数
def get_xunhu_gateway() -> XunhuPaymentGateway:
    """获取虎皮椒支付网关实例"""
    return XunhuPaymentGateway()


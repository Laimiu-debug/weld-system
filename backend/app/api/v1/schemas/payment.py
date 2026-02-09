"""
Payment schemas for the welding system backend.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PaymentRequest(BaseModel):
    """支付请求"""
    amount: float = Field(..., description="支付金额")
    currency: str = Field(default="CNY", description="货币类型")
    payment_method: str = Field(..., description="支付方式: alipay, wechat, bank")
    order_id: str = Field(..., description="订单ID")
    product_name: str = Field(..., description="产品名称")
    description: Optional[str] = Field(None, description="支付描述")
    return_url: Optional[str] = Field(None, description="支付成功返回URL")
    notify_url: Optional[str] = Field(None, description="支付结果通知URL")


class PaymentResponse(BaseModel):
    """支付响应"""
    success: bool = Field(..., description="支付是否成功")
    payment_url: Optional[str] = Field(None, description="支付页面URL")
    qr_code: Optional[str] = Field(None, description="支付二维码")
    order_id: str = Field(..., description="订单ID")
    transaction_id: Optional[str] = Field(None, description="交易ID")
    message: str = Field(..., description="响应消息")
    amount: float = Field(..., description="支付金额")
    payment_method: str = Field(..., description="支付方式")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class PaymentCallback(BaseModel):
    """支付回调"""
    order_id: str = Field(..., description="订单ID")
    transaction_id: str = Field(..., description="交易ID")
    amount: float = Field(..., description="支付金额")
    currency: str = Field(default="CNY", description="货币类型")
    payment_method: str = Field(..., description="支付方式")
    status: str = Field(..., description="支付状态: success, failed, pending")
    paid_at: datetime = Field(..., description="支付时间")
    signature: str = Field(..., description="签名")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")


class PaymentStatus(BaseModel):
    """支付状态查询"""
    order_id: str = Field(..., description="订单ID")
    status: str = Field(..., description="支付状态")
    amount: float = Field(..., description="支付金额")
    paid_at: Optional[datetime] = Field(None, description="支付时间")
    transaction_id: Optional[str] = Field(None, description="交易ID")
    failure_reason: Optional[str] = Field(None, description="失败原因")


class ManualPaymentRequest(BaseModel):
    """手动支付凭证提交请求"""
    order_id: str = Field(..., description="订单ID")
    transaction_id: str = Field(..., description="支付宝/微信交易号")
    payment_method: str = Field(..., description="支付方式: alipay, wechat")


class ManualPaymentConfirmRequest(BaseModel):
    """管理员确认手动支付请求"""
    order_id: str = Field(..., description="订单ID")
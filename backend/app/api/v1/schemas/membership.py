"""
Membership schemas for the welding system backend.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class SubscriptionPlanBase(BaseModel):
    """订阅计划基础模型"""
    id: str = Field(..., description="计划ID")
    name: str = Field(..., description="计划名称")
    description: Optional[str] = Field(None, description="计划描述")
    monthly_price: float = Field(0, description="月付价格")
    quarterly_price: float = Field(0, description="季付价格")
    yearly_price: float = Field(0, description="年付价格")
    currency: str = Field("CNY", description="货币单位")

    # 功能限制
    max_wps_files: int = Field(0, description="最大WPS文件数")
    max_pqr_files: int = Field(0, description="最大PQR文件数")
    max_ppqr_files: int = Field(0, description="最大pPQR文件数")
    max_materials: int = Field(0, description="最大材料数")
    max_welders: int = Field(0, description="最大焊工数")
    max_equipment: int = Field(0, description="最大设备数")
    max_factories: int = Field(0, description="最大工厂数")
    max_employees: int = Field(0, description="最大员工数")

    features: Optional[List[str]] = Field(None, description="功能列表")
    sort_order: int = Field(0, description="排序顺序")
    is_active: bool = Field(True, description="是否激活")
    is_recommended: bool = Field(False, description="是否推荐")


class SubscriptionPlan(SubscriptionPlanBase):
    """订阅计划完整模型"""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionBase(BaseModel):
    """订阅基础模型"""
    plan_id: str = Field(..., description="订阅计划ID")
    billing_cycle: str = Field(..., description="计费周期：monthly, quarterly, yearly")
    auto_renew: bool = Field(False, description="是否自动续费")
    payment_method: Optional[str] = Field(None, description="支付方式")


class SubscriptionCreate(SubscriptionBase):
    """创建订阅请求模型"""
    pass


class SubscriptionUpdate(BaseModel):
    """更新订阅请求模型"""
    status: Optional[str] = Field(None, description="订阅状态")
    auto_renew: Optional[bool] = Field(None, description="是否自动续费")
    payment_method: Optional[str] = Field(None, description="支付方式")


class Subscription(SubscriptionBase):
    """订阅完整模型"""
    id: int
    user_id: int
    status: str = Field(..., description="订阅状态")
    price: float = Field(..., description="价格")
    currency: str = Field(..., description="货币单位")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    trial_end_date: Optional[datetime] = Field(None, description="试用结束时间")
    last_payment_date: Optional[datetime] = Field(None, description="最后支付时间")
    next_billing_date: Optional[datetime] = Field(None, description="下次计费时间")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionTransactionBase(BaseModel):
    """订阅交易基础模型"""
    amount: float = Field(..., description="交易金额")
    currency: str = Field("CNY", description="货币单位")
    payment_method: str = Field(..., description="支付方式")
    description: Optional[str] = Field(None, description="描述")


class SubscriptionTransaction(SubscriptionTransactionBase):
    """订阅交易完整模型"""
    id: int
    subscription_id: int
    transaction_id: str = Field(..., description="交易ID")
    status: str = Field(..., description="交易状态")
    transaction_date: datetime = Field(..., description="交易时间")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MembershipUpgradeRequest(BaseModel):
    """会员升级请求模型"""
    plan_id: str = Field(..., description="目标计划ID")
    billing_cycle: str = Field(..., description="计费周期：monthly, quarterly, yearly")
    auto_renew: bool = Field(False, description="是否自动续费")
    payment_method: str = Field(..., description="支付方式：alipay, wechat, bank")


class MembershipUpgradeResponse(BaseModel):
    """会员升级响应模型"""
    success: bool = Field(..., description="是否成功")
    subscription_id: Optional[int] = Field(None, description="订阅ID")
    message: str = Field(..., description="响应消息")
    new_plan: Optional[str] = Field(None, description="新计划名称")
    next_billing_date: Optional[datetime] = Field(None, description="下次计费日期")
    amount_paid: Optional[float] = Field(None, description="支付金额")
    payment_url: Optional[str] = Field(None, description="支付页面URL")
    qr_code: Optional[str] = Field(None, description="支付二维码")


class SubscriptionInfo(BaseModel):
    """订阅信息模型"""
    plan_name: str = Field(..., description="计划名称")
    status: str = Field(..., description="订阅状态")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    auto_renew: bool = Field(..., description="是否自动续费")
    remaining_days: int = Field(..., description="剩余天数")
    features: List[str] = Field(..., description="功能列表")
    limits: dict = Field(..., description="使用限制")


class AdminSubscriptionInfo(BaseModel):
    """管理员订阅信息模型"""
    subscription_id: int
    user_id: int
    user_email: str
    user_name: str
    plan_name: str
    status: str
    billing_cycle: str
    price: float
    currency: str
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    payment_method: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
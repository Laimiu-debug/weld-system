"""
Subscription model for the welding system backend.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Subscription(Base):
    """订阅模型"""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(String, nullable=False)  # 订阅计划ID

    # 订阅状态
    status = Column(String, default="active")  # active, expired, cancelled, pending

    # 计费信息
    billing_cycle = Column(String, nullable=False)  # monthly, quarterly, yearly
    price = Column(Float, nullable=False)
    currency = Column(String, default="CNY")

    # 时间信息
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=False)
    trial_end_date = Column(DateTime, nullable=True)

    # 自动续费
    auto_renew = Column(Boolean, default=False)

    # 支付信息
    payment_method = Column(String, nullable=True)  # alipay, wechat, bank
    last_payment_date = Column(DateTime, nullable=True)
    next_billing_date = Column(DateTime, nullable=True)

    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="subscriptions")
    transactions = relationship("SubscriptionTransaction", back_populates="subscription", cascade="all, delete-orphan")


class SubscriptionPlan(Base):
    """订阅计划模型"""

    __tablename__ = "subscription_plans"

    id = Column(String, primary_key=True)  # 计划ID，如 'personal_pro'
    name = Column(String, nullable=False)  # 计划名称，如 '个人专业版'
    description = Column(String, nullable=True)

    # 价格信息
    monthly_price = Column(Float, default=0)
    quarterly_price = Column(Float, default=0)
    yearly_price = Column(Float, default=0)
    currency = Column(String, default="CNY")

    # 功能限制
    max_wps_files = Column(Integer, default=0)
    max_pqr_files = Column(Integer, default=0)
    max_ppqr_files = Column(Integer, default=0)
    max_materials = Column(Integer, default=0)
    max_welders = Column(Integer, default=0)
    max_equipment = Column(Integer, default=0)
    max_factories = Column(Integer, default=0)
    max_employees = Column(Integer, default=0)

    # 功能权限
    features = Column(String, nullable=True)  # JSON字符串存储功能列表

    # 排序和显示
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_recommended = Column(Boolean, default=False)

    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SubscriptionTransaction(Base):
    """订阅交易记录模型"""

    __tablename__ = "subscription_transactions"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    transaction_id = Column(String, unique=True, nullable=False)  # 第三方交易ID

    # 交易信息
    amount = Column(Float, nullable=False)
    currency = Column(String, default="CNY")
    payment_method = Column(String, nullable=False)

    # 交易状态
    status = Column(String, default="pending")  # pending, success, failed, refunded

    # 时间信息
    transaction_date = Column(DateTime, default=datetime.utcnow)

    # 备注信息
    description = Column(String, nullable=True)

    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    subscription = relationship("Subscription", back_populates="transactions")
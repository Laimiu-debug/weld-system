"""
Membership service for managing user memberships and subscriptions.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from fastapi import Depends
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionTransaction
from app.core.database import get_db
from app.services.payment_service import PaymentService


class MembershipService:
    """会员系统服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_membership_limits(self, tier: str) -> Dict[str, int]:
        """根据会员等级获取配额限制"""
        limits = {
            "free": {
                "wps": 10,
                "pqr": 10,
                "ppqr": 0,
                "materials": 0,
                "welders": 0,
                "equipment": 0,
                "storage": 100,  # MB
            },
            "personal_pro": {
                "wps": 30,
                "pqr": 30,
                "ppqr": 30,
                "materials": 50,
                "welders": 20,
                "equipment": 0,
                "storage": 500,
            },
            "personal_advanced": {
                "wps": 50,
                "pqr": 50,
                "ppqr": 50,
                "materials": 100,
                "welders": 50,
                "equipment": 20,
                "storage": 1000,
            },
            "personal_flagship": {
                "wps": 100,
                "pqr": 100,
                "ppqr": 100,
                "materials": 200,
                "welders": 100,
                "equipment": 50,
                "storage": 2000,
            },
            "enterprise": {
                "wps": 200,
                "pqr": 200,
                "ppqr": 200,
                "materials": 500,
                "welders": 200,
                "equipment": 100,
                "storage": 5000,
            },
            "enterprise_pro": {
                "wps": 400,
                "pqr": 400,
                "ppqr": 400,
                "materials": 1000,
                "welders": 500,
                "equipment": 200,
                "storage": 10000,
            },
            "enterprise_pro_max": {
                "wps": 500,
                "pqr": 500,
                "ppqr": 500,
                "materials": 2000,
                "welders": 1000,
                "equipment": 500,
                "storage": 20000,
            }
        }
        return limits.get(tier, limits["free"])

    def get_membership_features(self, tier: str) -> List[str]:
        """根据会员等级获取功能列表（动态生成）"""
        # 获取该等级的配额限制
        limits = self.get_membership_limits(tier)

        # 基础功能（所有等级都有）
        features = [
            f"WPS管理模块（{limits['wps']}个）",
            f"PQR管理模块（{limits['pqr']}个）"
        ]

        # pPQR模块（专业版及以上）
        if limits['ppqr'] > 0:
            features.append(f"pPQR管理模块（{limits['ppqr']}个）")

        # 焊材和焊工模块（专业版及以上）
        if tier not in ["free", "personal_free"]:
            if limits['materials'] > 0:
                features.append("焊材管理模块")
            if limits['welders'] > 0:
                features.append("焊工管理模块")

        # 生产、设备、质量模块（高级版及以上）
        if tier in ["personal_advanced", "personal_flagship"] or tier.startswith("enterprise"):
            features.append("生产管理模块")
            if limits['equipment'] > 0:
                features.append("设备管理模块")
            features.append("质量管理模块")

        # 报表统计（旗舰版及企业版）
        if tier == "personal_flagship" or tier.startswith("enterprise"):
            features.append("报表统计模块")

        # 企业版特有功能
        if tier.startswith("enterprise"):
            if tier == "enterprise":
                features.append("企业员工管理模块（10人）")
                features.append("多工厂数量：1个")
            elif tier == "enterprise_pro":
                features.append("企业员工管理模块（20人）")
                features.append("多工厂数量：3个")
            elif tier == "enterprise_pro_max":
                features.append("企业员工管理模块（50人）")
                features.append("多工厂数量：5个")

        return features

    def check_quota_available(self, user: User, resource_type: str, amount: int = 1) -> bool:
        """检查用户配额是否足够（处理None值）"""
        limits = self.get_membership_limits(user.member_tier)

        if resource_type == "wps":
            used = user.wps_quota_used or 0
            return used + amount <= limits["wps"]
        elif resource_type == "pqr":
            used = user.pqr_quota_used or 0
            return used + amount <= limits["pqr"]
        elif resource_type == "ppqr":
            used = user.ppqr_quota_used or 0
            return used + amount <= limits["ppqr"]
        elif resource_type == "storage":
            used = user.storage_quota_used or 0
            return used + amount <= limits["storage"]

        return False

    def update_quota_usage(self, user: User, resource_type: str, amount: int) -> bool:
        """
        更新用户配额使用情况

        Args:
            user: 用户对象
            resource_type: 资源类型 (wps/pqr/ppqr/storage)
            amount: 变更数量（正数=增加，负数=减少）

        Returns:
            bool: 是否更新成功
        """
        if amount == 0:
            return True

        # 只在增加配额时检查是否超限
        if amount > 0:
            if not self.check_quota_available(user, resource_type, amount):
                return False

        # 更新配额使用量（处理None值）
        if resource_type == "wps":
            current = user.wps_quota_used or 0
            user.wps_quota_used = max(0, current + amount)
        elif resource_type == "pqr":
            current = user.pqr_quota_used or 0
            user.pqr_quota_used = max(0, current + amount)
        elif resource_type == "ppqr":
            current = user.ppqr_quota_used or 0
            user.ppqr_quota_used = max(0, current + amount)
        elif resource_type == "storage":
            current = user.storage_quota_used or 0
            user.storage_quota_used = max(0, current + amount)

        self.db.commit()
        return True

    def get_user_membership_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户会员信息"""
        from app.models.company import CompanyEmployee, Company
        from datetime import datetime

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # 获取订阅信息（优先从订阅表获取最新的活跃订阅）
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).first()

        # 确定订阅状态和日期
        subscription_status = user.subscription_status or "inactive"
        subscription_start_date = user.subscription_start_date
        subscription_end_date = user.subscription_end_date
        auto_renewal = user.auto_renewal if user.auto_renewal is not None else False

        if subscription:
            # 如果有订阅记录，使用订阅表的数据
            subscription_status = subscription.status or "inactive"
            subscription_start_date = subscription.start_date
            subscription_end_date = subscription.end_date
            auto_renewal = subscription.auto_renew if subscription.auto_renew is not None else False

            # 更新用户表中的数据以保持同步
            user.subscription_status = subscription.status
            user.subscription_start_date = subscription.start_date
            user.subscription_end_date = subscription.end_date
            user.auto_renewal = subscription.auto_renew
            self.db.commit()
        else:
            # 如果没有订阅记录，根据会员等级设置默认值
            member_tier = user.member_tier or "free"

            # 免费版用户默认为激活状态
            if member_tier in ["free", "personal_free"]:
                subscription_status = "active"
                # 订阅开始日期为注册日期
                if not subscription_start_date and hasattr(user, 'created_at') and user.created_at:
                    subscription_start_date = user.created_at
                # 免费版永久有效，结束日期为None
                subscription_end_date = None
                auto_renewal = False
            else:
                # 付费版用户如果没有订阅记录，检查是否有结束日期
                if not subscription_status or subscription_status == "inactive":
                    # 如果有结束日期且未过期，设置为激活
                    if subscription_end_date and subscription_end_date > datetime.utcnow():
                        subscription_status = "active"
                    else:
                        subscription_status = "inactive"

                # 如果没有开始日期，使用注册日期
                if not subscription_start_date and hasattr(user, 'created_at') and user.created_at:
                    subscription_start_date = user.created_at

        limits = self.get_membership_limits(user.member_tier)
        features = self.get_membership_features(user.member_tier)

        # 检查用户是否通过企业继承会员权限
        is_inherited_from_company = False
        is_company_owner = False
        company_name = None

        # 如果用户是企业会员类型，检查是否是企业员工或企业所有者
        if user.membership_type == "enterprise":
            # 先查询用户是否拥有企业
            owned_company = self.db.query(Company).filter(Company.owner_id == user_id).first()

            if owned_company:
                # 用户是企业所有者，使用企业的订阅信息
                is_company_owner = True
                company_name = owned_company.name

                # 使用企业的订阅信息
                if owned_company.subscription_status:
                    subscription_status = owned_company.subscription_status
                if owned_company.subscription_start_date:
                    subscription_start_date = owned_company.subscription_start_date
                if owned_company.subscription_end_date:
                    subscription_end_date = owned_company.subscription_end_date
                if owned_company.auto_renewal is not None:
                    auto_renewal = owned_company.auto_renewal
            else:
                # 查询用户是否是某个企业的员工
                employee = self.db.query(CompanyEmployee).filter(
                    CompanyEmployee.user_id == user_id,
                    CompanyEmployee.status == "active"
                ).first()

                if employee:
                    # 获取企业信息
                    company = self.db.query(Company).filter(Company.id == employee.company_id).first()
                    if company:
                        # 用户是企业员工（非所有者），继承企业的会员权限
                        is_inherited_from_company = True
                        company_name = company.name

                        # 继承企业的订阅信息
                        if company.subscription_status:
                            subscription_status = company.subscription_status
                        if company.subscription_start_date:
                            subscription_start_date = company.subscription_start_date
                        if company.subscription_end_date:
                            subscription_end_date = company.subscription_end_date
                        if company.auto_renewal is not None:
                            auto_renewal = company.auto_renewal

        return {
            "user_id": user.id,
            "email": user.email,
            "membership_tier": user.member_tier or "free",
            "membership_type": user.membership_type or "personal",
            "subscription_status": subscription_status,
            "subscription_start_date": subscription_start_date.isoformat() if subscription_start_date else None,
            "subscription_end_date": subscription_end_date.isoformat() if subscription_end_date else None,
            "auto_renewal": auto_renewal,
            "is_inherited_from_company": is_inherited_from_company,
            "is_company_owner": is_company_owner,
            "company_name": company_name,
            "features": features,
            "quotas": {
                "wps": {"used": user.wps_quota_used or 0, "limit": limits["wps"]},
                "pqr": {"used": user.pqr_quota_used or 0, "limit": limits["pqr"]},
                "ppqr": {"used": user.ppqr_quota_used or 0, "limit": limits["ppqr"]},
                "storage": {"used": user.storage_quota_used or 0, "limit": limits["storage"]},
            }
        }

    def upgrade_membership(self, user_id: int, new_tier: str, admin_id: Optional[int] = None, reason: str = "") -> bool:
        """升级用户会员等级"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        old_tier = user.member_tier
        old_membership_type = user.membership_type

        # 更新会员等级
        user.member_tier = new_tier
        user.subscription_status = "active"
        user.subscription_start_date = datetime.utcnow()
        user.subscription_end_date = datetime.utcnow() + timedelta(days=30)  # 默认30天

        # 判断是否为企业会员
        is_enterprise_tier = new_tier in ["enterprise", "enterprise_pro", "enterprise_pro_max"]
        if is_enterprise_tier:
            user.membership_type = "enterprise"
        else:
            user.membership_type = "personal"

        user.updated_at = datetime.utcnow()
        self.db.commit()

        # 如果升级到企业会员，自动创建企业和员工记录
        if is_enterprise_tier and old_membership_type != "enterprise":
            self._create_enterprise_for_user(user, new_tier)

        # TODO: 记录操作日志
        # TODO: 发送通知

        return True

    def _create_enterprise_for_user(self, user: User, tier: str):
        """为用户创建企业和员工记录"""
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(self.db)

        # 检查是否已有企业
        existing_company = enterprise_service.get_company_by_owner(user.id)
        if existing_company:
            # 如果已有企业，更新会员等级
            enterprise_service.update_company(
                existing_company.id,
                membership_tier=tier,
                subscription_status="active",
                subscription_start_date=datetime.utcnow()
            )
            print(f"✅ 更新企业 {existing_company.name} 的会员等级为 {tier}")
            return

        # 创建企业
        company_name = user.company or f"{user.full_name or user.email}的企业"
        company = enterprise_service.create_company(
            owner_id=user.id,
            name=company_name,
            membership_tier=tier,
            contact_person=user.full_name,
            contact_phone=user.phone,
            contact_email=user.email
        )
        print(f"✅ 为用户 {user.email} 创建企业: {company.name} (ID: {company.id})")

        # 创建默认工厂（总部）
        factory = enterprise_service.create_factory(
            company_id=company.id,
            name=f"{company_name} - 总部",
            is_headquarters=True,
            created_by=user.id
        )
        print(f"✅ 为企业创建总部工厂: {factory.name} (ID: {factory.id})")

        # 将用户添加为企业管理员
        employee = enterprise_service.create_employee(
            company_id=company.id,
            user_id=user.id,
            role="admin",
            factory_id=factory.id,
            position="企业所有者",
            department="管理层",
            data_access_scope="company",
            created_by=user.id
        )
        print(f"✅ 将用户添加为企业管理员: {employee.employee_number}")

    def get_subscription_plans(self) -> List[Dict[str, Any]]:
        """获取所有订阅计划"""
        plans = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()

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
                "features": plan.features.split(",") if plan.features else [],
                "is_recommended": plan.is_recommended,
            })

        return result

    def get_expiring_subscriptions(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """获取即将过期的订阅"""
        expiry_date = datetime.utcnow() + timedelta(days=days_ahead)

        users = self.db.query(User).filter(
            and_(
                User.subscription_end_date <= expiry_date,
                User.subscription_end_date > datetime.utcnow(),
                User.auto_renewal == False,
                User.member_tier != "free"
            )
        ).all()

        result = []
        for user in users:
            result.append({
                "user_id": user.id,
                "email": user.email,
                "membership_tier": user.member_tier,
                "expiry_date": user.subscription_end_date.isoformat(),
                "days_until_expiry": (user.subscription_end_date - datetime.utcnow()).days
            })

        return result

    def process_subscription_renewal(self, user_id: int) -> bool:
        """创建待支付续费订单，不在未扣款时延长有效期。"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        ).order_by(Subscription.end_date.desc()).first()
        if not subscription:
            return False

        PaymentService(self.db).create_renewal_order_if_needed(subscription, notify=True)
        return True


def get_membership_service(db: Session = Depends(get_db)) -> MembershipService:
    """获取会员服务实例"""
    return MembershipService(db)
"""
会员等级计算和自动切换服务
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json

from app.models.subscription import Subscription
from app.models.user import User


# 会员等级优先级定义（数字越大优先级越高）
TIER_PRIORITY = {
    "enterprise_pro_max": 7,
    "enterprise_pro": 6,
    "enterprise": 5,
    "personal_flagship": 4,
    "personal_advanced": 3,
    "personal_pro": 2,
    "personal_free": 1,
    "free": 0
}


class MembershipTierService:
    """会员等级计算服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_tier_priority(self, tier: str) -> int:
        """获取会员等级的优先级"""
        return TIER_PRIORITY.get(tier, 0)

    def get_tier_permissions(self, tier: str) -> Dict[str, bool]:
        """
        根据会员等级生成权限字典

        这个方法生成的权限用于存储在user.permissions字段中,
        与前端的权限检查逻辑保持一致
        """
        # 基础权限模板
        base_permissions = {
            "wps_management": False,
            "pqr_management": False,
            "ppqr_management": False,
            "equipment_management": False,
            "production_management": False,
            "quality_management": False,
            "materials_management": False,
            "welders_management": False,
            "employee_management": False,
            "multi_factory_management": False,
            "reports_management": False,
            "api_access": False
        }

        # 根据会员等级设置权限
        if tier == "free" or tier == "personal_free":
            # 个人免费版: WPS、PQR
            base_permissions["wps_management"] = True
            base_permissions["pqr_management"] = True

        elif tier == "personal_pro":
            # 个人专业版: WPS、PQR、pPQR、焊材、焊工
            base_permissions["wps_management"] = True
            base_permissions["pqr_management"] = True
            base_permissions["ppqr_management"] = True
            base_permissions["materials_management"] = True
            base_permissions["welders_management"] = True

        elif tier == "personal_advanced":
            # 个人高级版: 专业版 + 设备、生产、质量
            base_permissions["wps_management"] = True
            base_permissions["pqr_management"] = True
            base_permissions["ppqr_management"] = True
            base_permissions["materials_management"] = True
            base_permissions["welders_management"] = True
            base_permissions["equipment_management"] = True
            base_permissions["production_management"] = True
            base_permissions["quality_management"] = True

        elif tier == "personal_flagship":
            # 个人旗舰版: 高级版 + 报表
            base_permissions["wps_management"] = True
            base_permissions["pqr_management"] = True
            base_permissions["ppqr_management"] = True
            base_permissions["materials_management"] = True
            base_permissions["welders_management"] = True
            base_permissions["equipment_management"] = True
            base_permissions["production_management"] = True
            base_permissions["quality_management"] = True
            base_permissions["reports_management"] = True

        elif tier in ["enterprise", "enterprise_pro", "enterprise_pro_max"]:
            # 企业版: 所有功能
            base_permissions["wps_management"] = True
            base_permissions["pqr_management"] = True
            base_permissions["ppqr_management"] = True
            base_permissions["materials_management"] = True
            base_permissions["welders_management"] = True
            base_permissions["equipment_management"] = True
            base_permissions["production_management"] = True
            base_permissions["quality_management"] = True
            base_permissions["reports_management"] = True
            base_permissions["employee_management"] = True
            base_permissions["multi_factory_management"] = True
            base_permissions["api_access"] = True

        return base_permissions

    def get_active_subscriptions(self, user_id: int) -> List[Subscription]:
        """
        获取用户所有有效的订阅
        
        有效订阅的条件：
        1. status = 'active'
        2. end_date > now()
        """
        now = datetime.utcnow()
        
        subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == 'active',
                Subscription.end_date > now
            )
        ).all()
        
        return subscriptions

    def sort_subscriptions_by_priority(
        self, 
        subscriptions: List[Subscription]
    ) -> List[Subscription]:
        """
        按优先级对订阅进行排序
        
        排序规则：
        1. 首先按会员等级优先级降序（高等级优先）
        2. 然后按到期时间升序（先到期的优先，用于确定性排序）
        """
        return sorted(
            subscriptions,
            key=lambda s: (
                -self.get_tier_priority(s.plan_id),  # 负号表示降序
                s.end_date  # 升序
            )
        )

    def calculate_current_tier(
        self, 
        user_id: int
    ) -> Tuple[Optional[str], Optional[Subscription], Optional[Subscription]]:
        """
        计算用户当前应该拥有的会员等级
        
        Returns:
            Tuple[当前会员等级, 当前订阅, 次高等级订阅]
        """
        # 获取所有有效订阅
        active_subscriptions = self.get_active_subscriptions(user_id)
        
        if not active_subscriptions:
            # 没有有效订阅，返回免费版
            return "free", None, None
        
        # 按优先级排序
        sorted_subscriptions = self.sort_subscriptions_by_priority(active_subscriptions)
        
        # 当前会员等级是优先级最高的订阅
        current_subscription = sorted_subscriptions[0]
        current_tier = current_subscription.plan_id
        
        # 次高等级订阅（如果存在）
        next_subscription = None
        if len(sorted_subscriptions) > 1:
            next_subscription = sorted_subscriptions[1]
        
        return current_tier, current_subscription, next_subscription

    def update_user_tier(self, user_id: int) -> Dict[str, any]:
        """
        更新用户的会员等级

        Returns:
            Dict包含更新信息：
            - old_tier: 旧会员等级
            - new_tier: 新会员等级
            - changed: 是否发生变化
            - current_subscription: 当前订阅
            - next_subscription: 次高等级订阅
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"用户不存在: {user_id}")

        old_tier = user.member_tier
        old_membership_type = user.membership_type

        # 计算当前应该拥有的会员等级
        new_tier, current_subscription, next_subscription = self.calculate_current_tier(user_id)

        # 更新用户会员信息
        changed = False
        if old_tier != new_tier:
            user.member_tier = new_tier
            changed = True

            # 根据会员等级更新membership_type
            is_enterprise_tier = new_tier in ["enterprise", "enterprise_pro", "enterprise_pro_max"]
            if is_enterprise_tier:
                user.membership_type = "enterprise"
            else:
                user.membership_type = "personal"

        # 🔥 关键修复: 始终更新permissions字段以确保与会员等级一致
        # 这样前端的权限检查才能正确工作
        # 即使会员等级没有变化,也要确保permissions字段是正确的
        permissions_dict = self.get_tier_permissions(new_tier)
        expected_permissions_json = json.dumps(permissions_dict)

        # 检查permissions是否需要更新
        if user.permissions != expected_permissions_json:
            user.permissions = expected_permissions_json
            print(f"[MembershipTierService] 更新用户 {user.email} 的permissions字段以匹配会员等级 {new_tier}")

        # 更新订阅状态和时间
        if current_subscription:
            user.subscription_status = "active"
            user.subscription_start_date = current_subscription.start_date
            user.subscription_end_date = current_subscription.end_date
            user.subscription_expires_at = current_subscription.end_date
        else:
            # 没有有效订阅
            user.subscription_status = "expired"
            user.subscription_end_date = None
            user.subscription_expires_at = None

        user.updated_at = datetime.utcnow()
        self.db.commit()

        # 如果升级到企业会员,需要创建或更新企业记录
        if changed:
            is_enterprise_tier = new_tier in ["enterprise", "enterprise_pro", "enterprise_pro_max"]
            if is_enterprise_tier:
                # 如果是新升级到企业会员,创建企业记录
                if old_membership_type != "enterprise":
                    self._create_enterprise_for_user(user, new_tier, current_subscription)
                else:
                    # 如果已经是企业会员,更新企业的会员等级和到期时间
                    self._update_enterprise_tier(user, new_tier, current_subscription)

        return {
            "old_tier": old_tier,
            "new_tier": new_tier,
            "changed": changed,
            "current_subscription": current_subscription,
            "next_subscription": next_subscription
        }

    def get_user_subscription_summary(self, user_id: int) -> Dict[str, any]:
        """
        获取用户订阅摘要信息
        
        Returns:
            Dict包含：
            - current_tier: 当前会员等级
            - current_subscription: 当前订阅信息
            - next_subscription: 次高等级订阅信息
            - all_active_subscriptions: 所有有效订阅列表
        """
        current_tier, current_subscription, next_subscription = self.calculate_current_tier(user_id)
        all_active_subscriptions = self.get_active_subscriptions(user_id)
        
        # 格式化订阅信息
        def format_subscription(sub: Optional[Subscription]) -> Optional[Dict]:
            if not sub:
                return None
            return {
                "id": sub.id,
                "plan_id": sub.plan_id,
                "billing_cycle": sub.billing_cycle,
                "start_date": sub.start_date.isoformat() if sub.start_date else None,
                "end_date": sub.end_date.isoformat() if sub.end_date else None,
                "status": sub.status,
                "priority": self.get_tier_priority(sub.plan_id)
            }
        
        return {
            "current_tier": current_tier,
            "current_subscription": format_subscription(current_subscription),
            "next_subscription": format_subscription(next_subscription),
            "all_active_subscriptions": [
                format_subscription(sub) for sub in all_active_subscriptions
            ]
        }

    def check_and_switch_expired_subscriptions(self) -> List[Dict[str, any]]:
        """
        检查所有用户的订阅，处理到期的订阅并自动切换会员等级

        这个方法应该由定时任务调用

        Returns:
            List[Dict] 包含所有发生变化的用户信息
        """
        now = datetime.utcnow()

        # 查找所有状态为active但已经过期的订阅
        expired_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'active',
                Subscription.end_date <= now
            )
        ).all()

        # 将过期订阅标记为expired
        for subscription in expired_subscriptions:
            subscription.status = 'expired'

        self.db.commit()

        # 刷新会话，确保后续查询能看到最新状态
        self.db.expire_all()

        # 获取受影响的用户ID（去重）
        affected_user_ids = list(set([sub.user_id for sub in expired_subscriptions]))

        # 更新每个受影响用户的会员等级
        results = []
        for user_id in affected_user_ids:
            try:
                result = self.update_user_tier(user_id)
                result['user_id'] = user_id
                results.append(result)

                # 记录日志
                if result['changed']:
                    print(f"[会员等级自动切换] 用户 {user_id}: {result['old_tier']} -> {result['new_tier']}")
                    if result['next_subscription']:
                        print(f"  切换到次高等级订阅: {result['next_subscription'].plan_id}")
                    else:
                        print(f"  没有其他有效订阅，降为免费版")
            except Exception as e:
                print(f"[会员等级自动切换错误] 用户 {user_id}: {str(e)}")
                results.append({
                    "user_id": user_id,
                    "error": str(e)
                })

        return results

    def get_all_subscriptions_for_user(
        self, 
        user_id: int,
        include_expired: bool = True
    ) -> List[Dict[str, any]]:
        """
        获取用户的所有订阅历史
        
        Args:
            user_id: 用户ID
            include_expired: 是否包含已过期的订阅
            
        Returns:
            List[Dict] 订阅列表，按创建时间降序排列
        """
        query = self.db.query(Subscription).filter(Subscription.user_id == user_id)
        
        if not include_expired:
            query = query.filter(Subscription.status == 'active')
        
        subscriptions = query.order_by(Subscription.created_at.desc()).all()
        
        result = []
        for sub in subscriptions:
            result.append({
                "id": sub.id,
                "plan_id": sub.plan_id,
                "billing_cycle": sub.billing_cycle,
                "price": sub.price,
                "currency": sub.currency,
                "status": sub.status,
                "start_date": sub.start_date.isoformat() if sub.start_date else None,
                "end_date": sub.end_date.isoformat() if sub.end_date else None,
                "created_at": sub.created_at.isoformat() if sub.created_at else None,
                "priority": self.get_tier_priority(sub.plan_id),
                "is_active": sub.status == 'active' and sub.end_date > datetime.utcnow()
            })
        
        return result

    def _create_enterprise_for_user(self, user: User, tier: str, subscription: Subscription):
        """为用户创建企业和员工记录"""
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(self.db)

        # 检查是否已有企业
        existing_company = enterprise_service.get_company_by_owner(user.id)
        if existing_company:
            # 如果已有企业,更新会员等级
            update_data = {
                "membership_tier": tier,
                "subscription_status": "active",
                "subscription_start_date": subscription.start_date if subscription else datetime.utcnow()
            }

            if subscription:
                update_data["subscription_end_date"] = subscription.end_date

            enterprise_service.update_company(existing_company.id, **update_data)
            print(f"✅ 更新企业 {existing_company.name} 的会员等级为 {tier}")
            return

        # 创建新企业
        company_name = f"{user.full_name or user.username}的企业"

        # create_company方法会根据membership_tier自动设置配额限制和subscription_status
        # 所以这里只需要传递基本信息和订阅结束日期
        company_data = {
            "owner_id": user.id,
            "name": company_name,
            "membership_tier": tier
        }

        # 如果有订阅信息,传递订阅结束日期
        if subscription:
            company_data["subscription_end_date"] = subscription.end_date

        company = enterprise_service.create_company(**company_data)
        print(f"✅ 为用户 {user.email} 创建企业: {company.name}")

        # 创建默认工厂
        factory = enterprise_service.create_factory(
            company_id=company.id,
            name="默认工厂",
            address="待完善",
            description="系统自动创建的默认工厂"
        )
        print(f"✅ 为企业 {company.name} 创建默认工厂: {factory.name}")

        # 将所有者添加为企业员工
        enterprise_service.create_employee(
            company_id=company.id,
            user_id=user.id,
            role="admin",  # 所有者使用admin角色
            factory_id=factory.id,
            created_by=user.id
        )
        print(f"✅ 将用户 {user.email} 添加为企业所有者")

    def _update_enterprise_tier(self, user: User, tier: str, subscription: Subscription):
        """更新企业的会员等级、配额和到期时间"""
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(self.db)

        # 获取用户的企业
        company = enterprise_service.get_company_by_owner(user.id)
        if company:
            # 根据新的会员等级获取配额限制
            tier_limits = enterprise_service._get_tier_limits(tier)

            # 准备更新数据
            update_data = {
                "membership_tier": tier,
                "max_employees": tier_limits["max_employees"],
                "max_factories": tier_limits["max_factories"],
                "max_wps_records": tier_limits["max_wps_records"],
                "max_pqr_records": tier_limits["max_pqr_records"],
                "subscription_status": "active",
                "subscription_start_date": subscription.start_date if subscription else datetime.utcnow()
            }

            # 如果提供了订阅信息,同步更新企业的到期时间
            if subscription:
                update_data["subscription_end_date"] = subscription.end_date
                print(f"   - 订阅到期时间: {subscription.end_date.strftime('%Y-%m-%d')}")

            enterprise_service.update_company(company.id, **update_data)
            print(f"✅ 更新企业 {company.name} 的会员等级为 {tier}")
            print(f"   - 最大员工数: {tier_limits['max_employees']}")
            print(f"   - 最大工厂数: {tier_limits['max_factories']}")
            print(f"   - WPS配额: {tier_limits['max_wps_records']}")
            print(f"   - PQR配额: {tier_limits['max_pqr_records']}")


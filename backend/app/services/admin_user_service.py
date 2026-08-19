"""
Admin user management service for admin operations.
管理员用户管理服务
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text

from app.models.user import User
from app.models.admin import Admin
from app.models.company import CompanyEmployee

logger = logging.getLogger(__name__)


class AdminUserService:
    """管理员用户管理服务类"""

    def __init__(self):
        pass

    def get_users_with_filters(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        membership_tier: Optional[str] = None,
        is_active: Optional[bool] = None,
        membership_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_field: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        获取用户列表（支持筛选和分页）
        """
        query = db.query(User)

        # 搜索功能
        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
                User.company.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # 会员等级筛选
        if membership_tier:
            query = query.filter(text("member_tier = :tier")).params(tier=membership_tier)

        # 用户状态筛选
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # 会员类型筛选
        if membership_type:
            query = query.filter(text("membership_type = :mtype")).params(mtype=membership_type)

        # 日期范围筛选
        if start_date:
            query = query.filter(User.created_at >= start_date)
        if end_date:
            query = query.filter(User.created_at <= end_date)

        # 排序
        if hasattr(User, sort_field):
            sort_column = getattr(User, sort_field)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        # 总数统计
        total = query.count()

        # 分页查询
        offset = (page - 1) * page_size
        users = query.offset(offset).limit(page_size).all()

        # 转换为响应格式
        user_items = []
        for user in users:
            user_data = self._format_user_data(user)
            user_items.append(user_data)

        return {
            "items": user_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        try:
            # 首先尝试作为整数ID处理
            user_int_id = int(user_id)
            user = db.query(User).filter(User.id == user_int_id).first()
            if user:
                return user
        except ValueError:
            pass

        try:
            # 如果整数ID不存在，尝试作为UUID处理
            user_uuid = UUID(user_id)
            return db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            return None

    def get_user_detail_data(self, db: Session, user: User) -> Dict[str, Any]:
        """获取用户详细信息数据"""
        return self._format_user_data(user, detailed=True)

    def adjust_user_membership(
        self,
        db: Session,
        user: User,
        membership_tier: Optional[str] = None,
        expires_at: Optional[str] = None,
        quotas: Optional[Dict[str, Any]] = None,
        reason: str = "",
        current_admin: Admin = None
    ) -> Dict[str, Any]:
        """
        调整用户会员等级
        """
        from app.models.subscription import Subscription

        # 记录调整前的状态
        old_tier = getattr(user, 'member_tier', 'free')
        old_membership_type = getattr(user, 'membership_type', 'personal')
        old_expires_at = getattr(user, 'subscription_expires_at', None)

        # 更新用户会员信息
        if membership_tier:
            try:
                user.member_tier = membership_tier
                # 判断是否为企业会员
                is_enterprise_tier = membership_tier in ["enterprise", "enterprise_pro", "enterprise_pro_max"]
                if is_enterprise_tier:
                    user.membership_type = "enterprise"
                else:
                    user.membership_type = "personal"
            except AttributeError:
                pass

        if expires_at:
            try:
                end_date = datetime.fromisoformat(expires_at)
                # 同时更新两个字段以保持兼容性
                user.subscription_end_date = end_date
                user.subscription_expires_at = end_date
            except (ValueError, AttributeError):
                pass

        # 自动根据会员等级更新配额和权限（如果没有手动指定配额）
        if membership_tier and not quotas:
            # 自动根据新的会员等级设置配额限制
            if hasattr(user, 'wps_limit'):
                user.wps_limit = self._get_wps_limit(membership_tier)
            if hasattr(user, 'pqr_limit'):
                user.pqr_limit = self._get_pqr_limit(membership_tier)
            if hasattr(user, 'ppqr_limit'):
                user.ppqr_limit = self._get_ppqr_limit(membership_tier)

            # 自动根据新的会员等级设置功能权限
            if hasattr(user, 'permissions'):
                user.permissions = self._get_permissions_by_tier(membership_tier)

        # 如果管理员手动指定了配额，使用管理员的设置
        if quotas:
            if quotas.get("wps_quota_used") is not None:
                user.wps_quota_used = quotas["wps_quota_used"]
            if quotas.get("pqr_quota_used") is not None:
                user.pqr_quota_used = quotas["pqr_quota_used"]
            if quotas.get("ppqr_quota_used") is not None:
                user.ppqr_quota_used = quotas["ppqr_quota_used"]
            if quotas.get("storage_quota_used") is not None:
                user.storage_quota_used = quotas["storage_quota_used"]
            # 手动设置配额限制
            if quotas.get("wps_limit") is not None:
                user.wps_limit = quotas["wps_limit"]
            if quotas.get("pqr_limit") is not None:
                user.pqr_limit = quotas["pqr_limit"]
            if quotas.get("ppqr_limit") is not None:
                user.ppqr_limit = quotas["ppqr_limit"]

        user.updated_at = datetime.utcnow()

        # 同时更新订阅表（如果存在）
        subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        if subscription:
            if membership_tier:
                subscription.plan_id = membership_tier
            if expires_at:
                try:
                    subscription.end_date = datetime.fromisoformat(expires_at)
                    # 更新状态为激活（如果未来时间）
                    if datetime.fromisoformat(expires_at) > datetime.utcnow():
                        subscription.status = 'active'
                    else:
                        subscription.status = 'expired'
                except (ValueError, AttributeError):
                    pass
            subscription.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(user)

        # 如果是企业会员，同步更新企业的会员等级和到期时间
        if membership_tier:
            is_enterprise_tier = membership_tier in ["enterprise", "enterprise_pro", "enterprise_pro_max"]
            if is_enterprise_tier:
                # 如果是新升级到企业会员，创建企业记录
                if old_membership_type != "enterprise":
                    self._create_enterprise_for_user(db, user, membership_tier, expires_at)
                else:
                    # 如果已经是企业会员，更新企业的会员等级和到期时间
                    self._update_enterprise_tier(db, user, membership_tier, expires_at)
        elif expires_at:
            # 即使没有修改会员等级，也要同步更新企业的到期时间
            is_enterprise_tier = user.membership_type == "enterprise"
            if is_enterprise_tier:
                self._update_enterprise_subscription_end_date(db, user, expires_at)

        # TODO: 记录操作日志

        return {
            "user_id": str(user.id),
            "user_email": user.email,
            "old_tier": old_tier,
            "new_tier": membership_tier or old_tier,
            "old_expires_at": old_expires_at.isoformat() if old_expires_at else None,
            "new_expires_at": expires_at,
            "reason": reason
        }

    def _update_enterprise_tier(self, db: Session, user: User, tier: str, expires_at: Optional[str] = None):
        """更新企业的会员等级、配额和到期时间"""
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

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
                "subscription_start_date": datetime.utcnow()
            }

            # 如果提供了到期时间，同步更新企业的到期时间
            if expires_at:
                try:
                    end_date = datetime.fromisoformat(expires_at)
                    update_data["subscription_end_date"] = end_date
                    print(f"   - 订阅到期时间: {end_date.strftime('%Y-%m-%d')}")
                except (ValueError, AttributeError):
                    pass

            # 更新企业会员等级和配额
            enterprise_service.update_company(company.id, **update_data)

            print(f"✅ 同步更新企业 {company.name} 的会员等级为 {tier}")
            print(f"   - 员工配额: {tier_limits['max_employees']}")
            print(f"   - 工厂配额: {tier_limits['max_factories']}")
            print(f"   - WPS配额: {tier_limits['max_wps_records']}")
            print(f"   - PQR配额: {tier_limits['max_pqr_records']}")
        else:
            print(f"⚠️  用户 {user.email} 没有企业记录，创建新企业")
            self._create_enterprise_for_user(db, user, tier, expires_at)

    def _update_enterprise_subscription_end_date(self, db: Session, user: User, expires_at: str):
        """仅更新企业的订阅到期时间"""
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 获取用户的企业
        company = enterprise_service.get_company_by_owner(user.id)
        if company:
            try:
                end_date = datetime.fromisoformat(expires_at)
                enterprise_service.update_company(
                    company.id,
                    subscription_end_date=end_date
                )
                print(f"✅ 同步更新企业 {company.name} 的订阅到期时间为 {end_date.strftime('%Y-%m-%d')}")
            except (ValueError, AttributeError) as e:
                print(f"⚠️  更新企业订阅到期时间失败: {str(e)}")

    def _create_enterprise_for_user(self, db: Session, user: User, tier: str, expires_at: Optional[str] = None):
        """为用户创建企业和员工记录"""
        from app.services.enterprise_service import EnterpriseService

        enterprise_service = EnterpriseService(db)

        # 检查是否已有企业
        existing_company = enterprise_service.get_company_by_owner(user.id)
        if existing_company:
            # 如果已有企业，更新会员等级和到期时间
            update_data = {
                "membership_tier": tier,
                "subscription_status": "active",
                "subscription_start_date": datetime.utcnow()
            }

            # 如果提供了到期时间，同步更新
            if expires_at:
                try:
                    end_date = datetime.fromisoformat(expires_at)
                    update_data["subscription_end_date"] = end_date
                except (ValueError, AttributeError):
                    pass

            enterprise_service.update_company(existing_company.id, **update_data)
            print(f"✅ 更新企业 {existing_company.name} 的会员等级为 {tier}")
            return

        # 创建企业
        company_name = user.company or f"{user.full_name or user.email}的企业"

        # 准备创建企业的参数
        create_params = {
            "owner_id": user.id,
            "name": company_name,
            "membership_tier": tier,
            "contact_person": user.full_name,
            "contact_phone": user.phone,
            "contact_email": user.email
        }

        # 如果提供了到期时间，设置订阅到期时间
        if expires_at:
            try:
                end_date = datetime.fromisoformat(expires_at)
                create_params["subscription_end_date"] = end_date
            except (ValueError, AttributeError):
                pass

        company = enterprise_service.create_company(**create_params)
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

    def toggle_user_status(
        self,
        db: Session,
        user: User,
        is_active: bool,
        reason: str = "",
        current_admin: Admin = None
    ) -> Dict[str, Any]:
        """
        切换用户状态
        """
        # 记录状态变更
        old_status = user.is_active
        user.is_active = is_active
        user.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(user)

        # TODO: 记录操作日志

        action = "启用" if is_active else "禁用"

        return {
            "user_id": str(user.id),
            "user_email": user.email,
            "old_status": old_status,
            "new_status": is_active,
            "action": action,
            "reason": reason
        }

    def delete_user(
        self,
        db: Session,
        user: User,
        current_admin: Admin = None
    ) -> Dict[str, Any]:
        """
        删除用户
        """
        try:
            user_info = {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name
            }

            company_employees = db.query(CompanyEmployee).filter(
                CompanyEmployee.user_id == user.id
            ).all()

            if company_employees:
                for emp in company_employees:
                    db.delete(emp)
                db.flush()

            db.delete(user)
            db.commit()

            logger.info("Deleted user id=%s", user_info["id"])

            return {
                "deleted_user": user_info,
                "deleted_at": datetime.utcnow().isoformat()
            }
        except Exception:
            logger.exception("Failed to delete user id=%s", getattr(user, "id", None))
            db.rollback()
            raise

    def get_user_statistics(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取用户统计数据
        """
        base_query = db.query(User)

        # 应用日期筛选
        if start_date:
            base_query = base_query.filter(User.created_at >= start_date)
        if end_date:
            base_query = base_query.filter(User.created_at <= end_date)

        # 总用户数
        total_users = base_query.count()

        # 新增用户数（在指定时间范围内）
        if start_date or end_date:
            new_users_query = db.query(User)
            if start_date:
                new_users_query = new_users_query.filter(User.created_at >= start_date)
            if end_date:
                new_users_query = new_users_query.filter(User.created_at <= end_date)
            new_users = new_users_query.count()
        else:
            # 默认统计最近30天的新增用户
            recent_date = datetime.utcnow() - timedelta(days=30)
            new_users = db.query(User).filter(User.created_at >= recent_date).count()

        # 活跃用户数（最近30天有登录）
        active_date = datetime.utcnow() - timedelta(days=30)
        active_users = db.query(User).filter(
            and_(
                User.last_login_at >= active_date if hasattr(User, 'last_login_at') else False,
                User.is_active == True
            )
        ).count()

        # 按会员等级统计
        try:
            tier_stats = db.execute(text("""
                SELECT member_tier, COUNT(id) as count
                FROM users
                WHERE is_active = TRUE
                GROUP BY member_tier
            """)).fetchall()
            by_tier = {tier: count for tier, count in tier_stats}
        except Exception:
            # 如果member_tier字段不存在，使用默认值
            all_users = db.query(User).filter(User.is_active == True).all()
            by_tier = {"free": len(all_users)}

        # 按状态统计
        active_count = db.query(User).filter(User.is_active == True).count()
        inactive_count = db.query(User).filter(User.is_active == False).count()

        # 增长率计算
        growth_rate = round((new_users / total_users * 100), 2) if total_users > 0 else 0

        # 趋势数据（简化版）
        trend = []
        if start_date and end_date:
            # 生成日期范围内的趋势数据
            current_date = start_date
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                count = db.query(User).filter(
                    and_(
                        User.created_at >= current_date,
                        User.created_at < next_date
                    )
                ).count()
                trend.append({
                    "date": current_date.isoformat(),
                    "count": count
                })
                current_date = next_date
        else:
            # 默认返回最近7天的趋势
            for i in range(7):
                date_point = datetime.utcnow() - timedelta(days=6-i)
                next_date = date_point + timedelta(days=1)
                count = db.query(User).filter(
                    and_(
                        User.created_at >= date_point,
                        User.created_at < next_date
                    )
                ).count()
                trend.append({
                    "date": date_point.date().isoformat(),
                    "count": count
                })

        return {
            "total_users": total_users,
            "new_users": new_users,
            "active_users": active_users,
            "inactive_users": inactive_count,
            "by_tier": by_tier,
            "by_status": {
                "active": active_count,
                "inactive": inactive_count
            },
            "growth_rate": growth_rate,
            "trend": trend
        }

    def get_subscription_statistics(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取订阅统计数据
        """
        base_query = db.query(User)

        # 应用日期筛选
        if start_date:
            base_query = base_query.filter(User.created_at >= start_date)
        if end_date:
            base_query = base_query.filter(User.created_at <= end_date)

        # 总用户数（用于计算转化率）
        try:
            total_users = base_query.count()
        except Exception:
            total_users = 0

        # 总订阅数（非免费用户）
        try:
            total_subscriptions = base_query.filter(text("member_tier != 'free'")).count()
        except Exception:
            # 如果member_tier字段不存在，返回0
            total_subscriptions = 0

        # 活跃订阅数
        try:
            active_subscriptions = base_query.filter(
                and_(
                    text("member_tier != 'free'"),
                    User.is_active == True
                )
            ).count()
        except Exception:
            active_subscriptions = 0

        # 新增订阅数（在指定时间范围内）
        if start_date or end_date:
            new_subscriptions_query = db.query(User)
            if start_date:
                new_subscriptions_query = new_subscriptions_query.filter(User.created_at >= start_date)
            if end_date:
                new_subscriptions_query = new_subscriptions_query.filter(User.created_at <= end_date)
            try:
                new_subscriptions = new_subscriptions_query.filter(text("member_tier != 'free'")).count()
            except Exception:
                new_subscriptions = 0
        else:
            # 默认统计最近30天的新增订阅
            recent_date = datetime.utcnow() - timedelta(days=30)
            try:
                new_subscriptions = db.query(User).filter(
                    and_(
                        User.created_at >= recent_date,
                        text("member_tier != 'free'")
                    )
                ).count()
            except Exception:
                new_subscriptions = 0

        # 按订阅类型统计
        try:
            subscription_stats = db.execute(text("""
                SELECT member_tier, COUNT(id) as count
                FROM users
                WHERE is_active = TRUE AND member_tier != 'free'
                GROUP BY member_tier
            """)).fetchall()
            by_type = {tier: count for tier, count in subscription_stats}
        except Exception:
            # 如果查询失败，返回空统计
            by_type = {}

        # 订阅状态分布
        try:
            status_stats = db.execute(text("""
                SELECT
                    CASE
                        WHEN member_tier = 'free' THEN 'free'
                        WHEN member_tier LIKE 'enterprise%' THEN 'enterprise'
                        WHEN member_tier LIKE 'personal%' THEN 'personal'
                        ELSE 'other'
                    END as category,
                    COUNT(id) as count
                FROM users
                WHERE is_active = TRUE
                GROUP BY category
            """)).fetchall()
            by_status = {status: count for status, count in status_stats}
        except Exception:
            by_status = {"free": total_subscriptions, "personal": 0, "enterprise": 0}

        # 收入统计 - 从实际交易记录计算
        from app.models.subscription import SubscriptionTransaction, Subscription
        from app.models.company import CompanyEmployee, Company

        # 获取所有继承会员的用户ID（企业员工但不是企业所有者）
        try:
            inherited_user_ids_subquery = db.query(CompanyEmployee.user_id).join(
                Company, CompanyEmployee.company_id == Company.id
            ).filter(
                and_(
                    CompanyEmployee.status == "active",
                    CompanyEmployee.user_id != Company.owner_id
                )
            ).subquery()
        except Exception:
            # 如果表不存在，使用空子查询
            inherited_user_ids_subquery = db.query(User.id).filter(User.id == -1).subquery()

        # 总收入 - 只计算付费用户的成功交易
        try:
            total_revenue = db.query(
                func.sum(SubscriptionTransaction.amount)
            ).join(
                Subscription, SubscriptionTransaction.subscription_id == Subscription.id
            ).filter(
                and_(
                    SubscriptionTransaction.status == "success",
                    ~Subscription.user_id.in_(inherited_user_ids_subquery)
                )
            ).scalar() or 0
        except Exception:
            total_revenue = 0

        # 本月收入 - 只计算付费用户的成功交易
        try:
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_revenue = db.query(
                func.sum(SubscriptionTransaction.amount)
            ).join(
                Subscription, SubscriptionTransaction.subscription_id == Subscription.id
            ).filter(
                and_(
                    SubscriptionTransaction.status == "success",
                    SubscriptionTransaction.transaction_date >= current_month_start,
                    ~Subscription.user_id.in_(inherited_user_ids_subquery)
                )
            ).scalar() or 0
        except Exception:
            monthly_revenue = 0

        # 年收入估算（本月收入 × 12）
        annual_revenue = monthly_revenue * 12

        # 统计继承会员数量
        try:
            inherited_members_count = db.query(User).filter(
                and_(
                    User.is_active == True,
                    User.id.in_(inherited_user_ids_subquery)
                )
            ).count()
        except Exception:
            inherited_members_count = 0

        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "new_subscriptions": new_subscriptions,
            "cancelled_subscriptions": 0,  # 需要从订单表或取消记录表中获取
            "revenue": {
                "monthly": float(monthly_revenue),
                "annual": float(annual_revenue),
                "total": float(total_revenue)
            },
            "by_type": by_type,
            "by_status": by_status,
            "conversion_rate": round((active_subscriptions / total_users * 100), 2) if total_users > 0 else 0,
            "churn_rate": 0,  # 需要实际计算
            "average_revenue_per_user": round((monthly_revenue / active_subscriptions), 2) if active_subscriptions > 0 else 0,
            "inherited_members_count": inherited_members_count
        }

    def _format_user_data(self, user: User, detailed: bool = False) -> Dict[str, Any]:
        """格式化用户数据"""
        from app.models.company import CompanyEmployee, Company
        from sqlalchemy.orm import object_session

        # 安全获取用户属性
        membership_tier = getattr(user, 'member_tier', 'free')
        membership_type = getattr(user, 'membership_type', 'personal')
        last_login_at = getattr(user, 'last_login_at', None)
        phone = getattr(user, 'phone', None)
        company = getattr(user, 'company', None)
        full_name = getattr(user, 'full_name', '')
        subscription_expires_at = getattr(user, 'subscription_expires_at', None)
        wps_quota_used = getattr(user, 'wps_quota_used', 0)
        pqr_quota_used = getattr(user, 'pqr_quota_used', 0)
        ppqr_quota_used = getattr(user, 'ppqr_quota_used', 0)
        storage_quota_used = getattr(user, 'storage_quota_used', 0)

        import json
        # 获取用户权限
        permissions = getattr(user, 'permissions', None)
        if permissions:
            try:
                parsed_permissions = json.loads(permissions)
            except json.JSONDecodeError:
                parsed_permissions = {}
        else:
            parsed_permissions = {}

        # 检查用户是否通过企业继承会员权限
        is_inherited_from_company = False
        company_name = None

        # 如果用户是企业会员类型，检查是否是企业员工（非企业所有者）
        if membership_type == "enterprise":
            db = object_session(user)
            if db:
                # 查询用户是否是某个企业的员工
                employee = db.query(CompanyEmployee).filter(
                    CompanyEmployee.user_id == user.id,
                    CompanyEmployee.status == "active"
                ).first()

                if employee:
                    # 获取企业信息
                    company_obj = db.query(Company).filter(Company.id == employee.company_id).first()
                    if company_obj:
                        # 如果用户不是企业所有者，说明是通过企业继承的会员权限
                        if company_obj.owner_id != user.id:
                            is_inherited_from_company = True
                            company_name = company_obj.name

        user_data = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": full_name,
            "membership_tier": membership_tier,
            "membership_type": membership_type,
            "is_active": user.is_active,
            "is_admin": getattr(user, 'is_superuser', False),
            "is_verified": getattr(user, 'is_verified', False),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login_at": last_login_at.isoformat() if last_login_at else None,
            "phone": phone,
            "company": company,
            "subscription_expires_at": subscription_expires_at.isoformat() if subscription_expires_at else None,
            "is_inherited_from_company": is_inherited_from_company,
            "company_name": company_name,
            "quotas": {
                "wps_limit": self._get_wps_limit(membership_tier),
                "pqr_limit": self._get_pqr_limit(membership_tier),
                "ppqr_limit": self._get_ppqr_limit(membership_tier),
                "current_wps": wps_quota_used,
                "current_pqr": pqr_quota_used,
                "current_ppqr": ppqr_quota_used,
                "storage_used": storage_quota_used  # MB
            },
            "permissions": parsed_permissions
        }

        if detailed:
            # 添加详细信息字段
            user_data.update({
                "auto_renewal": getattr(user, 'auto_renewal', False),
                "subscription_status": getattr(user, 'subscription_status', 'inactive'),
                "subscription_start_date": getattr(user, 'subscription_start_date', None),
                "last_login_ip": getattr(user, 'last_login_ip', None),
            })

        return user_data

    def _get_wps_limit(self, tier: str) -> int:
        """根据会员等级获取WPS限制"""
        limits = {
            "personal_free": 10,
            "personal_pro": 30,
            "personal_advanced": 50,
            "personal_flagship": 100,
            "enterprise": 200,
            "enterprise_pro": 400,
            "enterprise_pro_max": 500
        }
        return limits.get(tier, 10)

    def _get_pqr_limit(self, tier: str) -> int:
        """根据会员等级获取PQR限制"""
        limits = {
            "personal_free": 10,
            "personal_pro": 30,
            "personal_advanced": 50,
            "personal_flagship": 100,
            "enterprise": 200,
            "enterprise_pro": 400,
            "enterprise_pro_max": 500
        }
        return limits.get(tier, 10)

    def _get_ppqr_limit(self, tier: str) -> int:
        """根据会员等级获取pPQR限制"""
        limits = {
            "personal_free": 0,
            "personal_pro": 30,
            "personal_advanced": 50,
            "personal_flagship": 100,
            "enterprise": 200,
            "enterprise_pro": 400,
            "enterprise_pro_max": 500
        }
        return limits.get(tier, 0)

    def _get_permissions_by_tier(self, tier: str) -> str:
        """根据会员等级获取功能权限"""
        import json

        permissions_config = {
            "personal_free": {
                "wps_management": True,
                "pqr_management": True,
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
            },
            "personal_pro": {
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "equipment_management": False,
                "production_management": False,
                "quality_management": False,
                "materials_management": True,
                "welders_management": True,
                "employee_management": False,
                "multi_factory_management": False,
                "reports_management": False,
                "api_access": True
            },
            "personal_advanced": {
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "equipment_management": True,
                "production_management": True,
                "quality_management": True,
                "materials_management": True,
                "welders_management": True,
                "employee_management": False,
                "multi_factory_management": False,
                "reports_management": True,
                "api_access": True
            },
            "personal_flagship": {
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "equipment_management": True,
                "production_management": True,
                "quality_management": True,
                "materials_management": True,
                "welders_management": True,
                "employee_management": False,
                "multi_factory_management": False,
                "reports_management": True,
                "api_access": True
            },
            "enterprise": {
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "equipment_management": True,
                "production_management": True,
                "quality_management": True,
                "materials_management": True,
                "welders_management": True,
                "employee_management": True,
                "multi_factory_management": True,
                "reports_management": True,
                "api_access": True
            },
            "enterprise_pro": {
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "equipment_management": True,
                "production_management": True,
                "quality_management": True,
                "materials_management": True,
                "welders_management": True,
                "employee_management": True,
                "multi_factory_management": True,
                "reports_management": True,
                "api_access": True
            },
            "enterprise_pro_max": {
                "wps_management": True,
                "pqr_management": True,
                "ppqr_management": True,
                "equipment_management": True,
                "production_management": True,
                "quality_management": True,
                "materials_management": True,
                "welders_management": True,
                "employee_management": True,
                "multi_factory_management": True,
                "reports_management": True,
                "api_access": True
            }
        }

        return json.dumps(permissions_config.get(tier, permissions_config["personal_free"]))

    def get_enterprise_users(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取企业用户列表
        从 companies 表获取真实的企业数据，包括企业信息和员工信息
        """
        from app.models.company import Company, CompanyEmployee

        # 查询所有企业
        companies_query = db.query(Company).filter(Company.is_active == True)

        # 应用搜索筛选
        if search:
            # 关联 User 表进行搜索
            companies_query = companies_query.join(User, Company.owner_id == User.id)
            search_filter = or_(
                Company.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            companies_query = companies_query.filter(search_filter)

        # 获取总数
        total = companies_query.count()

        # 分页
        skip = (page - 1) * page_size
        companies = companies_query.offset(skip).limit(page_size).all()

        # 格式化企业数据
        companies_list = []
        total_employees = 0

        for company in companies:
            # 获取企业所有者信息
            owner = db.query(User).filter(User.id == company.owner_id).first()

            # 获取企业员工列表
            employees = db.query(CompanyEmployee).filter(
                CompanyEmployee.company_id == company.id,
                CompanyEmployee.status == "active"
            ).all()

            # 格式化员工数据
            members_list = []
            for emp in employees:
                emp_user = db.query(User).filter(User.id == emp.user_id).first()
                if emp_user:
                    member_data = {
                        "id": str(emp_user.id),
                        "username": emp_user.username,
                        "email": emp_user.email,
                        "full_name": emp_user.full_name,
                        "role": emp.role,  # admin, manager, employee
                        "is_active": emp_user.is_active,
                        "position": emp.position,
                        "department": emp.department,
                        "employee_number": emp.employee_number
                    }
                    members_list.append(member_data)

            total_employees += len(members_list)

            # 格式化企业数据
            company_data = {
                "company_id": str(company.id),
                "company_name": company.name,
                "admin_user": {
                    "id": str(owner.id) if owner else None,
                    "username": owner.username if owner else "N/A",
                    "email": owner.email if owner else "N/A",
                    "full_name": owner.full_name if owner else "N/A",
                    "is_active": owner.is_active if owner else False,
                    "membership_tier": owner.member_tier if owner else "free",
                    "membership_type": owner.membership_type if owner else "personal"
                },
                "members": members_list,
                "membership_tier": company.membership_tier,
                "subscription_status": company.subscription_status,
                "max_employees": company.max_employees,
                "max_factories": company.max_factories,
                "created_at": company.created_at.isoformat() if company.created_at else None
            }
            companies_list.append(company_data)

        return {
            "items": companies_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "summary": {
                "total_companies": total,
                "total_enterprise_users": total_employees
            }
        }

    def get_subscription_users(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取订阅管理用户列表
        只显示非免费版和非企业版会员
        """
        # 获取付费个人用户（非免费且非企业）
        paid_users_query = db.query(User).filter(
            and_(
                User.is_active == True,
                text("member_tier != 'free'"),
                text("member_tier != 'enterprise'"),
                or_(
                    text("member_tier LIKE 'personal_%'"),
                    text("member_tier IN ('personal_pro', 'personal_advanced', 'personal_flagship')")
                )
            )
        )

        # 应用搜索筛选
        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%")
            )
            paid_users_query = paid_users_query.filter(search_filter)

        # 按创建时间排序
        paid_users_query = paid_users_query.order_by(User.created_at.desc())

        # 总数统计
        total = paid_users_query.count()

        # 分页查询
        offset = (page - 1) * page_size
        users = paid_users_query.offset(offset).limit(page_size).all()

        # 转换为响应格式
        user_items = []
        for user in users:
            user_data = self._format_user_data(user, detailed=True)
            # 添加订阅相关信息
            user_data["subscription_info"] = {
                "tier": getattr(user, 'member_tier', 'free'),
                "type": getattr(user, 'membership_type', 'personal'),
                "status": getattr(user, 'subscription_status', 'active'),
                "expires_at": getattr(user, 'subscription_expires_at', None),
                "auto_renewal": getattr(user, 'auto_renewal', False)
            }
            user_items.append(user_data)

        # 按会员等级分组统计
        tier_counts = {}
        for user in users:
            tier = getattr(user, 'member_tier', 'free')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        return {
            "items": user_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "summary": {
                "total_paid_users": total,
                "tier_distribution": tier_counts
            }
        }


# 创建服务实例
admin_user_service = AdminUserService()
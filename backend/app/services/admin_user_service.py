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
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.admin import Admin
from app.models.company import Company, CompanyEmployee

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

    def list_admins(self, db: Session) -> Dict[str, Any]:
        """列出管理端账号，不返回密码哈希。"""
        admins = db.query(Admin).order_by(Admin.id.asc()).all()
        items = []
        for admin in admins:
            permissions = admin.permissions
            if permissions is None:
                permissions = ["all"] if admin.is_super_admin else []
            elif isinstance(permissions, dict):
                permissions = [key for key, enabled in permissions.items() if enabled]
            elif not isinstance(permissions, list):
                permissions = []
            role = "super_admin" if admin.is_super_admin else (admin.admin_level or "admin")
            items.append({
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "full_name": admin.full_name,
                "role": role,
                "permissions": permissions,
                "status": "active" if admin.is_active else "inactive",
                "last_login_at": admin.last_login_at.isoformat() if admin.last_login_at else None,
                "created_at": admin.created_at.isoformat() if admin.created_at else None,
            })
        return {
            "items": items,
            "total": len(items),
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

        end_date = None
        if expires_at:
            try:
                # 兼容 YYYY-MM-DD 与完整 ISO
                raw = expires_at.replace("Z", "+00:00") if isinstance(expires_at, str) else expires_at
                end_date = datetime.fromisoformat(raw) if isinstance(raw, str) else raw
                if end_date.tzinfo is not None:
                    end_date = end_date.replace(tzinfo=None)
                # 日期-only 视为当天结束
                if isinstance(expires_at, str) and len(expires_at) <= 10:
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                user.subscription_end_date = end_date
                user.subscription_expires_at = end_date
            except (ValueError, AttributeError, TypeError):
                end_date = None

        # 付费档默认激活；免费档清除状态
        try:
            if membership_tier in (None, "free", "personal_free"):
                if membership_tier in ("free", "personal_free"):
                    user.subscription_status = "inactive"
            else:
                if end_date:
                    user.subscription_status = "active" if end_date > datetime.utcnow() else "expired"
                else:
                    user.subscription_status = "active"
        except AttributeError:
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

        # 同步 / 补建订阅记录（管理员授会也要在订阅管理可见）
        now = datetime.utcnow()
        subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == user.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )
        paid_tier = membership_tier and membership_tier not in ("free", "personal_free")
        if paid_tier:
            sub_end = end_date or (now + timedelta(days=30))
            sub_status = "active" if sub_end > now else "expired"
            if subscription:
                if membership_tier:
                    subscription.plan_id = membership_tier
                if end_date:
                    subscription.end_date = end_date
                subscription.status = sub_status
                subscription.updated_at = now
            else:
                subscription = Subscription(
                    user_id=user.id,
                    plan_id=membership_tier,
                    status=sub_status,
                    billing_cycle="yearly",
                    price=0,
                    currency="CNY",
                    start_date=now,
                    end_date=sub_end,
                    auto_renew=False,
                    payment_method="admin_grant",
                )
                db.add(subscription)
        elif subscription and membership_tier in ("free", "personal_free"):
            subscription.status = "cancelled"
            subscription.updated_at = now

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
        删除用户。会先清理订阅/员工/通知已读等直接依赖；
        若为企业所有者或仍有业务外键引用，抛出明确错误（建议改用禁用）。
        """
        from app.models.subscription import Subscription, SubscriptionTransaction
        from app.models.user_notification import UserNotificationReadStatus

        user_info = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
        }

        owned_company = db.query(Company).filter(Company.owner_id == user.id).first()
        if owned_company:
            raise ValueError(
                f"该用户是企业「{owned_company.name}」的所有者，无法直接删除。"
                "请先转移企业归属，或改用「禁用」账号。"
            )

        try:
            # 员工关系
            for emp in db.query(CompanyEmployee).filter(CompanyEmployee.user_id == user.id).all():
                db.delete(emp)

            # 订阅及交易
            subscriptions = db.query(Subscription).filter(Subscription.user_id == user.id).all()
            for sub in subscriptions:
                for tx in db.query(SubscriptionTransaction).filter(
                    SubscriptionTransaction.subscription_id == sub.id
                ).all():
                    db.delete(tx)
                db.delete(sub)

            # 通知已读状态
            for row in db.query(UserNotificationReadStatus).filter(
                UserNotificationReadStatus.user_id == user.id
            ).all():
                db.delete(row)

            db.flush()
            db.delete(user)
            db.commit()

            logger.info("Deleted user id=%s", user_info["id"])
            return {
                "deleted_user": user_info,
                "deleted_at": datetime.utcnow().isoformat(),
            }
        except ValueError:
            db.rollback()
            raise
        except IntegrityError:
            db.rollback()
            logger.exception("Integrity error deleting user id=%s", user_info["id"])
            raise ValueError(
                "该用户仍有业务数据引用（如项目/单据创建人），无法硬删除。"
                "请改用「禁用」账号。"
            )
        except Exception:
            logger.exception("Failed to delete user id=%s", user_info["id"])
            db.rollback()
            raise

    def get_user_statistics(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取用户统计数据。
        - total_users: 当前启用账号总数（不受区间限制）
        - new_users: 区间内新注册
        - growth_rate: 相对区间起点存量的增长率
        - active_users: 近 30 天有登录
        - inactive_users: 启用但近 30 天未登录
        """
        if not end_date:
            end_date = datetime.utcnow().date()
        if not start_date:
            start_date = end_date - timedelta(days=29)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        # 总启用用户（当前快照）
        total_users = db.query(User).filter(User.is_active == True).count()  # noqa: E712
        disabled_users = db.query(User).filter(User.is_active == False).count()  # noqa: E712

        # 区间内新增
        new_users = db.query(User).filter(
            and_(User.created_at >= start_dt, User.created_at <= end_dt)
        ).count()

        # 区间起点之前的存量（用于增长率）
        users_before = db.query(User).filter(User.created_at < start_dt).count()
        growth_rate = (
            round((new_users / users_before) * 100, 2) if users_before > 0 else (100.0 if new_users > 0 else 0.0)
        )

        # 近 30 天活跃（登录口径，与区间筛选独立）
        active_cutoff = datetime.utcnow() - timedelta(days=30)
        active_users = db.query(User).filter(
            and_(
                User.is_active == True,  # noqa: E712
                User.last_login_at >= active_cutoff,
            )
        ).count()
        # 启用但久未登录
        inactive_users = max(total_users - active_users, 0)

        # 等级分布
        try:
            tier_stats = db.execute(text("""
                SELECT COALESCE(member_tier, 'free') AS member_tier, COUNT(id) AS count
                FROM users
                WHERE is_active = TRUE
                GROUP BY COALESCE(member_tier, 'free')
            """)).fetchall()
            by_tier = {tier: count for tier, count in tier_stats}
        except Exception:
            by_tier = {"free": total_users}

        # 每日新增 / 登录活跃（聚合一次）；累计用「起点存量 + 逐日新增」
        new_rows = db.execute(
            text("""
                SELECT DATE(created_at) AS d, COUNT(*) AS c
                FROM users
                WHERE created_at >= :start_dt AND created_at <= :end_dt
                GROUP BY DATE(created_at)
            """),
            {"start_dt": start_dt, "end_dt": end_dt},
        ).fetchall()
        new_map = {str(r[0]): int(r[1]) for r in new_rows}

        active_rows = db.execute(
            text("""
                SELECT DATE(last_login_at) AS d, COUNT(*) AS c
                FROM users
                WHERE is_active = TRUE
                  AND last_login_at IS NOT NULL
                  AND last_login_at >= :start_dt AND last_login_at <= :end_dt
                GROUP BY DATE(last_login_at)
            """),
            {"start_dt": start_dt, "end_dt": end_dt},
        ).fetchall()
        active_map = {str(r[0]): int(r[1]) for r in active_rows}

        # 起点前启用用户存量
        cumulative_base = db.query(User).filter(
            and_(
                User.is_active == True,  # noqa: E712
                User.created_at < start_dt,
            )
        ).count()

        trend = []
        current = start_date
        running = cumulative_base
        max_days = 366
        day_count = 0
        while current <= end_date and day_count < max_days:
            key = current.isoformat()
            new_count = new_map.get(key, 0)
            running += new_count
            trend.append({
                "date": key,
                "count": new_count,
                "new_users": new_count,
                "active_users": active_map.get(key, 0),
                "total_users": running,
            })
            current = current + timedelta(days=1)
            day_count += 1

        return {
            "total_users": total_users,
            "new_users": new_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "disabled_users": disabled_users,
            "by_tier": by_tier,
            "by_status": {
                "active": active_users,
                "inactive": inactive_users,
                "disabled": disabled_users,
            },
            "growth_rate": growth_rate,
            "trend": trend,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        }

    def get_subscription_statistics(
        self,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取订阅统计数据（基于 Subscription / 交易，排除企业继承员工）。
        """
        from app.models.subscription import SubscriptionTransaction, Subscription
        from app.models.company import Company

        if not end_date:
            end_date = datetime.utcnow().date()
        if not start_date:
            start_date = end_date - timedelta(days=29)

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        try:
            inherited_user_ids_subquery = db.query(CompanyEmployee.user_id).join(
                Company, CompanyEmployee.company_id == Company.id
            ).filter(
                and_(
                    CompanyEmployee.status == "active",
                    CompanyEmployee.user_id != Company.owner_id,
                )
            ).subquery()
        except Exception:
            inherited_user_ids_subquery = db.query(User.id).filter(User.id == -1).subquery()

        paid_base = db.query(Subscription).filter(
            ~Subscription.user_id.in_(inherited_user_ids_subquery)
        )

        total_subscriptions = paid_base.count()
        active_subscriptions = paid_base.filter(Subscription.status == "active").count()

        # 区间内新建 / 取消
        new_subscriptions = paid_base.filter(
            and_(Subscription.created_at >= start_dt, Subscription.created_at <= end_dt)
        ).count()

        cancelled_q = paid_base.filter(Subscription.status.in_(["cancelled", "canceled", "expired"]))
        # 优先用 updated_at 落入区间；若无更新时间则回退全量 cancelled 计数
        try:
            cancelled_in_period = cancelled_q.filter(
                and_(Subscription.updated_at >= start_dt, Subscription.updated_at <= end_dt)
            ).count()
        except Exception:
            cancelled_in_period = cancelled_q.count()

        cancelled_total = cancelled_q.count()

        # 流失率：区间取消 / (当前活跃 + 区间取消) 近似期初活跃
        churn_base = max(active_subscriptions + cancelled_in_period, 1)
        churn_rate = round((cancelled_in_period / churn_base) * 100, 2) if cancelled_in_period else 0.0

        # 按会员等级（用户表）分布 — 前端仍用 by_type 展示
        try:
            subscription_stats = db.execute(text("""
                SELECT COALESCE(member_tier, 'free') AS member_tier, COUNT(id) AS count
                FROM users
                WHERE is_active = TRUE AND COALESCE(member_tier, 'free') != 'free'
                GROUP BY COALESCE(member_tier, 'free')
            """)).fetchall()
            by_type = {tier: count for tier, count in subscription_stats}
        except Exception:
            by_type = {}

        # 收入
        try:
            total_revenue = db.query(
                func.sum(SubscriptionTransaction.amount)
            ).join(
                Subscription, SubscriptionTransaction.subscription_id == Subscription.id
            ).filter(
                and_(
                    SubscriptionTransaction.status == "success",
                    ~Subscription.user_id.in_(inherited_user_ids_subquery),
                )
            ).scalar() or 0
        except Exception:
            total_revenue = 0

        try:
            monthly_revenue = db.query(
                func.sum(SubscriptionTransaction.amount)
            ).join(
                Subscription, SubscriptionTransaction.subscription_id == Subscription.id
            ).filter(
                and_(
                    SubscriptionTransaction.status == "success",
                    SubscriptionTransaction.transaction_date >= start_dt,
                    SubscriptionTransaction.transaction_date <= end_dt,
                    ~Subscription.user_id.in_(inherited_user_ids_subquery),
                )
            ).scalar() or 0
        except Exception:
            monthly_revenue = 0

        # 年累计收入（近 365 天实收，而非月×12）
        year_start = datetime.utcnow() - timedelta(days=365)
        try:
            annual_revenue = db.query(
                func.sum(SubscriptionTransaction.amount)
            ).join(
                Subscription, SubscriptionTransaction.subscription_id == Subscription.id
            ).filter(
                and_(
                    SubscriptionTransaction.status == "success",
                    SubscriptionTransaction.transaction_date >= year_start,
                    ~Subscription.user_id.in_(inherited_user_ids_subquery),
                )
            ).scalar() or 0
        except Exception:
            annual_revenue = float(monthly_revenue)

        try:
            inherited_members_count = db.query(User).filter(
                and_(
                    User.is_active == True,  # noqa: E712
                    User.id.in_(inherited_user_ids_subquery),
                )
            ).count()
        except Exception:
            inherited_members_count = 0

        total_users = db.query(User).filter(User.is_active == True).count()  # noqa: E712

        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "new_subscriptions": new_subscriptions,
            "cancelled_subscriptions": cancelled_in_period,
            "cancelled_subscriptions_total": cancelled_total,
            "revenue": {
                "monthly": float(monthly_revenue),
                "period": float(monthly_revenue),
                "annual": float(annual_revenue),
                "total": float(total_revenue),
            },
            "by_type": by_type,
            "by_status": {
                "active": active_subscriptions,
                "cancelled": cancelled_total,
            },
            "conversion_rate": round((active_subscriptions / total_users * 100), 2) if total_users > 0 else 0,
            "churn_rate": churn_rate,
            "average_revenue_per_user": (
                round((float(monthly_revenue) / active_subscriptions), 2) if active_subscriptions > 0 else 0
            ),
            "inherited_members_count": inherited_members_count,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        }

    def _format_user_data(self, user: User, detailed: bool = False) -> Dict[str, Any]:
        """格式化用户数据"""
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

        # 检查用户是否通过企业继承会员权限，并解析关联企业 ID
        is_inherited_from_company = False
        company_name = None
        company_id = None

        db = object_session(user)
        if db:
            owned = db.query(Company).filter(Company.owner_id == user.id).first()
            if owned:
                company_id = str(owned.id)
                company_name = owned.name
            elif membership_type == "enterprise":
                employee = db.query(CompanyEmployee).filter(
                    CompanyEmployee.user_id == user.id,
                    CompanyEmployee.status == "active",
                ).first()
                if employee:
                    company_obj = db.query(Company).filter(Company.id == employee.company_id).first()
                    if company_obj:
                        company_id = str(company_obj.id)
                        company_name = company_obj.name
                        if company_obj.owner_id != user.id:
                            is_inherited_from_company = True

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
            "company_id": company_id,
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

    def get_enterprise_by_id(self, db: Session, company_id: str) -> Optional[Dict[str, Any]]:
        """按企业 ID 获取详情（含管理员与员工列表）。"""
        try:
            cid = int(company_id)
        except (TypeError, ValueError):
            raise ValueError("无效的企业ID格式")

        company = db.query(Company).filter(Company.id == cid).first()
        if not company:
            return None

        owner = db.query(User).filter(User.id == company.owner_id).first()
        employees = db.query(CompanyEmployee).filter(
            CompanyEmployee.company_id == company.id,
            CompanyEmployee.status == "active",
        ).all()

        members_list = []
        for emp in employees:
            emp_user = db.query(User).filter(User.id == emp.user_id).first()
            if emp_user:
                members_list.append({
                    "id": str(emp_user.id),
                    "username": emp_user.username,
                    "email": emp_user.email,
                    "full_name": emp_user.full_name,
                    "role": emp.role,
                    "is_active": emp_user.is_active,
                    "position": emp.position,
                    "department": emp.department,
                    "employee_number": emp.employee_number,
                })

        return {
            "company_id": str(company.id),
            "company_name": company.name,
            "admin_user": {
                "id": str(owner.id) if owner else None,
                "username": owner.username if owner else "N/A",
                "email": owner.email if owner else "N/A",
                "full_name": owner.full_name if owner else "N/A",
                "is_active": owner.is_active if owner else False,
                "membership_tier": owner.member_tier if owner else "free",
                "membership_type": owner.membership_type if owner else "personal",
                "subscription_expires_at": (
                    owner.subscription_expires_at.isoformat()
                    if owner and getattr(owner, "subscription_expires_at", None)
                    else None
                ),
            },
            "members": members_list,
            "membership_tier": company.membership_tier,
            "subscription_status": company.subscription_status,
            "subscription_end_date": (
                company.subscription_end_date.isoformat()
                if getattr(company, "subscription_end_date", None)
                else None
            ),
            "max_employees": company.max_employees,
            "max_factories": company.max_factories,
            "created_at": company.created_at.isoformat() if company.created_at else None,
        }

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
        # 查询所有企业
        companies_query = db.query(Company).filter(Company.is_active == True)  # noqa: E712

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
            detail = self.get_enterprise_by_id(db, str(company.id))
            if detail:
                total_employees += len(detail.get("members") or [])
                companies_list.append(detail)

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
        search: Optional[str] = None,
        membership_type: Optional[str] = None,
        membership_tier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取订阅管理用户列表：所有非免费付费档（个人 + 企业）。
        含管理员直接授会的 enterprise_pro_max 等高等级。
        """
        free_tiers = ["free", "personal_free", ""]

        paid_users_query = db.query(User).filter(
            and_(
                User.is_active == True,  # noqa: E712
                User.member_tier.isnot(None),
                ~User.member_tier.in_(free_tiers),
            )
        )

        if membership_type in ("personal", "enterprise"):
            paid_users_query = paid_users_query.filter(User.membership_type == membership_type)

        if membership_tier:
            paid_users_query = paid_users_query.filter(User.member_tier == membership_tier)

        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
            )
            paid_users_query = paid_users_query.filter(search_filter)

        paid_users_query = paid_users_query.order_by(User.created_at.desc())

        total = paid_users_query.count()
        offset = (page - 1) * page_size
        users = paid_users_query.offset(offset).limit(page_size).all()

        user_items = []
        for user in users:
            user_data = self._format_user_data(user, detailed=True)
            expires = getattr(user, "subscription_expires_at", None) or getattr(
                user, "subscription_end_date", None
            )
            status = getattr(user, "subscription_status", None) or "inactive"
            # 到期时间在未来但状态未激活时，展示为 active（兼容历史脏数据）
            if expires and isinstance(expires, datetime) and expires > datetime.utcnow():
                if status in (None, "", "inactive"):
                    status = "active"
            elif expires and isinstance(expires, datetime) and expires <= datetime.utcnow():
                status = "expired"

            user_data["subscription_info"] = {
                "tier": getattr(user, "member_tier", "free"),
                "type": getattr(user, "membership_type", "personal"),
                "status": status,
                "expires_at": expires.isoformat() if expires else None,
                "auto_renewal": getattr(user, "auto_renewal", False),
            }
            user_items.append(user_data)

        # 全量等级分布与付费总数（不受列表筛选影响）
        base_paid = db.query(User).filter(
            and_(
                User.is_active == True,  # noqa: E712
                User.member_tier.isnot(None),
                ~User.member_tier.in_(free_tiers),
            )
        )
        total_paid_users = base_paid.count()
        tier_rows = (
            db.query(User.member_tier, func.count(User.id))
            .filter(
                and_(
                    User.is_active == True,  # noqa: E712
                    User.member_tier.isnot(None),
                    ~User.member_tier.in_(free_tiers),
                )
            )
            .group_by(User.member_tier)
            .all()
        )
        tier_counts = {tier: count for tier, count in tier_rows}

        return {
            "items": user_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
            "summary": {
                "total_paid_users": total_paid_users,
                "tier_distribution": tier_counts,
            },
        }


# 创建服务实例
admin_user_service = AdminUserService()
"""
System service for monitoring and statistics.
"""
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.user import User
from app.models.subscription import Subscription, SubscriptionTransaction
from app.models.system_log import SystemLog
from app.models.system_announcement import SystemAnnouncement


class SystemService:
    """系统监控和统计服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态 - 使用真实数据"""
        try:
            # CPU 使用率
            cpu_usage = psutil.cpu_percent(interval=1)

            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100

            # 系统运行时间
            uptime_seconds = int(time.time() - psutil.boot_time())

            # 数据库连接状态
            try:
                self.db.execute("SELECT 1")
                database_status = "connected"
            except Exception:
                database_status = "disconnected"

            # 活跃用户数（最近5分钟） - 使用真实数据
            active_time = datetime.utcnow() - timedelta(minutes=5)
            active_users = self.db.query(User).filter(
                User.last_login_at >= active_time
            ).count()

            # 总用户数 - 使用真实数据
            total_users = self.db.query(User).filter(User.is_active == True).count()

            # 今日活跃用户数 - 使用真实数据
            today_active = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_active_users = self.db.query(User).filter(
                and_(
                    User.last_login_at >= today_active,
                    User.is_active == True
                )
            ).count()

            # API请求统计（最近1分钟）- 如果没有日志则显示0
            api_time = datetime.utcnow() - timedelta(minutes=1)
            api_requests = self.db.query(SystemLog).filter(
                and_(
                    SystemLog.log_type == "api",
                    SystemLog.created_at >= api_time
                )
            ).count()

            # 今日API请求总数
            today_api_requests = self.db.query(SystemLog).filter(
                and_(
                    SystemLog.log_type == "api",
                    SystemLog.created_at >= today_active
                )
            ).count()

            return {
                "status": "healthy" if database_status == "connected" else "unhealthy",
                "uptime_seconds": uptime_seconds,
                "cpu_usage": round(cpu_usage, 2),
                "memory_usage": round(memory_usage, 2),
                "disk_usage": round(disk_usage, 2),
                "database_status": database_status,
                "active_users_5min": active_users,
                "active_users_today": today_active_users,
                "total_users": total_users,
                "api_requests_per_minute": api_requests,
                "api_requests_today": today_api_requests,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_user_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取用户统计数据 - 使用真实数据"""
        from app.models.company import CompanyEmployee, Company

        # 总用户数（所有时间）- 不受日期范围限制
        total_users = self.db.query(User).filter(User.is_active == True).count()

        # 新增用户数（在指定时间范围内）
        new_users_query = self.db.query(User)
        if start_date:
            new_users_query = new_users_query.filter(User.created_at >= start_date)
        if end_date:
            new_users_query = new_users_query.filter(User.created_at <= end_date)
        new_users = new_users_query.filter(User.is_active == True).count()

        # 活跃用户数（最近30天有登录）
        active_date = datetime.utcnow() - timedelta(days=30)
        active_users = self.db.query(User).filter(
            and_(
                User.last_login_at >= active_date,
                User.is_active == True
            )
        ).count()

        # 非活跃用户数
        inactive_users = total_users - active_users

        # 按会员等级统计
        tier_stats = self.db.query(
            User.member_tier,
            func.count(User.id)
        ).filter(User.is_active == True).group_by(User.member_tier).all()

        by_tier = {tier: count for tier, count in tier_stats}

        # 按会员类型统计
        type_stats = self.db.query(
            User.membership_type,
            func.count(User.id)
        ).filter(User.is_active == True).group_by(User.membership_type).all()

        by_type = {mtype: count for mtype, count in type_stats}

        # 按状态统计
        by_status = {
            "active": active_users,
            "inactive": inactive_users
        }

        # 增长率计算
        growth_rate = round((new_users / total_users * 100), 2) if total_users > 0 else 0

        # 生成趋势数据（最近30天）
        trend_data = []
        for i in range(30):
            date = (datetime.utcnow() - timedelta(days=29-i)).replace(hour=0, minute=0, second=0, microsecond=0)
            next_date = date + timedelta(days=1)

            # 统计当天注册的用户数
            daily_users = self.db.query(User).filter(
                and_(
                    User.created_at >= date,
                    User.created_at < next_date,
                    User.is_active == True
                )
            ).count()

            trend_data.append({
                "date": date.strftime('%Y-%m-%d'),
                "count": daily_users
            })

        # 会员等级分布
        tier_distribution = {
            "free": by_tier.get("free", 0),
            "personal_free": by_tier.get("personal_free", 0),
            "personal_pro": by_tier.get("personal_pro", 0),
            "personal_advanced": by_tier.get("personal_advanced", 0),
            "personal_flagship": by_tier.get("personal_flagship", 0),
            "enterprise": by_tier.get("enterprise", 0),
            "enterprise_pro": by_tier.get("enterprise_pro", 0),
            "enterprise_pro_max": by_tier.get("enterprise_pro_max", 0)
        }

        return {
            "total_users": total_users,
            "new_users": new_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "by_tier": tier_distribution,
            "by_type": by_type,
            "by_status": by_status,
            "growth_rate": growth_rate,
            "trend": trend_data,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_subscription_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取订阅统计数据 - 使用真实数据,排除继承会员"""
        from app.models.company import CompanyEmployee, Company

        # 获取所有继承会员的用户ID（企业员工但不是企业所有者）
        inherited_user_ids_subquery = self.db.query(CompanyEmployee.user_id).join(
            Company, CompanyEmployee.company_id == Company.id
        ).filter(
            and_(
                CompanyEmployee.status == "active",
                CompanyEmployee.user_id != Company.owner_id
            )
        ).subquery()

        base_query = self.db.query(Subscription)

        # 应用日期筛选
        if start_date:
            base_query = base_query.filter(Subscription.created_at >= start_date)
        if end_date:
            base_query = base_query.filter(Subscription.created_at <= end_date)

        # 排除继承会员的订阅（只统计真实付费订阅）
        paid_query = base_query.filter(~Subscription.user_id.in_(inherited_user_ids_subquery))

        # 总订阅数（只计算付费订阅）
        total_subscriptions = paid_query.count()

        # 活跃订阅数（只计算付费订阅）
        active_subscriptions = paid_query.filter(Subscription.status == "active").count()

        # 按状态统计（只计算付费订阅）
        status_stats = self.db.query(
            Subscription.status,
            func.count(Subscription.id)
        ).filter(~Subscription.user_id.in_(inherited_user_ids_subquery)).group_by(Subscription.status).all()

        by_status = {status: count for status, count in status_stats}

        # 按计划类型统计（只计算付费订阅）
        plan_stats = self.db.query(
            Subscription.plan_id,
            func.count(Subscription.id)
        ).filter(~Subscription.user_id.in_(inherited_user_ids_subquery)).group_by(Subscription.plan_id).all()

        by_plan = {plan: count for plan, count in plan_stats}

        # 本月新增订阅数（只计算付费订阅）
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_new = paid_query.filter(Subscription.created_at >= current_month_start).count()

        # 总收入 - 只计算付费用户的交易
        total_revenue = self.db.query(
            func.sum(SubscriptionTransaction.amount)
        ).join(
            Subscription, SubscriptionTransaction.subscription_id == Subscription.id
        ).filter(
            and_(
                SubscriptionTransaction.status == "success",
                ~Subscription.user_id.in_(inherited_user_ids_subquery)
            )
        ).scalar() or 0

        # 本月收入（只计算付费用户的交易）
        monthly_revenue = self.db.query(
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

        # 今日新增订阅（只计算付费订阅）
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_new = paid_query.filter(Subscription.created_at >= today_start).count()

        # 续订统计 - 通过自动续费字段统计（只计算付费订阅）
        renewals = self.db.query(Subscription).filter(
            and_(
                Subscription.auto_renew == True,
                ~Subscription.user_id.in_(inherited_user_ids_subquery)
            )
        ).count()

        # 统计继承会员数量（用于参考）
        inherited_members_count = self.db.query(User).filter(
            and_(
                User.is_active == True,
                User.id.in_(inherited_user_ids_subquery)
            )
        ).count()

        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "by_status": by_status,
            "by_plan": by_plan,
            "monthly_new": monthly_new,
            "daily_new": daily_new,
            "renewals": renewals,
            "total_revenue": float(total_revenue),
            "monthly_revenue": float(monthly_revenue),
            "inherited_members_count": inherited_members_count,  # 新增：继承会员数量
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_error_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取错误日志 - 使用真实数据"""
        query = self.db.query(SystemLog)

        # 只查询错误级别日志
        query = query.filter(SystemLog.log_level.in_(["error", "critical"]))

        # 应用筛选
        if level:
            query = query.filter(SystemLog.log_level == level)
        if start_date:
            query = query.filter(SystemLog.created_at >= start_date)
        if end_date:
            query = query.filter(SystemLog.created_at <= end_date)

        # 总数
        total = query.count()

        # 分页查询
        offset = (page - 1) * page_size
        logs = query.order_by(SystemLog.created_at.desc()).offset(offset).limit(page_size).all()

        # 转换为响应格式
        log_items = []
        for log in logs:
            log_items.append({
                "id": log.id,
                "log_level": log.log_level,
                "log_type": log.log_type,
                "message": log.message,
                "user_id": log.user_id,
                "ip_address": log.ip_address,
                "request_path": log.request_path,
                "request_method": log.request_method,
                "response_status": log.response_status,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            })

        # 添加系统状态摘要
        total_logs = self.db.query(SystemLog).count()
        recent_errors = self.db.query(SystemLog).filter(
            and_(
                SystemLog.log_level.in_(["error", "critical"]),
                SystemLog.created_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).count()

        return {
            "items": log_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
            "summary": {
                "total_logs": total_logs,
                "recent_errors_24h": recent_errors,
                "has_errors": total > 0,
                "last_24h_errors": recent_errors
            }
        }

    def create_system_log(
        self,
        log_level: str,
        log_type: str,
        message: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        stack_trace: Optional[str] = None
    ) -> SystemLog:
        """创建系统日志"""
        log = SystemLog(
            log_level=log_level,
            log_type=log_type,
            message=message,
            user_id=user_id,
            details=details,
            error_message=error_message,
            stack_trace=stack_trace
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        # 这里可以从数据库或配置文件中读取系统配置
        # 目前返回默认配置
        return {
            "maintenance_mode": False,
            "registration_enabled": True,
            "max_upload_size_mb": 100,
            "session_timeout_minutes": 60,
            "api_rate_limit": 1000,
            "supported_languages": ["zh-CN", "en-US"],
            "default_membership_tier": "free",
            "auto_cleanup_days": 90,
            "email_notifications": True,
            "sms_notifications": False,
        }

    def update_system_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新系统配置"""
        # TODO: 实现系统配置的持久化存储
        # 目前只是返回更新后的配置
        updated_config = self.get_system_config()
        updated_config.update(config_data)

        # 记录配置更新日志
        self.create_system_log(
            log_level="info",
            log_type="system",
            message="系统配置已更新",
            details=updated_config
        )

        return updated_config


def get_system_service(db: Session) -> SystemService:
    """获取系统服务实例"""
    return SystemService(db)
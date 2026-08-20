"""
Notification service for handling system notifications.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from fastapi import HTTPException, status

from app.models.user import User
from app.models.subscription import Subscription
from app.models.system_announcement import SystemAnnouncement
from app.core.database import get_db
from app.core.config import settings
from app.services.notification_prefs import (
    parse_user_prefs,
    should_create_in_app,
    should_send_email,
    should_send_sms,
    map_quota_category,
    map_document_category,
)

try:
    from fastapi import Depends
except ImportError:
    Depends = None


class NotificationService:
    """通知服务类"""

    def __init__(self, db: Session):
        self.db = db

    def deliver_user_notification(
        self,
        user: User,
        *,
        title: str,
        content: str,
        category: str,
        announcement_type: str = "info",
        priority: str = "normal",
        expire_days: int = 14,
        commit: bool = True,
    ) -> Optional[SystemAnnouncement]:
        """
        Create an in-app announcement for one user and optionally email/SMS,
        respecting the user's notification preferences.
        """
        prefs = parse_user_prefs(user)
        if not should_create_in_app(prefs, category):
            return None

        announcement = SystemAnnouncement(
            title=title,
            content=content,
            announcement_type=announcement_type,
            priority=priority,
            target_audience="user",
            is_auto_generated=True,
            is_published=True,
            publish_at=datetime.utcnow(),
            expire_at=datetime.utcnow() + timedelta(days=expire_days),
            created_by=user.id,
        )
        self.db.add(announcement)

        if should_send_email(prefs, category, priority=priority) and user.email:
            try:
                from app.services.email_service import email_service

                email_service.send_email(
                    to_email=user.email,
                    subject=f"【焊序】{title}",
                    html_content=f"<p>{content}</p>",
                    text_content=content,
                )
            except Exception as exc:
                print(f"发送通知邮件失败: {exc}")

        if should_send_sms(prefs, category, priority=priority) and getattr(user, "phone", None):
            try:
                from app.services.sms_service import sms_service

                # 复用短信通道发送简短提醒（开发环境会 mock）
                sms_service.send_sms(
                    phone=user.phone,
                    template_code=getattr(settings, "SMS_TEMPLATE_LOGIN", "SMS_LOGIN"),
                    template_params={"code": title[:20], "minutes": "0"},
                )
            except Exception as exc:
                print(f"发送通知短信失败: {exc}")

        if commit:
            self.db.commit()
            self.db.refresh(announcement)
        return announcement

    def check_expiring_subscriptions(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """检查即将到期的订阅"""
        expiry_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        # 查找即将到期的订阅
        expiring_subscriptions = self.db.query(Subscription).join(User).filter(
            and_(
                Subscription.end_date <= expiry_date,
                Subscription.end_date > datetime.utcnow(),
                Subscription.status == "active",
                User.auto_renewal == False
            )
        ).all()

        result = []
        for subscription in expiring_subscriptions:
            days_until_expiry = (subscription.end_date - datetime.utcnow()).days
            result.append({
                "user_id": subscription.user_id,
                "user_email": subscription.user.email,
                "subscription_id": subscription.id,
                "plan_id": subscription.plan_id,
                "end_date": subscription.end_date.isoformat(),
                "days_until_expiry": days_until_expiry
            })

        return result

    def send_expiration_reminders(self, days_ahead: int = 7) -> int:
        """发送订阅到期提醒"""
        expiring_subscriptions = self.check_expiring_subscriptions(days_ahead)
        
        sent_count = 0
        for subscription_info in expiring_subscriptions:
            try:
                user = self.db.query(User).filter(User.id == subscription_info["user_id"]).first()
                if not user:
                    continue
                created = self.deliver_user_notification(
                    user,
                    title="订阅即将到期提醒",
                    content=(
                        f"您的订阅将在 {subscription_info['days_until_expiry']} 天后到期，"
                        "请及时续费以免影响使用。"
                    ),
                    category="membership",
                    announcement_type="warning",
                    priority="normal",
                    expire_days=max(subscription_info["days_until_expiry"], 1),
                    commit=False,
                )
                if created:
                    sent_count += 1
            except Exception as e:
                print(f"发送到期提醒失败: {str(e)}")

        self.db.commit()
        return sent_count

    def check_expired_subscriptions(self) -> List[Dict[str, Any]]:
        """检查已过期的订阅"""
        # 查找已过期的订阅
        expired_subscriptions = self.db.query(Subscription).join(User).filter(
            and_(
                Subscription.end_date < datetime.utcnow(),
                Subscription.status == "active"
            )
        ).all()

        result = []
        for subscription in expired_subscriptions:
            result.append({
                "user_id": subscription.user_id,
                "user_email": subscription.user.email,
                "subscription_id": subscription.id,
                "plan_id": subscription.plan_id,
                "end_date": subscription.end_date.isoformat(),
                "days_expired": (datetime.utcnow() - subscription.end_date).days
            })

        return result

    def process_expired_subscriptions(self) -> int:
        """
        处理已过期的订阅

        注意：这个方法已被 MembershipTierService.check_and_switch_expired_subscriptions() 替代
        建议使用新的服务来处理订阅到期和会员等级自动切换
        """
        # 使用新的会员等级计算服务处理订阅到期
        from app.services.membership_tier_service import MembershipTierService
        tier_service = MembershipTierService(self.db)

        # 检查并切换过期订阅
        results = tier_service.check_and_switch_expired_subscriptions()

        processed_count = 0
        for result in results:
            if 'error' in result:
                print(f"[订阅到期处理错误] 用户 {result['user_id']}: {result['error']}")
                continue

            user_id = result['user_id']

            try:
                # 如果会员等级发生变化，创建系统公告
                if result['changed']:
                    user = self.db.query(User).filter(User.id == user_id).first()
                    if not user:
                        continue

                    # 根据新等级确定公告内容
                    if result['new_tier'] == 'free':
                        # 降为免费版
                        announcement_content = "您的订阅已过期，已自动切换为免费版。部分功能可能受限，请升级订阅以继续使用全部功能。"
                    else:
                        # 切换到次高等级
                        announcement_content = f"您的高等级订阅已过期，已自动切换到您的其他有效订阅（{result['new_tier']}）。"

                    created = self.deliver_user_notification(
                        user,
                        title="会员等级变更通知",
                        content=announcement_content,
                        category="membership",
                        announcement_type="info",
                        priority="normal",
                        expire_days=30,
                        commit=False,
                    )
                    if created:
                        processed_count += 1
            except Exception as e:
                print(f"处理过期订阅失败 (用户 {user_id}): {str(e)}")
        
        self.db.commit()
        return processed_count

    def process_auto_renewals(self) -> int:
        """为即将到期且开启自动续费的订阅创建待支付订单，不直接扣款或延期。"""
        # 延迟导入：PaymentService 顶层依赖本模块发通知。
        from app.services.payment_service import PaymentService

        renew_date = datetime.utcnow() + timedelta(days=7)

        auto_renew_subscriptions = self.db.query(Subscription).join(User).filter(
            and_(
                Subscription.next_billing_date <= renew_date,
                Subscription.end_date > datetime.utcnow(),
                Subscription.status == "active",
                User.auto_renewal == True
            )
        ).all()

        renewed_count = 0
        payment_service = PaymentService(self.db)
        for subscription in auto_renew_subscriptions:
            try:
                order = payment_service.create_renewal_order_if_needed(subscription, notify=True)
                if order:
                    renewed_count += 1
            except Exception as e:
                print(f"处理自动续费失败: {str(e)}")

        return renewed_count

    def create_system_announcement(
        self,
        title: str,
        content: str,
        announcement_type: str = "info",
        priority: str = "normal",
        target_audience: str = "all",
        publish_at: Optional[datetime] = None,
        expire_at: Optional[datetime] = None,
        created_by: Optional[int] = None,
        is_auto_generated: bool = False
    ) -> SystemAnnouncement:
        """
        创建系统公告

        Args:
            title: 公告标题
            content: 公告内容
            announcement_type: 公告类型
            priority: 优先级
            target_audience: 目标受众
            publish_at: 发布时间
            expire_at: 过期时间
            created_by: 创建者用户ID（None表示系统自动创建）
            is_auto_generated: 是否为自动生成的公告
        """
        announcement = SystemAnnouncement(
            title=title,
            content=content,
            announcement_type=announcement_type,
            priority=priority,
            target_audience=target_audience,
            is_published=True,
            is_auto_generated=is_auto_generated,
            publish_at=publish_at or datetime.utcnow(),
            expire_at=expire_at,
            created_by=created_by  # None表示系统自动创建
        )

        self.db.add(announcement)
        self.db.commit()
        self.db.refresh(announcement)

        return announcement

    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取用户通知"""
        # 获取用户信息以获取注册时间
        from app.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return []

        # 用户只能看到在其注册时间之后发布的通知
        user_created_at = user.created_at

        query = self.db.query(SystemAnnouncement).filter(
            or_(
                SystemAnnouncement.target_audience == "all",
                SystemAnnouncement.target_audience == "user",
                SystemAnnouncement.created_by == user_id
            ),
            SystemAnnouncement.is_published == True,
            SystemAnnouncement.publish_at <= datetime.utcnow(),
            SystemAnnouncement.publish_at >= user_created_at,  # 只显示用户注册后发布的通知
            or_(
                SystemAnnouncement.expire_at.is_(None),
                SystemAnnouncement.expire_at > datetime.utcnow()
            )
        )

        if unread_only:
            # 这里应该添加已读/未读状态查询
            # 暂时返回所有通知
            pass

        announcements = query.order_by(SystemAnnouncement.publish_at.desc()).limit(limit).all()

        result = []
        for announcement in announcements:
            result.append({
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "type": announcement.announcement_type,
                "priority": announcement.priority,
                "publish_at": announcement.publish_at.isoformat(),
                "expire_at": announcement.expire_at.isoformat() if announcement.expire_at else None,
                "view_count": announcement.view_count
            })

        return result


    # ==================== 新增：配额相关通知 ====================

    def notify_quota_warning(self, user: User, quota_type: str, usage_percent: int):
        """配额使用警告"""
        quota_names = {
            "wps": "WPS记录",
            "pqr": "PQR记录",
            "ppqr": "pPQR记录",
            "storage": "存储空间",
        }

        quota_name = quota_names.get(quota_type, quota_type)

        if usage_percent >= 100:
            title = f"🚫 {quota_name}配额已用完"
            announcement_type = "error"
            priority = "urgent"
            content_suffix = "您已无法创建新的记录，请升级会员或清理不需要的记录。"
        elif usage_percent >= 90:
            title = f"⚠️ {quota_name}配额即将用完"
            announcement_type = "warning"
            priority = "high"
            content_suffix = "请及时升级会员或清理不需要的记录。"
        else:  # >= 80
            title = f"📊 {quota_name}配额使用提醒"
            announcement_type = "info"
            priority = "normal"
            content_suffix = "建议您关注配额使用情况。"

        content = f"""尊敬的用户 {user.username or user.email}，您好！

您的{quota_name}配额已使用 {usage_percent}%。

{content_suffix}

升级会员，获得更多配额！"""

        self.deliver_user_notification(
            user,
            title=title,
            content=content,
            category=map_quota_category(quota_type),
            announcement_type=announcement_type,
            priority=priority,
            expire_days=7,
        )

    def notify_unusual_login(self, user: User, ip: str, location: str = "未知"):
        """异常登录通知"""
        title = f"🔐 检测到异常登录"
        content = f"""尊敬的用户 {user.username or user.email}，您好！

我们检测到您的账号在新的地点登录：

登录时间：{datetime.utcnow().strftime('%Y年%m月%d日 %H:%M')}
登录IP：{ip}
登录地点：{location}

如果这是您本人的操作，请忽略此消息。
如果不是您本人操作，请立即修改密码并联系客服。"""

        self.deliver_user_notification(
            user,
            title=title,
            content=content,
            category="security_alerts",
            announcement_type="warning",
            priority="urgent",
            expire_days=3,
        )

    def notify_password_changed(self, user: User):
        """密码修改通知"""
        title = f"🔑 密码已修改"
        content = f"""尊敬的用户 {user.username or user.email}，您好！

您的账号密码已于 {datetime.utcnow().strftime('%Y年%m月%d日 %H:%M')} 修改成功。

如果这不是您本人的操作，请立即联系客服。"""

        self.deliver_user_notification(
            user,
            title=title,
            content=content,
            category="security_alerts",
            announcement_type="info",
            priority="high",
            expire_days=7,
        )

    def check_and_notify_quota_usage(self, thresholds: List[int] = [80, 90, 100]):
        """
        检查并通知配额使用情况

        Args:
            thresholds: 触发通知的阈值列表，默认[80, 90, 100]
        """
        from app.services.membership_service import MembershipService

        membership_service = MembershipService(self.db)
        notified_count = 0

        # 查找所有活跃用户
        users = self.db.query(User).filter(User.is_active == True).all()

        for user in users:
            # 获取用户配额限制
            quotas = membership_service.get_membership_limits(user.member_tier or "free")

            # 检查各类配额
            for quota_type in ["wps", "pqr", "ppqr"]:
                if quota_type not in quotas:
                    continue

                limit = quotas[quota_type]

                # 获取已使用量
                if quota_type == "wps":
                    used = user.wps_quota_used or 0
                elif quota_type == "pqr":
                    used = user.pqr_quota_used or 0
                elif quota_type == "ppqr":
                    used = user.ppqr_quota_used or 0
                else:
                    continue

                if limit <= 0:  # 无限配额
                    continue

                usage_percent = int((used / limit) * 100)

                # 检查是否达到阈值
                for threshold in thresholds:
                    if usage_percent >= threshold:
                        # 检查是否已经发送过此阈值的通知（避免重复通知）
                        # 这里可以添加去重逻辑
                        self.notify_quota_warning(user, quota_type, usage_percent)
                        notified_count += 1
                        break  # 只发送最高阈值的通知

        return notified_count

    # ==================== 审批通知 ====================

    def notify_approval_submitted(
        self,
        submitter_id: int,
        approver_ids: List[int],
        document_type: str,
        document_title: str,
        instance_id: int
    ) -> int:
        """通知审批人有新的审批请求"""
        sent_count = 0
        category = map_document_category(document_type)

        for approver_id in approver_ids:
            try:
                user = self.db.query(User).filter(User.id == approver_id).first()
                if not user:
                    continue
                created = self.deliver_user_notification(
                    user,
                    title="新的审批请求",
                    content=f"您有一个新的{document_type}审批请求：{document_title}",
                    category=category,
                    announcement_type="info",
                    priority="normal",
                    commit=False,
                )
                if created:
                    sent_count += 1
            except Exception as e:
                print(f"发送审批通知失败: {str(e)}")

        self.db.commit()
        return sent_count

    def notify_approval_result(
        self,
        submitter_id: int,
        document_type: str,
        document_title: str,
        result: str,  # approved, rejected, returned
        comment: str,
        instance_id: int
    ):
        """通知提交人审批结果"""
        result_text = {
            "approved": "已通过",
            "rejected": "已拒绝",
            "returned": "已退回"
        }.get(result, "已处理")

        try:
            user = self.db.query(User).filter(User.id == submitter_id).first()
            if not user:
                return
            self.deliver_user_notification(
                user,
                title=f"审批{result_text}",
                content=f"您提交的{document_type}「{document_title}」{result_text}。{comment}",
                category=map_document_category(document_type),
                announcement_type="success" if result == "approved" else "warning",
                priority="normal",
            )
        except Exception as e:
            print(f"发送审批结果通知失败: {str(e)}")

    def notify_approval_reminder(
        self,
        approver_ids: List[int],
        document_type: str,
        document_title: str,
        instance_id: int,
        days_pending: int
    ) -> int:
        """提醒审批人处理待审批文档"""
        sent_count = 0
        category = map_document_category(document_type)

        for approver_id in approver_ids:
            try:
                user = self.db.query(User).filter(User.id == approver_id).first()
                if not user:
                    continue
                created = self.deliver_user_notification(
                    user,
                    title="审批提醒",
                    content=(
                        f"您有一个{document_type}审批请求「{document_title}」"
                        f"已等待{days_pending}天，请及时处理。"
                    ),
                    category=category,
                    announcement_type="warning",
                    priority="high",
                    commit=False,
                )
                if created:
                    sent_count += 1
            except Exception as e:
                print(f"发送审批提醒失败: {str(e)}")

        self.db.commit()
        return sent_count

    def _notify_user_once_today(
        self,
        user_id: int,
        title: str,
        content: str,
        *,
        category: str = "system_updates",
        announcement_type: str = "warning",
        priority: str = "high",
    ) -> bool:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing = (
            self.db.query(SystemAnnouncement)
            .filter(
                SystemAnnouncement.created_by == user_id,
                SystemAnnouncement.title == title,
                SystemAnnouncement.is_auto_generated == True,
                SystemAnnouncement.publish_at >= today,
            )
            .first()
        )
        if existing:
            return False
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        created = self.deliver_user_notification(
            user,
            title=title,
            content=content,
            category=category,
            announcement_type=announcement_type,
            priority=priority,
            commit=False,
        )
        return created is not None

    def notify_expiring_welder_certs(self, days_ahead: int = 30) -> int:
        from datetime import date

        from app.models.welder import Welder, WelderCertification, WelderCertifiedProject

        today = date.today()
        until = today + timedelta(days=days_ahead)
        sent = 0

        # 优先：持证项目到期
        project_rows = (
            self.db.query(WelderCertifiedProject, WelderCertification, Welder)
            .join(
                WelderCertification,
                WelderCertification.id == WelderCertifiedProject.certification_id,
            )
            .join(Welder, Welder.id == WelderCertifiedProject.welder_id)
            .filter(
                Welder.is_active == True,  # noqa: E712
                WelderCertifiedProject.is_active == True,  # noqa: E712
                WelderCertification.is_active == True,  # noqa: E712
                WelderCertifiedProject.expiry_date.isnot(None),
                WelderCertifiedProject.expiry_date >= today,
                WelderCertifiedProject.expiry_date <= until,
            )
            .all()
        )
        for project, cert, welder in project_rows:
            days_left = (project.expiry_date - today).days
            if days_left <= 30:
                welder.certification_status = "expiring_soon"
                project.status = "expiring_soon"
                cert.status = "expiring_soon"
            system = cert.certification_system or "未标注体系"
            project_name = project.project_name or "持证项目"
            title = f"持证即将到期：{welder.full_name} · {system}"
            content = (
                f"焊工 {welder.full_name}（{welder.welder_code}）"
                f"【{system}】持证项目「{project_name}」"
                f"（证号 {cert.certification_number}）将于 {project.expiry_date} 到期，剩余 {days_left} 天。"
                f"请及时安排复审/换证。"
            )
            if self._notify_user_once_today(
                welder.user_id,
                title,
                content,
                category="welder_certifications",
            ):
                sent += 1

        # 兼容：无项目子表的旧证书到期
        has_project = self.db.query(WelderCertifiedProject.certification_id).filter(
            WelderCertifiedProject.is_active == True,  # noqa: E712
        )
        legacy_rows = (
            self.db.query(WelderCertification, Welder)
            .join(Welder, Welder.id == WelderCertification.welder_id)
            .filter(
                Welder.is_active == True,  # noqa: E712
                WelderCertification.is_active == True,  # noqa: E712
                ~WelderCertification.id.in_(has_project),
                WelderCertification.expiry_date.isnot(None),
                WelderCertification.expiry_date >= today,
                WelderCertification.expiry_date <= until,
            )
            .all()
        )
        for cert, welder in legacy_rows:
            days_left = (cert.expiry_date - today).days
            if days_left <= 30:
                welder.certification_status = "expiring_soon"
                cert.status = "expiring_soon"
            system = cert.certification_system or "未标注体系"
            project_name = cert.project_name or cert.certification_type or "持证项目"
            title = f"持证即将到期：{welder.full_name} · {system}"
            content = (
                f"焊工 {welder.full_name}（{welder.welder_code}）"
                f"【{system}】持证项目「{project_name}」"
                f"（证号 {cert.certification_number}）将于 {cert.expiry_date} 到期，剩余 {days_left} 天。"
                f"请及时安排复审/换证。"
            )
            if self._notify_user_once_today(
                welder.user_id,
                title,
                content,
                category="welder_certifications",
            ):
                sent += 1

        # 审证日（next_renewal_date）预警 — 项目优先
        renewal_project_rows = (
            self.db.query(WelderCertifiedProject, WelderCertification, Welder)
            .join(
                WelderCertification,
                WelderCertification.id == WelderCertifiedProject.certification_id,
            )
            .join(Welder, Welder.id == WelderCertifiedProject.welder_id)
            .filter(
                Welder.is_active == True,  # noqa: E712
                WelderCertifiedProject.is_active == True,  # noqa: E712
                WelderCertification.is_active == True,  # noqa: E712
                WelderCertifiedProject.next_renewal_date.isnot(None),
                WelderCertifiedProject.next_renewal_date >= today,
                WelderCertifiedProject.next_renewal_date <= until,
            )
            .all()
        )
        for project, cert, welder in renewal_project_rows:
            days_left = (project.next_renewal_date - today).days
            system = cert.certification_system or "未标注体系"
            project_name = project.project_name or "持证项目"
            title = f"审证临近：{welder.full_name} · {system}"
            content = (
                f"焊工 {welder.full_name}（{welder.welder_code}）"
                f"【{system}】持证项目「{project_name}」"
                f"下次审证日为 {project.next_renewal_date}，剩余 {days_left} 天。"
            )
            if self._notify_user_once_today(
                welder.user_id,
                title,
                content,
                category="welder_certifications",
            ):
                sent += 1

        renewal_rows = (
            self.db.query(WelderCertification, Welder)
            .join(Welder, Welder.id == WelderCertification.welder_id)
            .filter(
                Welder.is_active == True,  # noqa: E712
                WelderCertification.is_active == True,  # noqa: E712
                ~WelderCertification.id.in_(has_project),
                WelderCertification.next_renewal_date.isnot(None),
                WelderCertification.next_renewal_date >= today,
                WelderCertification.next_renewal_date <= until,
            )
            .all()
        )
        for cert, welder in renewal_rows:
            days_left = (cert.next_renewal_date - today).days
            system = cert.certification_system or "未标注体系"
            project_name = cert.project_name or cert.certification_type or "持证项目"
            title = f"审证临近：{welder.full_name} · {system}"
            content = (
                f"焊工 {welder.full_name}（{welder.welder_code}）"
                f"【{system}】持证项目「{project_name}」"
                f"下次审证日为 {cert.next_renewal_date}，剩余 {days_left} 天。"
            )
            if self._notify_user_once_today(
                welder.user_id,
                title,
                content,
                category="welder_certifications",
            ):
                sent += 1

        self.db.commit()
        return sent

    def notify_expiring_warranties(self, days_ahead: int = 30) -> int:
        from datetime import date

        from app.models.equipment import Equipment

        today = date.today()
        until = today + timedelta(days=days_ahead)
        equipment_rows = (
            self.db.query(Equipment)
            .filter(
                Equipment.is_active == True,
                Equipment.warranty_expiry_date.isnot(None),
                Equipment.warranty_expiry_date >= today,
                Equipment.warranty_expiry_date <= until,
            )
            .all()
        )
        sent = 0
        for equipment in equipment_rows:
            days_left = (equipment.warranty_expiry_date - today).days
            title = f"设备保修即将到期：{equipment.equipment_name}"
            content = (
                f"设备 {equipment.equipment_name}（{equipment.equipment_code}）保修将于 "
                f"{equipment.warranty_expiry_date} 到期，剩余 {days_left} 天。"
            )
            if self._notify_user_once_today(
                equipment.user_id,
                title,
                content,
                category="equipment_maintenance",
            ):
                sent += 1
        self.db.commit()
        return sent


def get_notification_service(db: Session = None) -> NotificationService:
    """获取通知服务实例"""
    return NotificationService(db)
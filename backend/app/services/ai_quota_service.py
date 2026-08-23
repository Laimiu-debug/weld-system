"""Transactional platform-AI point reservation and settlement."""
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.data_access import WorkspaceContext, WorkspaceType
from app.models.company import Company
from app.models.smart_import import AIPlanEntitlement, AIUsageLedger, ExtractionJob
from app.models.user import User


class AIQuotaError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 402):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class AIQuotaService:
    """Use page-based AI points while retaining provider token details."""

    def __init__(self, db: Session):
        self.db = db

    def estimate(self, pages: int) -> int:
        return max(1, pages)

    def get_status(self, user: User, context: WorkspaceContext) -> dict[str, Any]:
        entitlement = self._get_entitlement(user, context, lock=False)
        used = self._used_points(user, context, self._period_start())
        daily_used = self._used_points_since(user, context, self._day_start())
        day_start = self._day_start()
        month_start = datetime.combine(self._period_start(), datetime.min.time())
        tasks_today = self._job_count(context, user.id, day_start)
        tasks_month = self._job_count(context, user.id, month_start)
        active_tasks = self._job_count(context, user.id, None, active_only=True)
        user_tasks_today = self._job_count(context, user.id, day_start, user_only=True)
        user_tasks_month = self._job_count(
            context, user.id, month_start, user_only=True
        )
        user_active_tasks = self._job_count(
            context, user.id, None, active_only=True, user_only=True
        )
        monthly = entitlement.monthly_points if entitlement else 0
        return {
            "tier_key": self._tier_key(user, context),
            "workspace_type": str(context.workspace_type),
            "monthly_points": monthly,
            "daily_points": entitlement.daily_points if entitlement else 0,
            "daily_used_points": daily_used,
            "daily_remaining_points": max(
                0, (entitlement.daily_points if entitlement else 0) - daily_used
            ),
            "used_points": used,
            "reserved_or_used_points": used,
            "remaining_points": max(0, monthly - used),
            "max_points_per_task": (
                entitlement.max_points_per_task if entitlement else 0
            ),
            "max_pages_per_task": entitlement.max_pages_per_task if entitlement else 0,
            "max_tasks_per_day": entitlement.max_tasks_per_day if entitlement else 0,
            "max_tasks_per_month": entitlement.max_tasks_per_month
            if entitlement
            else 0,
            "max_concurrent_tasks": entitlement.max_concurrent_tasks
            if entitlement
            else 0,
            "max_user_tasks_per_day": entitlement.max_user_tasks_per_day
            if entitlement
            else 0,
            "max_user_tasks_per_month": entitlement.max_user_tasks_per_month
            if entitlement
            else 0,
            "max_user_concurrent_tasks": entitlement.max_user_concurrent_tasks
            if entitlement
            else 0,
            "tasks_today": tasks_today,
            "tasks_month": tasks_month,
            "active_tasks": active_tasks,
            "user_tasks_today": user_tasks_today,
            "user_tasks_month": user_tasks_month,
            "user_active_tasks": user_active_tasks,
            "period_start": self._period_start(),
            "platform_enabled": bool(entitlement and entitlement.is_enabled),
        }

    def enforce_task_limits(
        self, user: User, context: WorkspaceContext, pages: int
    ) -> None:
        entitlement = self._get_entitlement(user, context, lock=True)
        if entitlement is None or not entitlement.is_enabled:
            raise AIQuotaError("ai_plan_not_enabled", "当前会员套餐未开通 AI 功能", 403)
        if pages > entitlement.max_pages_per_task:
            raise AIQuotaError(
                "ai_task_limit_exceeded",
                f"单次最多解析 {entitlement.max_pages_per_task} 页",
                422,
            )
        day_start = self._day_start()
        month_start = datetime.combine(self._period_start(), datetime.min.time())
        if (
            self._job_count(context, user.id, day_start)
            >= entitlement.max_tasks_per_day
        ):
            raise AIQuotaError("ai_daily_task_limit", "当前工作区今日 AI 任务数已达上限", 429)
        if (
            self._job_count(context, user.id, month_start)
            >= entitlement.max_tasks_per_month
        ):
            raise AIQuotaError("ai_monthly_task_limit", "当前工作区本月 AI 任务数已达上限", 429)
        if (
            self._job_count(context, user.id, None, active_only=True)
            >= entitlement.max_concurrent_tasks
        ):
            raise AIQuotaError("ai_concurrent_task_limit", "当前工作区并发 AI 任务数已达上限", 429)
        if context.workspace_type == WorkspaceType.ENTERPRISE:
            if (
                self._job_count(context, user.id, day_start, user_only=True)
                >= entitlement.max_user_tasks_per_day
            ):
                raise AIQuotaError("ai_user_daily_task_limit", "您今日的 AI 任务数已达上限", 429)
            if (
                self._job_count(context, user.id, month_start, user_only=True)
                >= entitlement.max_user_tasks_per_month
            ):
                raise AIQuotaError("ai_user_monthly_task_limit", "您本月的 AI 任务数已达上限", 429)
            if (
                self._job_count(
                    context, user.id, None, active_only=True, user_only=True
                )
                >= entitlement.max_user_concurrent_tasks
            ):
                raise AIQuotaError("ai_user_concurrent_limit", "您的并发 AI 任务数已达上限", 429)

    def reserve(
        self,
        job: ExtractionJob,
        user: User,
        context: WorkspaceContext,
        pages: int,
    ) -> int:
        existing = self._ledger(f"reserve:{job.id}")
        if existing:
            return existing.points
        entitlement = self._get_entitlement(user, context, lock=True)
        if entitlement is None or not entitlement.is_enabled:
            raise AIQuotaError("ai_plan_not_enabled", "当前会员套餐未开通平台 AI 额度")
        points = self.estimate(pages)
        if (
            pages > entitlement.max_pages_per_task
            or points > entitlement.max_points_per_task
        ):
            raise AIQuotaError(
                "ai_task_limit_exceeded",
                f"单次最多解析 {entitlement.max_pages_per_task} 页",
                422,
            )
        used = self._used_points(user, context, self._period_start())
        daily_used = self._used_points_since(user, context, self._day_start())
        if daily_used + points > entitlement.daily_points:
            raise AIQuotaError(
                "ai_daily_quota_exhausted",
                f"平台 AI 点数不足，今日剩余 {max(0, entitlement.daily_points - daily_used)} 点",
            )
        if used + points > entitlement.monthly_points:
            raise AIQuotaError(
                "ai_quota_exhausted",
                f"平台 AI 点数不足，本月剩余 {max(0, entitlement.monthly_points - used)} 点",
            )
        self.db.add(
            self._new_ledger(
                job,
                user,
                context,
                source="platform",
                transaction_type="reservation",
                points=points,
                balance_delta=-points,
                idempotency_key=f"reserve:{job.id}",
                ocr_pages=pages,
            )
        )
        self.db.commit()
        return points

    def settle(
        self,
        job: ExtractionJob,
        user: User,
        context: WorkspaceContext,
        pages: int,
    ) -> None:
        key = f"settle:{job.id}"
        if self._ledger(key):
            return
        if job.mode == "byok":
            source = "byok"
            points = 0
            delta = 0
        else:
            reservation = self._ledger(f"reserve:{job.id}")
            if reservation is None:
                raise AIQuotaError("ai_reservation_missing", "平台 AI 额度预占记录不存在", 409)
            source = "platform"
            points = self.estimate(pages)
            delta = reservation.points - points
        self.db.add(
            self._new_ledger(
                job,
                user,
                context,
                source=source,
                transaction_type="settlement",
                points=points,
                balance_delta=delta,
                idempotency_key=key,
                input_tokens=job.input_tokens or 0,
                output_tokens=job.output_tokens or 0,
                total_tokens=job.total_tokens or 0,
                ocr_pages=pages,
            )
        )
        self.db.commit()

    def refund(
        self, job_id: str, user: User, context: WorkspaceContext, reason: str
    ) -> None:
        key = f"refund:{job_id}"
        if self._ledger(key) or self._ledger(f"settle:{job_id}"):
            return
        reservation = self._ledger(f"reserve:{job_id}")
        if reservation is None:
            return
        job = self.db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
        if job is None:
            return
        ledger = self._new_ledger(
            job,
            user,
            context,
            source="platform",
            transaction_type="refund",
            points=reservation.points,
            balance_delta=reservation.points,
            idempotency_key=key,
        )
        ledger.metadata_json = {"reason": reason[:200]}
        self.db.add(ledger)
        self.db.commit()

    def _get_entitlement(
        self, user: User, context: WorkspaceContext, lock: bool
    ) -> AIPlanEntitlement | None:
        query = self.db.query(AIPlanEntitlement).filter(
            AIPlanEntitlement.tier_key == self._tier_key(user, context),
            AIPlanEntitlement.workspace_type == str(context.workspace_type),
        )
        if lock:
            query = query.with_for_update()
        return query.first()

    def _tier_key(self, user: User, context: WorkspaceContext) -> str:
        if context.workspace_type == WorkspaceType.ENTERPRISE:
            company = (
                self.db.query(Company).filter(Company.id == context.company_id).first()
            )
            return (company.membership_tier if company else None) or "enterprise"
        return user.member_tier or "free"

    def _used_points(
        self, user: User, context: WorkspaceContext, period_start: date
    ) -> int:
        query = self.db.query(
            func.coalesce(func.sum(AIUsageLedger.balance_delta), 0)
        ).filter(
            AIUsageLedger.source == "platform",
            AIUsageLedger.period_start == period_start,
            AIUsageLedger.workspace_type == str(context.workspace_type),
        )
        if context.workspace_type == WorkspaceType.ENTERPRISE:
            query = query.filter(AIUsageLedger.company_id == context.company_id)
        else:
            query = query.filter(AIUsageLedger.user_id == user.id)
        return max(0, -int(query.scalar() or 0))

    def _used_points_since(
        self, user: User, context: WorkspaceContext, since: datetime
    ) -> int:
        query = self.db.query(
            func.coalesce(func.sum(AIUsageLedger.balance_delta), 0)
        ).filter(
            AIUsageLedger.source == "platform",
            AIUsageLedger.created_at >= since,
            AIUsageLedger.workspace_type == str(context.workspace_type),
        )
        if context.workspace_type == WorkspaceType.ENTERPRISE:
            query = query.filter(AIUsageLedger.company_id == context.company_id)
        else:
            query = query.filter(AIUsageLedger.user_id == user.id)
        return max(0, -int(query.scalar() or 0))

    def _job_count(
        self,
        context: WorkspaceContext,
        user_id: int,
        since: datetime | None,
        *,
        active_only: bool = False,
        user_only: bool = False,
    ) -> int:
        query = self.db.query(func.count(ExtractionJob.id))
        if context.workspace_type == WorkspaceType.ENTERPRISE and not user_only:
            query = query.filter(ExtractionJob.company_id == context.company_id)
        else:
            query = query.filter(ExtractionJob.user_id == user_id)
        if since is not None:
            query = query.filter(ExtractionJob.created_at >= since)
        if active_only:
            query = query.filter(ExtractionJob.status.in_(("queued", "processing")))
        return int(query.scalar() or 0)

    def _ledger(self, key: str) -> AIUsageLedger | None:
        return (
            self.db.query(AIUsageLedger)
            .filter(AIUsageLedger.idempotency_key == key)
            .first()
        )

    def _new_ledger(
        self,
        job: ExtractionJob,
        user: User,
        context: WorkspaceContext,
        *,
        source: str,
        transaction_type: str,
        points: int,
        balance_delta: int,
        idempotency_key: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        ocr_pages: int = 0,
    ) -> AIUsageLedger:
        return AIUsageLedger(
            id=str(uuid4()),
            job_id=job.id,
            user_id=user.id,
            workspace_type=str(context.workspace_type),
            company_id=context.company_id,
            factory_id=context.factory_id,
            access_level="company" if context.is_enterprise() else "private",
            source=source,
            transaction_type=transaction_type,
            points=points,
            balance_delta=balance_delta,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            ocr_pages=ocr_pages,
            period_start=self._period_start(),
            idempotency_key=idempotency_key,
            metadata_json={"provider": job.provider, "model": job.model},
        )

    @staticmethod
    def _period_start() -> date:
        now = datetime.now(UTC)
        return date(now.year, now.month, 1)

    @staticmethod
    def _day_start() -> datetime:
        now = datetime.now(UTC).replace(tzinfo=None)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

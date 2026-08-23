"""P8 observability, privacy, deployment and lifecycle services."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.core.module_permissions import user_can_manage_employees
from app.models.company import Company
from app.models.operations import (
    AIProviderHealthCheck,
    BackupVerification,
    DataOutboundConsent,
    DeploymentProfile,
    OperationalAlert,
    OperationalTaskEvent,
    TenantLifecycleJob,
)
from app.models.smart_import import AIUsageLedger, ExtractionJob, SourceDocument
from app.models.user import User
from app.services.ai_credential_service import AIProviderConfigService


REQUIRED_BACKUP_CATEGORIES = {
    "database",
    "original_files",
    "evidence",
    "rule_versions",
    "approval_records",
}
SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "password",
    "secret",
    "token",
    "encrypted_api_key",
}


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def canonical_hash(value: Any) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def sanitize_log_context(value: dict) -> dict:
    """Recursively redact secrets before operational context is persisted."""

    def clean(item):
        if isinstance(item, dict):
            return {
                key: "[REDACTED]"
                if key.lower() in SENSITIVE_KEYS
                or any(
                    part in key.lower()
                    for part in ("password", "secret", "token", "api_key")
                )
                else clean(val)
                for key, val in item.items()
            }
        if isinstance(item, list):
            return [clean(entry) for entry in item]
        return item

    return clean(value)


def validate_backup_manifest(
    manifest: dict, restore_tested: bool = False
) -> tuple[str, dict, list[str]]:
    coverage = (
        manifest.get("coverage") if isinstance(manifest.get("coverage"), dict) else {}
    )
    normalized = {
        key: bool(coverage.get(key)) for key in sorted(REQUIRED_BACKUP_CATEGORIES)
    }
    coverage_missing = [key for key, covered in normalized.items() if not covered]
    missing = list(coverage_missing)
    if not restore_tested:
        missing.append("restore_drill")
    checksums_ok = bool(manifest.get("checksums_verified"))
    if not missing and checksums_ok:
        status = "passed"
    elif len(coverage_missing) == len(REQUIRED_BACKUP_CATEGORIES):
        status = "failed"
    else:
        status = "partial"
    return status, normalized, missing


def deployment_capabilities(
    mode: str, network_policy: str, local_ai: bool, local_ocr: bool
) -> dict:
    offline = mode == "offline" or network_policy == "offline"
    return {
        "external_ai": not offline
        and network_policy in {"external_allowed", "allowlist_only"},
        "local_ai": bool(local_ai),
        "local_ocr": bool(local_ocr),
        "manual_entry": True,
        "external_storage": not offline,
    }


class OperationsService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _scope(context: WorkspaceContext, user_id: int | None = None) -> dict:
        return {
            "user_id": user_id or context.user_id,
            "workspace_type": context.workspace_type,
            "company_id": context.company_id,
            "factory_id": context.factory_id,
        }

    def ensure_manager(self, user: User, context: WorkspaceContext) -> Company | None:
        if user.is_superuser:
            return None
        if context.workspace_type != WorkspaceType.ENTERPRISE or not context.company_id:
            raise HTTPException(403, "只有企业管理员或平台管理员可以执行此操作")
        company = (
            self.db.query(Company).filter(Company.id == context.company_id).first()
        )
        if not company or not user_can_manage_employees(self.db, user, company):
            raise HTTPException(403, "只有企业管理员可以执行此操作")
        return company

    def _scope_filter(self, query, model, user: User, context: WorkspaceContext):
        if context.workspace_type == WorkspaceType.ENTERPRISE:
            return query.filter(
                model.workspace_type == "enterprise",
                model.company_id == context.company_id,
            )
        return query.filter(
            model.workspace_type == "personal", model.user_id == user.id
        )

    def record_extraction_job(self, job: ExtractionJob) -> OperationalTaskEvent:
        kind = "ocr" if (job.schema_snapshot or {}).get("job_kind") == "parse" else "ai"
        existing = (
            self.db.query(OperationalTaskEvent)
            .filter(
                OperationalTaskEvent.task_kind == kind,
                OperationalTaskEvent.source_ref == job.id,
            )
            .first()
        )
        started = job.started_at or job.created_at
        completed = job.completed_at or utcnow()
        duration = (
            max(0, int((completed - started).total_seconds() * 1000)) if started else 0
        )
        queue_wait = (
            max(0, int((started - job.created_at).total_seconds() * 1000))
            if started and job.created_at
            else 0
        )
        values = {
            "status": job.status,
            "provider": job.provider,
            "model": job.model,
            "queue_wait_ms": queue_wait,
            "duration_ms": duration,
            "retry_count": max(0, (job.attempt_count or 0) - 1),
            "input_tokens": job.input_tokens or 0,
            "output_tokens": job.output_tokens or 0,
            "total_tokens": job.total_tokens or 0,
            "estimated_cost_micros": int(
                ((job.input_tokens or 0) * 2 + (job.output_tokens or 0) * 8)
            ),
            "error_code": job.error_code,
            "log_context": sanitize_log_context(
                {
                    "request_trace_id": job.request_trace_id,
                    "mode": job.mode,
                    "progress": job.progress_detail,
                }
            ),
            "started_at": started,
            "completed_at": job.completed_at,
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            return existing
        item = OperationalTaskEvent(
            id=str(uuid4()),
            task_kind=kind,
            source_ref=job.id,
            **values,
            user_id=job.user_id,
            workspace_type=job.workspace_type,
            company_id=job.company_id,
            factory_id=job.factory_id,
        )
        self.db.add(item)
        return item

    def record_task_event(
        self,
        task_kind: str,
        source_ref: str,
        status: str,
        context: WorkspaceContext,
        user_id: int,
        *,
        duration_ms: int = 0,
        retry_count: int = 0,
        error_code: str | None = None,
        log_context: dict | None = None,
    ) -> OperationalTaskEvent:
        existing = (
            self.db.query(OperationalTaskEvent)
            .filter(
                OperationalTaskEvent.task_kind == task_kind,
                OperationalTaskEvent.source_ref == source_ref,
            )
            .first()
        )
        item = existing or OperationalTaskEvent(
            id=str(uuid4()),
            task_kind=task_kind,
            source_ref=source_ref,
            **self._scope(context, user_id),
        )
        item.status = status
        item.duration_ms = max(0, duration_ms)
        item.retry_count = max(0, retry_count)
        item.error_code = error_code
        item.log_context = sanitize_log_context(log_context or {})
        item.completed_at = (
            utcnow() if status in {"completed", "failed", "cancelled"} else None
        )
        if not existing:
            self.db.add(item)
        return item

    def dashboard(self, user: User, context: WorkspaceContext, hours: int = 24) -> dict:
        since = utcnow() - timedelta(hours=hours)
        query = self._scope_filter(
            self.db.query(OperationalTaskEvent), OperationalTaskEvent, user, context
        ).filter(OperationalTaskEvent.created_at >= since)
        events = query.all()
        queued = (
            self._scope_filter(
                self.db.query(ExtractionJob), ExtractionJob, user, context
            )
            .filter(ExtractionJob.status == "queued")
            .count()
        )
        total = len(events)
        failed = sum(item.status == "failed" for item in events)
        retried = sum(item.retry_count > 0 for item in events)
        by_kind = {}
        for kind in ("ai", "ocr", "rule", "import"):
            rows = [item for item in events if item.task_kind == kind]
            by_kind[kind] = {
                "count": len(rows),
                "average_duration_ms": int(
                    sum(item.duration_ms for item in rows) / len(rows)
                )
                if rows
                else 0,
                "failure_rate": round(
                    sum(item.status == "failed" for item in rows) / len(rows), 4
                )
                if rows
                else 0,
                "retry_rate": round(
                    sum(item.retry_count > 0 for item in rows) / len(rows), 4
                )
                if rows
                else 0,
                "tokens": sum(item.total_tokens for item in rows),
                "estimated_cost_micros": sum(
                    item.estimated_cost_micros for item in rows
                ),
            }
        return {
            "window_hours": hours,
            "queue_length": queued,
            "task_count": total,
            "average_duration_ms": int(sum(item.duration_ms for item in events) / total)
            if total
            else 0,
            "failure_rate": round(failed / total, 4) if total else 0,
            "retry_rate": round(retried / total, 4) if total else 0,
            "total_tokens": sum(item.total_tokens for item in events),
            "estimated_cost_micros": sum(item.estimated_cost_micros for item in events),
            "by_task_kind": by_kind,
        }

    def detect_usage_anomalies(
        self, user: User, context: WorkspaceContext
    ) -> list[OperationalAlert]:
        self.ensure_manager(user, context)
        today = utcnow().date()
        query = self._scope_filter(
            self.db.query(AIUsageLedger), AIUsageLedger, user, context
        ).filter(AIUsageLedger.period_start == today)
        rows = query.all()
        points = sum(
            max(0, -(item.balance_delta or 0))
            for item in rows
            if item.transaction_type == "settlement"
        )
        tokens = sum(
            item.total_tokens or 0
            for item in rows
            if item.transaction_type == "settlement"
        )
        alerts = []
        metrics = self.dashboard(user, context, 24)
        thresholds = [
            ("quota_warning", points >= 8000, "企业 AI 额度接近预警阈值", {"points": points}),
            (
                "token_anomaly",
                tokens >= 1_000_000,
                "企业 AI Token 消耗异常",
                {"tokens": tokens},
            ),
            (
                "queue_backlog",
                metrics["queue_length"] >= settings.AI_MAX_QUEUED_TASKS * 0.8,
                "AI/OCR 队列积压",
                {"queue_length": metrics["queue_length"]},
            ),
            (
                "failure_rate",
                metrics["task_count"] >= 5 and metrics["failure_rate"] >= 0.2,
                "AI/OCR/导入任务失败率异常",
                {"failure_rate": metrics["failure_rate"]},
            ),
        ]
        for alert_type, triggered, title, detail in thresholds:
            if not triggered:
                continue
            fingerprint = canonical_hash(
                {"type": alert_type, "company": context.company_id, "date": str(today)}
            )
            item = (
                self.db.query(OperationalAlert)
                .filter(
                    OperationalAlert.fingerprint == fingerprint,
                    OperationalAlert.status.in_(["open", "acknowledged"]),
                )
                .first()
            )
            if not item:
                item = OperationalAlert(
                    id=str(uuid4()),
                    alert_type=alert_type,
                    severity="warning",
                    fingerprint=fingerprint,
                    title=title,
                    detail=detail,
                    **self._scope(context, user.id),
                )
                self.db.add(item)
            alerts.append(item)
        self.db.commit()
        return alerts

    def list_alerts(self, user: User, context: WorkspaceContext):
        return (
            self._scope_filter(
                self.db.query(OperationalAlert), OperationalAlert, user, context
            )
            .order_by(OperationalAlert.created_at.desc())
            .all()
        )

    def decide_alert(
        self, alert_id: str, action: str, user: User, context: WorkspaceContext
    ):
        self.ensure_manager(user, context)
        item = (
            self._scope_filter(
                self.db.query(OperationalAlert), OperationalAlert, user, context
            )
            .filter(OperationalAlert.id == alert_id)
            .first()
        )
        if not item:
            raise HTTPException(404, "告警不存在")
        item.status = "acknowledged" if action == "acknowledge" else "resolved"
        item.acknowledged_by, item.acknowledged_at = user.id, utcnow()
        if item.status == "resolved":
            item.resolved_at = utcnow()
        self.db.commit()
        return item

    def health_check(
        self, config_id: str, user: User, context: WorkspaceContext, client=None
    ):
        credentials = AIProviderConfigService(self.db)
        config, key = credentials.resolve_for_use(config_id, user, context)
        started = time.perf_counter()
        status, code, message = "healthy", None, "连接正常"
        owns_client = client is None
        client = client or httpx.Client(
            timeout=10, follow_redirects=False, trust_env=False
        )
        try:
            response = client.get(
                f"{config.base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {key}"},
            )
            if response.status_code in {401, 403}:
                status, code, message = (
                    "unavailable",
                    "provider_auth_failed",
                    "API Key 无效或无权访问",
                )
            elif response.status_code == 429:
                status, code, message = "degraded", "provider_rate_limited", "服务限流或额度不足"
            elif response.status_code >= 500:
                status, code, message = (
                    "unavailable",
                    "provider_unavailable",
                    "模型服务暂不可用",
                )
            elif response.status_code >= 400:
                status, code, message = (
                    "degraded",
                    "provider_probe_rejected",
                    "健康探测被服务拒绝",
                )
        except (httpx.TimeoutException, httpx.RequestError):
            status, code, message = "unavailable", "provider_unreachable", "无法连接模型服务"
        finally:
            if owns_client:
                client.close()
        latency = int((time.perf_counter() - started) * 1000)
        config.last_test_status = "success" if status == "healthy" else "failed"
        config.last_tested_at, config.last_error = (
            utcnow(),
            None if status == "healthy" else message,
        )
        item = AIProviderHealthCheck(
            id=str(uuid4()),
            provider_config_id=config.id,
            provider=config.provider,
            model=config.model,
            status=status,
            latency_ms=latency,
            error_code=code,
            safe_message=message,
            **self._scope(context, user.id),
        )
        self.db.add(item)
        self.db.commit()
        return item

    def fallback_plan(
        self,
        preferred_config_id: str | None,
        allow_manual: bool,
        user: User,
        context: WorkspaceContext,
    ) -> dict:
        profile = self.get_deployment_profile(context)
        caps = deployment_capabilities(
            profile.deployment_mode if profile else settings.DEPLOYMENT_MODE,
            profile.network_policy
            if profile
            else (
                "offline"
                if settings.DEPLOYMENT_MODE == "offline"
                else "external_allowed"
            ),
            bool(
                (profile and profile.local_ai_base_url) or settings.AI_OFFLINE_BASE_URL
            ),
            bool(
                (profile and profile.local_ocr_enabled) or settings.OCR_OFFLINE_ENABLED
            ),
        )
        configs = AIProviderConfigService(self.db).list(user, context)
        healthy = [
            item
            for item in configs
            if item.is_active and item.last_test_status == "success"
        ]
        preferred = next(
            (item for item in healthy if item.id == preferred_config_id), None
        )
        chain = []
        if caps["external_ai"] and preferred:
            chain.append(
                {
                    "mode": "byok",
                    "config_id": preferred.id,
                    "provider": preferred.provider,
                    "model": preferred.model,
                }
            )
        if caps["external_ai"]:
            chain.extend(
                {
                    "mode": "byok",
                    "config_id": item.id,
                    "provider": item.provider,
                    "model": item.model,
                }
                for item in healthy
                if item.id != getattr(preferred, "id", None)
            )
        if caps["local_ai"]:
            chain.append(
                {
                    "mode": "offline",
                    "base_url": (profile.local_ai_base_url if profile else None)
                    or settings.AI_OFFLINE_BASE_URL,
                    "model": (profile.local_ai_model if profile else None)
                    or settings.AI_OFFLINE_MODEL,
                }
            )
        if allow_manual:
            chain.append({"mode": "manual", "reason": "所有模型不可用时保留手工录入"})
        return {"capabilities": caps, "fallback_chain": chain, "available": bool(chain)}

    def create_consent(self, data, user: User, context: WorkspaceContext):
        document = (
            self._scope_filter(
                self.db.query(SourceDocument), SourceDocument, user, context
            )
            .filter(SourceDocument.id == data.document_id)
            .first()
        )
        if not document:
            raise HTTPException(404, "文档不存在")
        host = data.provider_host.lower().strip()
        if "/" in host or ":" in host or host.startswith("."):
            raise HTTPException(422, "外部服务商域名格式无效")
        try:
            expires = (
                datetime.fromisoformat(data.expires_at) if data.expires_at else None
            )
            if expires and expires.tzinfo:
                expires = expires.astimezone(UTC).replace(tzinfo=None)
        except ValueError as exc:
            raise HTTPException(422, "授权到期时间格式无效") from exc
        item = DataOutboundConsent(
            id=str(uuid4()),
            document_id=document.id,
            document_type=document.document_type,
            provider_host=host,
            purpose=data.purpose,
            privacy_notice_version=data.privacy_notice_version,
            privacy_notice_hash=data.privacy_notice_hash,
            authorized=data.authorized,
            authorized_by=user.id if data.authorized else None,
            authorized_at=utcnow() if data.authorized else None,
            expires_at=expires,
            **self._scope(context, user.id),
        )
        self.db.add(item)
        self.db.commit()
        return item

    def require_consent(
        self,
        document_id: str,
        provider_url: str,
        user: User,
        context: WorkspaceContext,
        consent_id: str | None = None,
    ):
        host = (urlsplit(provider_url).hostname or "").lower()
        now = utcnow()
        item = (
            self._scope_filter(
                self.db.query(DataOutboundConsent), DataOutboundConsent, user, context
            )
            .filter(
                DataOutboundConsent.document_id == document_id,
                DataOutboundConsent.provider_host == host,
                DataOutboundConsent.id == consent_id,
                DataOutboundConsent.authorized.is_(True),
                DataOutboundConsent.revoked_at.is_(None),
            )
            .order_by(DataOutboundConsent.authorized_at.desc())
            .first()
        )
        if not item or (item.expires_at and item.expires_at <= now):
            raise HTTPException(428, "向外部模型发送图纸/PQR前必须阅读隐私说明并明确授权")
        return item

    def revoke_consent(self, consent_id: str, user: User, context: WorkspaceContext):
        item = (
            self._scope_filter(
                self.db.query(DataOutboundConsent), DataOutboundConsent, user, context
            )
            .filter(DataOutboundConsent.id == consent_id)
            .first()
        )
        if not item:
            raise HTTPException(404, "外发授权不存在")
        item.revoked_at = utcnow()
        self.db.commit()
        return item

    def get_deployment_profile(self, context: WorkspaceContext):
        if not context.company_id:
            return None
        return (
            self.db.query(DeploymentProfile)
            .filter(DeploymentProfile.company_id == context.company_id)
            .first()
        )

    def update_deployment_profile(self, data, user: User, context: WorkspaceContext):
        self.ensure_manager(user, context)
        if data.deployment_mode == "offline" and data.network_policy != "offline":
            raise HTTPException(422, "完全离线部署必须使用 offline 网络策略")
        if data.network_policy == "offline" and not (
            data.local_ai_base_url or data.local_ocr_enabled
        ):
            # Manual entry remains available, but make the limitation explicit.
            data.config_snapshot["degraded_to_manual"] = True
        item = self.get_deployment_profile(context)
        if not item:
            item = DeploymentProfile(company_id=context.company_id)
            self.db.add(item)
        for key, value in data.model_dump().items():
            setattr(item, key, value)
        item.updated_by = user.id
        self.db.commit()
        return item

    def verify_backup(self, data, user: User):
        if not user.is_superuser:
            raise HTTPException(403, "只有平台管理员可以登记恢复验证")
        status, coverage, missing = validate_backup_manifest(
            data.manifest, data.restore_tested
        )
        item = BackupVerification(
            id=str(uuid4()),
            backup_ref=data.backup_ref,
            manifest_hash=canonical_hash(data.manifest),
            status=status,
            coverage=coverage,
            missing_categories=missing,
            restore_tested=data.restore_tested,
            restore_target=data.restore_target,
            verified_by=user.id,
            notes=data.notes,
        )
        self.db.add(item)
        self.db.commit()
        return item

    def create_lifecycle_job(self, data, user: User, context: WorkspaceContext):
        company = self.ensure_manager(user, context)
        company_id = (
            context.company_id if context.company_id else getattr(company, "id", None)
        )
        if (
            data.operation == "delete"
            and data.confirmation != f"DELETE COMPANY {company_id}"
        ):
            raise HTTPException(422, f"删除申请确认文本必须为 DELETE COMPANY {company_id}")
        item = TenantLifecycleJob(
            id=str(uuid4()),
            company_id=company_id,
            operation=data.operation,
            confirmation=data.confirmation,
            requested_by=user.id,
            deletion_plan={
                "requires_export": True,
                "requires_second_approval": True,
                "cascade_via_foreign_keys": True,
            }
            if data.operation == "delete"
            else {},
        )
        self.db.add(item)
        self.db.commit()
        return item

    def decide_lifecycle_job(
        self, job_id: str, approve: bool, user: User, context: WorkspaceContext
    ):
        self.ensure_manager(user, context)
        item = (
            self.db.query(TenantLifecycleJob)
            .filter(
                TenantLifecycleJob.id == job_id,
                TenantLifecycleJob.company_id == context.company_id,
            )
            .first()
        )
        if not item or item.status != "requested":
            raise HTTPException(409, "生命周期任务不存在或状态不可审批")
        if item.requested_by == user.id and not user.is_superuser:
            raise HTTPException(409, "租户删除/导出必须由另一名管理员复核")
        item.status = "approved" if approve else "cancelled"
        item.approved_by, item.approved_at = user.id, utcnow()
        self.db.commit()
        return item

    def execute_lifecycle_job(
        self,
        job_id: str,
        confirmation: str,
        dry_run: bool,
        user: User,
        context: WorkspaceContext,
    ):
        self.ensure_manager(user, context)
        item = (
            self.db.query(TenantLifecycleJob)
            .filter(
                TenantLifecycleJob.id == job_id,
                TenantLifecycleJob.company_id == context.company_id,
            )
            .first()
        )
        if not item or item.status != "approved":
            raise HTTPException(409, "生命周期任务尚未批准")
        expected = f"EXECUTE {item.operation.upper()} {item.company_id}"
        if confirmation != expected:
            raise HTTPException(422, f"执行确认文本必须为 {expected}")
        if item.operation == "delete" and not dry_run and not item.export_manifest:
            raise HTTPException(409, "租户删除前必须先完成 dry-run 并生成导出清单")
        company_id = item.company_id
        table_counts = {}
        for model in (SourceDocument, ExtractionJob, AIUsageLedger):
            if hasattr(model, "company_id"):
                table_counts[model.__tablename__] = (
                    self.db.query(model).filter(model.company_id == company_id).count()
                )
        item.export_manifest = {
            "company_id": company_id,
            "generated_at": utcnow().isoformat(),
            "table_counts": table_counts,
            "includes_private_files": True,
            "includes_audit": True,
        }
        if dry_run:
            self.db.commit()
            return item
        item.status = "processing"
        self.db.flush()
        if item.operation == "delete":
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if company:
                self.db.delete(company)
        item.status, item.executed_by, item.executed_at = "completed", user.id, utcnow()
        self.db.commit()
        return item

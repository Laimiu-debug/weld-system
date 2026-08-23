"""P8 observability, privacy, deployment and lifecycle services."""
from __future__ import annotations

import hashlib
import json
import time
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base
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
from app.services.document_storage_service import get_document_storage


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
    mode: str,
    network_policy: str,
    local_ai: bool,
    local_ocr: bool,
    external_storage_allowed: bool = True,
) -> dict:
    offline = mode == "offline" or network_policy == "offline"
    return {
        "external_ai": not offline
        and network_policy in {"external_allowed", "allowlist_only"},
        "local_ai": bool(local_ai),
        "local_ocr": bool(local_ocr),
        "manual_entry": True,
        "external_storage": not offline and bool(external_storage_allowed),
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
            profile.external_storage_allowed if profile else True,
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

    def ensure_document_storage_allowed(self, context: WorkspaceContext) -> None:
        """Block tenant writes to an external document backend when policy forbids it."""
        if settings.DOCUMENT_STORAGE_BACKEND.strip().lower() == "local":
            return
        profile = self.get_deployment_profile(context)
        offline = (
            (profile and profile.network_policy == "offline")
            or (profile and profile.deployment_mode == "offline")
            or (not profile and settings.DEPLOYMENT_MODE == "offline")
        )
        if offline or (profile and not profile.external_storage_allowed):
            raise HTTPException(503, "当前部署策略禁止向外部文档存储写入数据")

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

    @staticmethod
    def _export_root() -> Path:
        root = (Path(settings.UPLOAD_DIR).resolve() / "tenant_exports").resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root

    @classmethod
    def _export_path(cls, artifact_key: str) -> Path:
        root = cls._export_root()
        candidate = (Path(settings.UPLOAD_DIR).resolve() / artifact_key).resolve()
        if not candidate.is_relative_to(root):
            raise HTTPException(409, "租户导出制品路径无效")
        return candidate

    @staticmethod
    def _json_bytes(value: Any) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        ).encode("utf-8")

    @staticmethod
    def _file_sha256(path: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as source:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                size += len(chunk)
        return digest.hexdigest(), size

    def _tenant_table_rows(self, company_id: int) -> dict[str, list[dict]]:
        """Collect direct company rows plus dependent child rows through foreign keys."""
        tables = sorted(Base.metadata.tables.values(), key=lambda row: row.name)
        collected: dict[str, list[dict]] = {table.name: [] for table in tables}

        for table in tables:
            if table.name == Company.__tablename__:
                statement = select(table).where(table.c.id == company_id)
            elif "company_id" in table.c:
                statement = select(table).where(table.c.company_id == company_id)
            else:
                continue
            collected[table.name] = [
                dict(row) for row in self.db.execute(statement).mappings()
            ]

        changed = True
        while changed:
            changed = False
            for table in tables:
                primary_keys = [column.name for column in table.primary_key.columns]
                known_keys = {
                    tuple(row.get(column) for column in primary_keys)
                    for row in collected[table.name]
                }
                for foreign_key in table.foreign_keys:
                    parent_rows = collected[foreign_key.column.table.name]
                    parent_values = {
                        row.get(foreign_key.column.name)
                        for row in parent_rows
                        if row.get(foreign_key.column.name) is not None
                    }
                    if not parent_values:
                        continue
                    ordered_values = sorted(parent_values, key=str)
                    for offset in range(0, len(ordered_values), 1000):
                        values = ordered_values[offset : offset + 1000]
                        rows = self.db.execute(
                            select(table).where(foreign_key.parent.in_(values))
                        ).mappings()
                        for mapping in rows:
                            row = dict(mapping)
                            key = tuple(row.get(column) for column in primary_keys)
                            if key in known_keys:
                                continue
                            collected[table.name].append(row)
                            known_keys.add(key)
                            changed = True
        return collected

    def _create_tenant_export(self, job: TenantLifecycleJob, company_id: int) -> dict:
        """Create an atomic ZIP containing every company-scoped table and source file."""
        root = self._export_root()
        final_path = (root / f"{job.id}.zip").resolve()
        staging_path = (root / f".{job.id}.{uuid4().hex}.part").resolve()
        table_counts: dict[str, int] = {}
        exported_files: list[dict[str, Any]] = []
        try:
            with zipfile.ZipFile(
                staging_path, "x", compression=zipfile.ZIP_DEFLATED, allowZip64=True
            ) as archive:
                tenant_rows = self._tenant_table_rows(company_id)
                if len(tenant_rows.get(Company.__tablename__, [])) != 1:
                    raise HTTPException(404, "企业不存在，无法生成租户导出制品")
                for table_name, rows in tenant_rows.items():
                    table_counts[table_name] = len(rows)
                    archive.writestr(
                        f"tables/{table_name}.json", self._json_bytes(rows)
                    )

                documents = (
                    self.db.query(SourceDocument)
                    .filter(SourceDocument.company_id == company_id)
                    .order_by(SourceDocument.id)
                    .all()
                )
                storage = get_document_storage()
                for document in documents:
                    safe_name = Path(document.original_filename or "document").name
                    member = f"private_documents/{document.id}/{safe_name}"
                    digest = hashlib.sha256()
                    size = 0
                    with storage.open_stream(document.storage_key) as source:
                        with archive.open(member, "w") as destination:
                            while True:
                                chunk = source.read(1024 * 1024)
                                if not chunk:
                                    break
                                digest.update(chunk)
                                size += len(chunk)
                                destination.write(chunk)
                    actual_hash = digest.hexdigest()
                    if document.sha256 and actual_hash != document.sha256:
                        raise HTTPException(409, f"原始文档校验失败：{document.id}")
                    exported_files.append(
                        {
                            "document_id": document.id,
                            "archive_member": member,
                            "sha256": actual_hash,
                            "size_bytes": size,
                        }
                    )

                content_manifest = {
                    "format_version": 1,
                    "job_id": job.id,
                    "company_id": company_id,
                    "generated_at": utcnow().isoformat(),
                    "table_counts": table_counts,
                    "private_files": exported_files,
                }
                archive.writestr("manifest.json", self._json_bytes(content_manifest))
            staging_path.replace(final_path)
        except Exception:
            staging_path.unlink(missing_ok=True)
            raise

        artifact_hash, size = self._file_sha256(final_path)
        return {
            "format": "tenant-export-zip-v1",
            "company_id": company_id,
            "job_id": job.id,
            "generated_at": utcnow().isoformat(),
            "artifact_key": final_path.relative_to(
                Path(settings.UPLOAD_DIR).resolve()
            ).as_posix(),
            "artifact_sha256": artifact_hash,
            "artifact_size_bytes": size,
            "table_counts": table_counts,
            "private_file_count": len(exported_files),
            "includes_private_files": True,
            "includes_audit": True,
        }

    def _validate_tenant_export(
        self, manifest: dict, job: TenantLifecycleJob, company_id: int
    ) -> Path:
        if (
            manifest.get("format") != "tenant-export-zip-v1"
            or manifest.get("job_id") != job.id
            or manifest.get("company_id") != company_id
            or not manifest.get("artifact_key")
            or not manifest.get("artifact_sha256")
        ):
            raise HTTPException(409, "租户删除前必须生成有效的数据导出制品")
        path = self._export_path(manifest["artifact_key"])
        if not path.is_file():
            raise HTTPException(409, "租户导出制品不存在，请重新执行 dry-run")
        digest, size = self._file_sha256(path)
        if digest != manifest["artifact_sha256"]:
            raise HTTPException(409, "租户导出制品校验失败，请重新执行 dry-run")
        if size != manifest.get("artifact_size_bytes"):
            raise HTTPException(409, "租户导出制品大小不匹配，请重新执行 dry-run")
        try:
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    raise HTTPException(409, "租户导出制品已损坏")
                content = json.loads(archive.read("manifest.json"))
        except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as exc:
            raise HTTPException(409, "租户导出制品无法验证") from exc
        if content.get("job_id") != job.id or content.get("company_id") != company_id:
            raise HTTPException(409, "租户导出制品与生命周期任务不匹配")
        return path

    def lifecycle_export_artifact(
        self, job_id: str, user: User, context: WorkspaceContext
    ) -> tuple[Path, TenantLifecycleJob]:
        self.ensure_manager(user, context)
        item = (
            self.db.query(TenantLifecycleJob)
            .filter(
                TenantLifecycleJob.id == job_id,
                TenantLifecycleJob.company_id == context.company_id,
            )
            .first()
        )
        if not item or not item.export_manifest:
            raise HTTPException(404, "租户导出制品不存在")
        path = self._validate_tenant_export(
            item.export_manifest, item, context.company_id
        )
        return path, item

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
        company_id = item.company_id
        if dry_run or (item.operation == "export" and not item.export_manifest):
            item.export_manifest = self._create_tenant_export(item, company_id)
        if dry_run:
            self.db.commit()
            return item
        self._validate_tenant_export(item.export_manifest or {}, item, company_id)
        item.status = "processing"
        self.db.flush()
        if item.operation == "delete":
            storage_keys = [
                value
                for (value,) in self.db.query(SourceDocument.storage_key)
                .filter(SourceDocument.company_id == company_id)
                .all()
            ]
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if company:
                self.db.delete(company)
        item.status, item.executed_by, item.executed_at = "completed", user.id, utcnow()
        self.db.commit()
        if item.operation == "delete":
            storage = get_document_storage()
            failures = []
            for storage_key in storage_keys:
                try:
                    storage.delete(storage_key)
                except Exception:
                    failures.append(storage_key)
            if failures:
                item.status = "failed"
                item.error_message = f"数据库已删除，但有 {len(failures)} 个原始文件清理失败"
                self.db.commit()
                raise HTTPException(500, "租户数据已删除，但部分原始文件需要人工清理")
        return item

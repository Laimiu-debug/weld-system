"""P8 operations, privacy, deployment and tenant lifecycle models."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


def _uuid() -> str:
    return str(uuid4())


class OperationsWorkspaceMixin:
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    workspace_type = Column(String(20), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"))
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class OperationalTaskEvent(OperationsWorkspaceMixin, Base):
    __tablename__ = "operational_task_events"
    id = Column(String(36), primary_key=True, default=_uuid)
    task_kind = Column(String(20), nullable=False)
    source_ref = Column(String(120), nullable=False)
    status = Column(String(20), nullable=False)
    provider = Column(String(80))
    model = Column(String(120))
    queue_wait_ms = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_micros = Column(Integer, nullable=False, default=0)
    error_code = Column(String(80))
    log_context = Column(JSONB, nullable=False, default=dict)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "task_kind IN ('ai','ocr','rule','import')", name="ck_operational_task_kind"
        ),
        CheckConstraint(
            "status IN ('queued','processing','completed','failed','cancelled')",
            name="ck_operational_task_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_operational_task_workspace",
        ),
        CheckConstraint(
            "queue_wait_ms >= 0 AND duration_ms >= 0 AND retry_count >= 0 AND total_tokens >= 0 AND estimated_cost_micros >= 0",
            name="ck_operational_task_nonnegative",
        ),
        UniqueConstraint("task_kind", "source_ref", name="uq_operational_task_source"),
        Index(
            "ix_operational_task_scope_time",
            "workspace_type",
            "company_id",
            "user_id",
            "created_at",
        ),
    )


class OperationalAlert(OperationsWorkspaceMixin, Base):
    __tablename__ = "operational_alerts"
    id = Column(String(36), primary_key=True, default=_uuid)
    alert_type = Column(String(40), nullable=False)
    severity = Column(String(20), nullable=False)
    fingerprint = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="open")
    title = Column(String(200), nullable=False)
    detail = Column(JSONB, nullable=False, default=dict)
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "severity IN ('info','warning','critical')",
            name="ck_operational_alert_severity",
        ),
        CheckConstraint(
            "status IN ('open','acknowledged','resolved')",
            name="ck_operational_alert_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_operational_alert_workspace",
        ),
        Index(
            "uq_operational_alert_active_fingerprint",
            "fingerprint",
            unique=True,
            postgresql_where=text("status IN ('open', 'acknowledged')"),
        ),
        Index("ix_operational_alert_scope", "company_id", "status", "severity"),
    )


class AIProviderHealthCheck(OperationsWorkspaceMixin, Base):
    __tablename__ = "ai_provider_health_checks"
    id = Column(String(36), primary_key=True, default=_uuid)
    provider_config_id = Column(
        String(36), ForeignKey("ai_provider_configs.id", ondelete="SET NULL")
    )
    provider = Column(String(80), nullable=False)
    model = Column(String(120), nullable=False)
    status = Column(String(20), nullable=False)
    latency_ms = Column(Integer)
    error_code = Column(String(80))
    safe_message = Column(String(300))
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint(
            "status IN ('healthy','degraded','unavailable')",
            name="ck_ai_provider_health_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_ai_provider_health_workspace",
        ),
        Index("ix_ai_provider_health_config", "provider_config_id", "checked_at"),
    )


class DataOutboundConsent(OperationsWorkspaceMixin, Base):
    __tablename__ = "data_outbound_consents"
    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(
        String(36),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type = Column(String(20), nullable=False)
    provider_host = Column(String(255), nullable=False)
    purpose = Column(String(200), nullable=False)
    privacy_notice_version = Column(String(40), nullable=False)
    privacy_notice_hash = Column(String(64), nullable=False)
    authorized = Column(Boolean, nullable=False, default=False)
    authorized_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    authorized_at = Column(DateTime)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('drawing','pqr','wps','ppqr','welder','unknown')",
            name="ck_data_outbound_document_type",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_data_outbound_workspace",
        ),
        Index(
            "ix_data_outbound_document", "document_id", "provider_host", "authorized"
        ),
    )


class DeploymentProfile(Base):
    __tablename__ = "deployment_profiles"
    id = Column(String(36), primary_key=True, default=_uuid)
    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), unique=True
    )
    deployment_mode = Column(String(20), nullable=False, default="saas")
    network_policy = Column(String(20), nullable=False, default="external_allowed")
    local_ai_base_url = Column(String(500))
    local_ai_model = Column(String(120))
    local_ocr_enabled = Column(Boolean, nullable=False, default=False)
    external_storage_allowed = Column(Boolean, nullable=False, default=True)
    config_snapshot = Column(JSONB, nullable=False, default=dict)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    __table_args__ = (
        CheckConstraint(
            "deployment_mode IN ('saas','private','offline')",
            name="ck_deployment_profile_mode",
        ),
        CheckConstraint(
            "network_policy IN ('external_allowed','allowlist_only','offline')",
            name="ck_deployment_profile_network",
        ),
    )


class BackupVerification(Base):
    __tablename__ = "backup_verifications"
    id = Column(String(36), primary_key=True, default=_uuid)
    backup_ref = Column(String(255), nullable=False)
    manifest_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False)
    coverage = Column(JSONB, nullable=False, default=dict)
    missing_categories = Column(JSONB, nullable=False, default=list)
    restore_tested = Column(Boolean, nullable=False, default=False)
    restore_target = Column(String(100))
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    verified_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text)
    __table_args__ = (
        CheckConstraint(
            "status IN ('passed','failed','partial')",
            name="ck_backup_verification_status",
        ),
        UniqueConstraint(
            "backup_ref", "manifest_hash", name="uq_backup_verification_ref_hash"
        ),
    )


class TenantLifecycleJob(Base):
    __tablename__ = "tenant_lifecycle_jobs"
    id = Column(String(36), primary_key=True, default=_uuid)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"))
    operation = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="requested")
    confirmation = Column(String(200))
    export_manifest = Column(JSONB, nullable=False, default=dict)
    deletion_plan = Column(JSONB, nullable=False, default=dict)
    requested_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    executed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    approved_at = Column(DateTime)
    executed_at = Column(DateTime)
    error_message = Column(Text)
    __table_args__ = (
        CheckConstraint(
            "operation IN ('export','delete')", name="ck_tenant_lifecycle_operation"
        ),
        CheckConstraint(
            "status IN ('requested','approved','processing','completed','failed','cancelled')",
            name="ck_tenant_lifecycle_status",
        ),
        Index("ix_tenant_lifecycle_company", "company_id", "operation", "status"),
    )


class CredentialRotationAudit(Base):
    __tablename__ = "credential_rotation_audits"
    id = Column(String(36), primary_key=True, default=_uuid)
    credential_type = Column(String(30), nullable=False)
    credential_ref = Column(String(100), nullable=False)
    scope_type = Column(String(20), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    old_version = Column(Integer, nullable=False)
    new_version = Column(Integer, nullable=False)
    rotated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    rotated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(String(300))
    __table_args__ = (
        CheckConstraint(
            "credential_type IN ('ai_api_key','jwt','database','redis','storage')",
            name="ck_credential_rotation_type",
        ),
        CheckConstraint(
            "new_version > old_version", name="ck_credential_rotation_version"
        ),
        Index(
            "ix_credential_rotation_ref",
            "credential_type",
            "credential_ref",
            "rotated_at",
        ),
    )

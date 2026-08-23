"""add P8 observability, privacy and tenant lifecycle

Revision ID: add_operations_security_p8
Revises: add_production_release_p7
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_operations_security_p8"
down_revision = "add_production_release_p7"
branch_labels = None
depends_on = None


def scope_columns():
    return [
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("workspace_type", sa.String(20), nullable=False),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "factory_id",
            sa.Integer(),
            sa.ForeignKey("factories.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade():
    op.create_table(
        "operational_task_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_kind", sa.String(20), nullable=False),
        sa.Column("source_ref", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(80)),
        sa.Column("model", sa.String(120)),
        sa.Column("queue_wait_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "estimated_cost_micros", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("error_code", sa.String(80)),
        sa.Column("log_context", postgresql.JSONB(), nullable=False),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        *scope_columns(),
        sa.CheckConstraint(
            "task_kind IN ('ai','ocr','rule','import')", name="ck_operational_task_kind"
        ),
        sa.CheckConstraint(
            "status IN ('queued','processing','completed','failed','cancelled')",
            name="ck_operational_task_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_operational_task_workspace",
        ),
        sa.CheckConstraint(
            "queue_wait_ms >= 0 AND duration_ms >= 0 AND retry_count >= 0 AND total_tokens >= 0 AND estimated_cost_micros >= 0",
            name="ck_operational_task_nonnegative",
        ),
        sa.UniqueConstraint(
            "task_kind", "source_ref", name="uq_operational_task_source"
        ),
    )
    op.create_index(
        "ix_operational_task_scope_time",
        "operational_task_events",
        ["workspace_type", "company_id", "user_id", "created_at"],
    )

    op.create_table(
        "operational_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("alert_type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("detail", postgresql.JSONB(), nullable=False),
        sa.Column(
            "acknowledged_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("acknowledged_at", sa.DateTime()),
        sa.Column("resolved_at", sa.DateTime()),
        *scope_columns(),
        sa.CheckConstraint(
            "severity IN ('info','warning','critical')",
            name="ck_operational_alert_severity",
        ),
        sa.CheckConstraint(
            "status IN ('open','acknowledged','resolved')",
            name="ck_operational_alert_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_operational_alert_workspace",
        ),
        sa.UniqueConstraint(
            "fingerprint", "status", name="uq_operational_alert_fingerprint_status"
        ),
    )
    op.create_index(
        "ix_operational_alert_scope",
        "operational_alerts",
        ["company_id", "status", "severity"],
    )

    op.create_table(
        "ai_provider_health_checks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "provider_config_id",
            sa.String(36),
            sa.ForeignKey("ai_provider_configs.id", ondelete="SET NULL"),
        ),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("error_code", sa.String(80)),
        sa.Column("safe_message", sa.String(300)),
        sa.Column(
            "checked_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        *scope_columns(),
        sa.CheckConstraint(
            "status IN ('healthy','degraded','unavailable')",
            name="ck_ai_provider_health_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_ai_provider_health_workspace",
        ),
    )
    op.create_index(
        "ix_ai_provider_health_config",
        "ai_provider_health_checks",
        ["provider_config_id", "checked_at"],
    )

    op.create_table(
        "data_outbound_consents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(36),
            sa.ForeignKey("source_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(20), nullable=False),
        sa.Column("provider_host", sa.String(255), nullable=False),
        sa.Column("purpose", sa.String(200), nullable=False),
        sa.Column("privacy_notice_version", sa.String(40), nullable=False),
        sa.Column("privacy_notice_hash", sa.String(64), nullable=False),
        sa.Column(
            "authorized", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "authorized_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("authorized_at", sa.DateTime()),
        sa.Column("expires_at", sa.DateTime()),
        sa.Column("revoked_at", sa.DateTime()),
        *scope_columns(),
        sa.CheckConstraint(
            "document_type IN ('drawing','pqr','wps','ppqr','welder','unknown')",
            name="ck_data_outbound_document_type",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_data_outbound_workspace",
        ),
    )
    op.create_index(
        "ix_data_outbound_document",
        "data_outbound_consents",
        ["document_id", "provider_host", "authorized"],
    )

    op.create_table(
        "deployment_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            unique=True,
        ),
        sa.Column(
            "deployment_mode", sa.String(20), nullable=False, server_default="saas"
        ),
        sa.Column(
            "network_policy",
            sa.String(20),
            nullable=False,
            server_default="external_allowed",
        ),
        sa.Column("local_ai_base_url", sa.String(500)),
        sa.Column("local_ai_model", sa.String(120)),
        sa.Column(
            "local_ocr_enabled", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "external_storage_allowed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("config_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "deployment_mode IN ('saas','private','offline')",
            name="ck_deployment_profile_mode",
        ),
        sa.CheckConstraint(
            "network_policy IN ('external_allowed','allowlist_only','offline')",
            name="ck_deployment_profile_network",
        ),
    )

    op.create_table(
        "backup_verifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("backup_ref", sa.String(255), nullable=False),
        sa.Column("manifest_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("coverage", postgresql.JSONB(), nullable=False),
        sa.Column("missing_categories", postgresql.JSONB(), nullable=False),
        sa.Column(
            "restore_tested", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("restore_target", sa.String(100)),
        sa.Column(
            "verified_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "verified_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("notes", sa.Text()),
        sa.CheckConstraint(
            "status IN ('passed','failed','partial')",
            name="ck_backup_verification_status",
        ),
        sa.UniqueConstraint(
            "backup_ref", "manifest_hash", name="uq_backup_verification_ref_hash"
        ),
    )

    op.create_table(
        "tenant_lifecycle_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
        ),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="requested"),
        sa.Column("confirmation", sa.String(200)),
        sa.Column("export_manifest", postgresql.JSONB(), nullable=False),
        sa.Column("deletion_plan", postgresql.JSONB(), nullable=False),
        sa.Column(
            "requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "executed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "requested_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("executed_at", sa.DateTime()),
        sa.Column("error_message", sa.Text()),
        sa.CheckConstraint(
            "operation IN ('export','delete')", name="ck_tenant_lifecycle_operation"
        ),
        sa.CheckConstraint(
            "status IN ('requested','approved','processing','completed','failed','cancelled')",
            name="ck_tenant_lifecycle_status",
        ),
    )
    op.create_index(
        "ix_tenant_lifecycle_company",
        "tenant_lifecycle_jobs",
        ["company_id", "operation", "status"],
    )

    op.create_table(
        "credential_rotation_audits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("credential_type", sa.String(30), nullable=False),
        sa.Column("credential_ref", sa.String(100), nullable=False),
        sa.Column("scope_type", sa.String(20), nullable=False),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("old_version", sa.Integer(), nullable=False),
        sa.Column("new_version", sa.Integer(), nullable=False),
        sa.Column(
            "rotated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "rotated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("reason", sa.String(300)),
        sa.CheckConstraint(
            "credential_type IN ('ai_api_key','jwt','database','redis','storage')",
            name="ck_credential_rotation_type",
        ),
        sa.CheckConstraint(
            "new_version > old_version", name="ck_credential_rotation_version"
        ),
    )
    op.create_index(
        "ix_credential_rotation_ref",
        "credential_rotation_audits",
        ["credential_type", "credential_ref", "rotated_at"],
    )


def downgrade():
    for table in [
        "credential_rotation_audits",
        "tenant_lifecycle_jobs",
        "backup_verifications",
        "deployment_profiles",
        "data_outbound_consents",
        "ai_provider_health_checks",
        "operational_alerts",
        "operational_task_events",
    ]:
        op.drop_table(table)

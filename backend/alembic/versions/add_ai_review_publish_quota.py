"""Add AI membership entitlements and usage ledger.

Revision ID: add_ai_review_publish_quota
Revises: add_ai_extraction_usage
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_ai_review_publish_quota"
down_revision = "add_ai_extraction_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_plan_entitlements (
          id SERIAL PRIMARY KEY,
          tier_key VARCHAR(50) NOT NULL,
          workspace_type VARCHAR(20) NOT NULL,
          monthly_points INTEGER NOT NULL DEFAULT 0,
          max_points_per_task INTEGER NOT NULL DEFAULT 0,
          max_pages_per_task INTEGER NOT NULL DEFAULT 0,
          is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
          created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
          CONSTRAINT ck_ai_entitlement_workspace_type
            CHECK (workspace_type IN ('personal','enterprise')),
          CONSTRAINT ck_ai_entitlement_nonnegative
            CHECK (monthly_points >= 0 AND max_points_per_task >= 0 AND max_pages_per_task >= 0)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_entitlement_tier_workspace
          ON ai_plan_entitlements (tier_key, workspace_type);

        CREATE TABLE IF NOT EXISTS ai_usage_ledgers (
          id VARCHAR(36) PRIMARY KEY,
          job_id VARCHAR(36) REFERENCES extraction_jobs(id) ON DELETE SET NULL,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          workspace_type VARCHAR(20) NOT NULL,
          company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
          factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
          access_level VARCHAR(20) NOT NULL DEFAULT 'private',
          source VARCHAR(20) NOT NULL,
          transaction_type VARCHAR(20) NOT NULL,
          points INTEGER NOT NULL DEFAULT 0,
          balance_delta INTEGER NOT NULL DEFAULT 0,
          input_tokens INTEGER NOT NULL DEFAULT 0,
          output_tokens INTEGER NOT NULL DEFAULT 0,
          total_tokens INTEGER NOT NULL DEFAULT 0,
          ocr_pages INTEGER NOT NULL DEFAULT 0,
          period_start DATE NOT NULL,
          idempotency_key VARCHAR(120) NOT NULL,
          metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
          CONSTRAINT ck_ai_usage_ledger_workspace_type
            CHECK (workspace_type IN ('personal','enterprise')),
          CONSTRAINT ck_ai_usage_ledger_access_level
            CHECK (access_level IN ('private','factory','company','public')),
          CONSTRAINT ck_ai_usage_source CHECK (source IN ('platform','byok')),
          CONSTRAINT ck_ai_usage_transaction_type
            CHECK (transaction_type IN ('reservation','settlement','refund')),
          CONSTRAINT ck_ai_usage_nonnegative
            CHECK (points >= 0 AND input_tokens >= 0 AND output_tokens >= 0 AND total_tokens >= 0 AND ocr_pages >= 0)
        );
        CREATE INDEX IF NOT EXISTS ix_ai_usage_ledgers_job_id
          ON ai_usage_ledgers (job_id);
        CREATE INDEX IF NOT EXISTS ix_ai_usage_ledgers_period_start
          ON ai_usage_ledgers (period_start);
        CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_usage_ledgers_idempotency_key
          ON ai_usage_ledgers (idempotency_key);
        CREATE INDEX IF NOT EXISTS ix_ai_usage_workspace_period
          ON ai_usage_ledgers (workspace_type, company_id, user_id, period_start);

        INSERT INTO ai_plan_entitlements
          (tier_key, workspace_type, monthly_points, max_points_per_task, max_pages_per_task)
        VALUES
          ('free', 'personal', 10, 10, 10),
          ('personal_free', 'personal', 10, 10, 10),
          ('personal_pro', 'personal', 100, 30, 30),
          ('personal_advanced', 'personal', 300, 30, 30),
          ('personal_flagship', 'personal', 1000, 30, 30),
          ('enterprise', 'enterprise', 2000, 30, 30),
          ('enterprise_pro', 'enterprise', 6000, 30, 30),
          ('enterprise_pro_max', 'enterprise', 20000, 30, 30)
        ON CONFLICT (tier_key, workspace_type) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS ai_usage_ledgers;
        DROP TABLE IF EXISTS ai_plan_entitlements;
        """
    )

"""Add encrypted AI provider configurations and enterprise AI policies.

Revision ID: add_ai_provider_configs
Revises: add_ai_review_publish_quota
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_ai_provider_configs"
down_revision = "add_ai_review_publish_quota"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_provider_configs (
          id VARCHAR(36) PRIMARY KEY,
          scope_type VARCHAR(20) NOT NULL,
          user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
          company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
          name VARCHAR(100) NOT NULL,
          provider VARCHAR(80) NOT NULL,
          base_url VARCHAR(500) NOT NULL,
          model VARCHAR(120) NOT NULL,
          encrypted_api_key TEXT NOT NULL,
          key_last_four VARCHAR(8) NOT NULL,
          key_version INTEGER NOT NULL DEFAULT 1,
          is_active BOOLEAN NOT NULL DEFAULT TRUE,
          is_default BOOLEAN NOT NULL DEFAULT FALSE,
          last_test_status VARCHAR(20) NOT NULL DEFAULT 'untested',
          last_tested_at TIMESTAMP WITHOUT TIME ZONE,
          last_error VARCHAR(300),
          created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
          updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
          created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
          CONSTRAINT ck_ai_provider_config_scope
            CHECK (scope_type IN ('personal','enterprise','platform')),
          CONSTRAINT ck_ai_provider_config_owner CHECK (
            (scope_type = 'personal' AND user_id IS NOT NULL AND company_id IS NULL) OR
            (scope_type = 'enterprise' AND user_id IS NULL AND company_id IS NOT NULL) OR
            (scope_type = 'platform' AND user_id IS NULL AND company_id IS NULL)
          ),
          CONSTRAINT ck_ai_provider_config_test_status
            CHECK (last_test_status IN ('untested','success','failed'))
        );
        CREATE INDEX IF NOT EXISTS ix_ai_provider_configs_user_id ON ai_provider_configs(user_id);
        CREATE INDEX IF NOT EXISTS ix_ai_provider_configs_company_id ON ai_provider_configs(company_id);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_provider_personal_name
          ON ai_provider_configs(user_id, name) WHERE scope_type = 'personal' AND is_active;
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_provider_enterprise_name
          ON ai_provider_configs(company_id, name) WHERE scope_type = 'enterprise' AND is_active;
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_provider_platform_name
          ON ai_provider_configs(name) WHERE scope_type = 'platform' AND is_active;

        CREATE TABLE IF NOT EXISTS enterprise_ai_policies (
          id VARCHAR(36) PRIMARY KEY,
          company_id INTEGER NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
          allow_ai BOOLEAN NOT NULL DEFAULT TRUE,
          allow_external_providers BOOLEAN NOT NULL DEFAULT TRUE,
          allow_personal_keys BOOLEAN NOT NULL DEFAULT TRUE,
          require_enterprise_key BOOLEAN NOT NULL DEFAULT FALSE,
          allowed_hosts JSONB NOT NULL DEFAULT '[]'::jsonb,
          created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
          updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
          created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        );

        ALTER TABLE extraction_jobs
          ADD COLUMN IF NOT EXISTS provider_config_id VARCHAR(36);
        CREATE INDEX IF NOT EXISTS ix_extraction_jobs_provider_config_id
          ON extraction_jobs(provider_config_id);
        DO $$ BEGIN
          ALTER TABLE extraction_jobs ADD CONSTRAINT fk_extraction_jobs_provider_config
            FOREIGN KEY (provider_config_id) REFERENCES ai_provider_configs(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE extraction_jobs DROP CONSTRAINT IF EXISTS fk_extraction_jobs_provider_config;
        DROP INDEX IF EXISTS ix_extraction_jobs_provider_config_id;
        ALTER TABLE extraction_jobs DROP COLUMN IF EXISTS provider_config_id;
        DROP TABLE IF EXISTS enterprise_ai_policies;
        DROP TABLE IF EXISTS ai_provider_configs;
        """
    )

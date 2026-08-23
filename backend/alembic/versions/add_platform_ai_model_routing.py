"""Add platform AI model routing and differential point pricing.

Revision ID: add_platform_ai_model_routing
Revises: harden_operations_logic
"""
from alembic import op
import sqlalchemy as sa


revision = "add_platform_ai_model_routing"
down_revision = "harden_operations_logic"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE ai_provider_configs
              ADD COLUMN IF NOT EXISTS task_types JSONB NOT NULL DEFAULT '[]'::jsonb,
              ADD COLUMN IF NOT EXISTS complexity_level VARCHAR(20) NOT NULL DEFAULT 'standard',
              ADD COLUMN IF NOT EXISTS point_multiplier DOUBLE PRECISION NOT NULL DEFAULT 1.0,
              ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 100;
            ALTER TABLE ai_provider_configs
              DROP CONSTRAINT IF EXISTS ck_ai_provider_config_complexity;
            ALTER TABLE ai_provider_configs
              ADD CONSTRAINT ck_ai_provider_config_complexity
              CHECK (complexity_level IN ('simple','standard','advanced'));
            ALTER TABLE ai_provider_configs
              DROP CONSTRAINT IF EXISTS ck_ai_provider_config_routing_values;
            ALTER TABLE ai_provider_configs
              ADD CONSTRAINT ck_ai_provider_config_routing_values
              CHECK (point_multiplier > 0 AND point_multiplier <= 20 AND priority >= 0);
            CREATE INDEX IF NOT EXISTS ix_ai_provider_configs_platform_routing
              ON ai_provider_configs(scope_type, is_active, complexity_level, priority);
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP INDEX IF EXISTS ix_ai_provider_configs_platform_routing;
            ALTER TABLE ai_provider_configs
              DROP CONSTRAINT IF EXISTS ck_ai_provider_config_routing_values,
              DROP CONSTRAINT IF EXISTS ck_ai_provider_config_complexity,
              DROP COLUMN IF EXISTS priority,
              DROP COLUMN IF EXISTS point_multiplier,
              DROP COLUMN IF EXISTS complexity_level,
              DROP COLUMN IF EXISTS task_types;
            """
        )
    )

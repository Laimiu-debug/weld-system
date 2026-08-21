"""Add missing production_plans columns for MVP model alignment.

Revision ID: fix_production_plan_cols
Revises: add_business_mvp_tables
Create Date: 2026-08-21
"""
from alembic import op

revision = "fix_production_plan_cols"
down_revision = "add_business_mvp_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Older environments may have created production_plans before these columns existed.
    # CREATE TABLE IF NOT EXISTS would skip schema updates, so add columns idempotently.
    statements = [
        "ALTER TABLE production_plans ADD COLUMN IF NOT EXISTS priority VARCHAR(50) DEFAULT 'normal'",
        "ALTER TABLE production_plans ADD COLUMN IF NOT EXISTS progress_percentage FLOAT DEFAULT 0",
        "ALTER TABLE production_plans ADD COLUMN IF NOT EXISTS planned_quantity FLOAT",
        "ALTER TABLE production_plans ADD COLUMN IF NOT EXISTS unit VARCHAR(50)",
        "ALTER TABLE production_plans ADD COLUMN IF NOT EXISTS assigned_team VARCHAR(255)",
        "ALTER TABLE production_plans ADD COLUMN IF NOT EXISTS quality_standards TEXT",
    ]
    for sql in statements:
        op.execute(sql)


def downgrade() -> None:
    # Keep data-safe: do not drop columns on downgrade.
    pass

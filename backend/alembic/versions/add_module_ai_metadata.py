"""Add schema version for custom-module AI metadata.

Revision ID: add_module_ai_metadata
Revises: add_user_feedbacks
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_module_ai_metadata"
down_revision = "add_user_feedbacks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE custom_modules "
        "ADD COLUMN IF NOT EXISTS schema_version INTEGER NOT NULL DEFAULT 1"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE custom_modules DROP COLUMN IF EXISTS schema_version")

"""Add provider response and usage fields to extraction jobs.

Revision ID: add_ai_extraction_usage
Revises: add_smart_import_staging
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_ai_extraction_usage"
down_revision = "add_smart_import_staging"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE extraction_jobs
          ADD COLUMN IF NOT EXISTS external_response_id VARCHAR(120),
          ADD COLUMN IF NOT EXISTS input_tokens INTEGER NOT NULL DEFAULT 0,
          ADD COLUMN IF NOT EXISTS output_tokens INTEGER NOT NULL DEFAULT 0,
          ADD COLUMN IF NOT EXISTS total_tokens INTEGER NOT NULL DEFAULT 0;
        CREATE INDEX IF NOT EXISTS ix_extraction_jobs_external_response_id
          ON extraction_jobs (external_response_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_extraction_jobs_external_response_id;
        ALTER TABLE extraction_jobs
          DROP COLUMN IF EXISTS total_tokens,
          DROP COLUMN IF EXISTS output_tokens,
          DROP COLUMN IF EXISTS input_tokens,
          DROP COLUMN IF EXISTS external_response_id;
        """
    )

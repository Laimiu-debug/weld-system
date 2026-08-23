"""Add asynchronous extraction job lifecycle fields.

Revision ID: add_async_extraction_jobs
Revises: add_ai_provider_configs
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_async_extraction_jobs"
down_revision = "add_ai_provider_configs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE extraction_jobs
          ADD COLUMN IF NOT EXISTS retry_of_job_id VARCHAR(36),
          ADD COLUMN IF NOT EXISTS run_ocr BOOLEAN NOT NULL DEFAULT TRUE,
          ADD COLUMN IF NOT EXISTS progress INTEGER NOT NULL DEFAULT 0;
        CREATE INDEX IF NOT EXISTS ix_extraction_jobs_retry_of_job_id
          ON extraction_jobs(retry_of_job_id);
        DO $$ BEGIN
          ALTER TABLE extraction_jobs ADD CONSTRAINT fk_extraction_jobs_retry_of
            FOREIGN KEY (retry_of_job_id) REFERENCES extraction_jobs(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        DO $$ BEGIN
          ALTER TABLE extraction_jobs ADD CONSTRAINT ck_extraction_job_progress
            CHECK (progress >= 0 AND progress <= 100);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        UPDATE extraction_jobs SET progress = CASE
          WHEN status = 'completed' THEN 100
          WHEN status = 'processing' THEN 10
          ELSE 0
        END;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE extraction_jobs DROP CONSTRAINT IF EXISTS ck_extraction_job_progress;
        ALTER TABLE extraction_jobs DROP CONSTRAINT IF EXISTS fk_extraction_jobs_retry_of;
        DROP INDEX IF EXISTS ix_extraction_jobs_retry_of_job_id;
        ALTER TABLE extraction_jobs
          DROP COLUMN IF EXISTS progress,
          DROP COLUMN IF EXISTS run_ocr,
          DROP COLUMN IF EXISTS retry_of_job_id;
        """
    )

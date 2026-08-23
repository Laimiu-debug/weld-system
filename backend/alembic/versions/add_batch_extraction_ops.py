"""Add partial-success lifecycle state for import batches.

Revision ID: add_batch_extraction_ops
Revises: add_async_extraction_jobs
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_batch_extraction_ops"
down_revision = "add_async_extraction_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE import_batches DROP CONSTRAINT IF EXISTS ck_import_batch_status;
        ALTER TABLE import_batches ADD CONSTRAINT ck_import_batch_status CHECK (
          status IN ('draft','queued','processing','review','partial_success','completed','failed','cancelled')
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE import_batches SET status = 'review' WHERE status = 'partial_success';
        ALTER TABLE import_batches DROP CONSTRAINT IF EXISTS ck_import_batch_status;
        ALTER TABLE import_batches ADD CONSTRAINT ck_import_batch_status CHECK (
          status IN ('draft','queued','processing','review','completed','failed','cancelled')
        );
        """
    )

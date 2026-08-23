"""Bind approval instances to immutable version snapshots.

Revision ID: add_approval_version_snapshots
Revises: add_ai_multilevel_limits
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_approval_version_snapshots"
down_revision = "add_ai_multilevel_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql(
        """
        ALTER TABLE approval_instances
          ADD COLUMN document_ref VARCHAR(100),
          ADD COLUMN version_key VARCHAR(100),
          ADD COLUMN version_snapshot JSONB,
          ADD COLUMN snapshot_hash VARCHAR(64);
        ALTER TABLE approval_instances ALTER COLUMN document_id DROP NOT NULL;
        UPDATE approval_instances SET
          document_ref = document_id::text,
          version_key = 'legacy-' || document_id::text,
          version_snapshot = jsonb_build_object(
            'document_type', document_type,
            'document_id', document_id,
            'legacy_snapshot', true
          ),
          snapshot_hash = md5(document_type || ':' || document_id::text || ':legacy');
        ALTER TABLE approval_instances
          ALTER COLUMN document_ref SET NOT NULL,
          ALTER COLUMN version_key SET NOT NULL,
          ALTER COLUMN version_snapshot SET NOT NULL,
          ALTER COLUMN snapshot_hash SET NOT NULL;
        CREATE INDEX ix_approval_document_version
          ON approval_instances(document_type, document_ref, version_key);
        """
    )


def downgrade() -> None:
    op.get_bind().exec_driver_sql(
        """
        DROP INDEX IF EXISTS ix_approval_document_version;
        ALTER TABLE approval_instances
          DROP COLUMN IF EXISTS document_ref,
          DROP COLUMN IF EXISTS version_key,
          DROP COLUMN IF EXISTS version_snapshot,
          DROP COLUMN IF EXISTS snapshot_hash;
        DELETE FROM approval_instances WHERE document_id IS NULL;
        ALTER TABLE approval_instances ALTER COLUMN document_id SET NOT NULL;
        """
    )

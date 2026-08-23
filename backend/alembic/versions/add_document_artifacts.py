"""Add typed document artifact metadata and retention fields.

Revision ID: add_document_artifacts
Revises: add_batch_extraction_ops
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_document_artifacts"
down_revision = "add_batch_extraction_ops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE document_artifacts (
          id VARCHAR(36) PRIMARY KEY,
          document_id VARCHAR(36) NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
          artifact_type VARCHAR(30) NOT NULL,
          storage_key VARCHAR(500), reference_id VARCHAR(100), mime_type VARCHAR(120),
          size_bytes INTEGER NOT NULL DEFAULT 0, sha256 VARCHAR(64),
          retention_class VARCHAR(30) NOT NULL, expires_at TIMESTAMP,
          status VARCHAR(20) NOT NULL DEFAULT 'active', metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
          company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
          factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
          access_level VARCHAR(20) NOT NULL DEFAULT 'private', created_at TIMESTAMP NOT NULL DEFAULT NOW(),
          CONSTRAINT ck_document_artifact_workspace_type CHECK (workspace_type IN ('personal','enterprise')),
          CONSTRAINT ck_document_artifact_access_level CHECK (access_level IN ('private','factory','company','public')),
          CONSTRAINT ck_document_artifact_type CHECK (artifact_type IN ('original','page_preview','ocr_text','extraction_result','formal_export')),
          CONSTRAINT ck_document_artifact_retention CHECK (retention_class IN ('original','temporary','evidence','export')),
          CONSTRAINT ck_document_artifact_status CHECK (status IN ('active','expired','deleted','failed'))
        );
        CREATE INDEX ix_document_artifacts_document_id ON document_artifacts(document_id);
        CREATE INDEX ix_document_artifacts_artifact_type ON document_artifacts(artifact_type);
        CREATE INDEX ix_document_artifacts_status ON document_artifacts(status);
        CREATE INDEX ix_document_artifacts_expires_at ON document_artifacts(expires_at);
        CREATE INDEX ix_document_artifacts_document_type_status ON document_artifacts(document_id, artifact_type, status);
        CREATE INDEX ix_document_artifacts_workspace_expiry ON document_artifacts(workspace_type, company_id, user_id, expires_at);

        INSERT INTO document_artifacts (
          id, document_id, artifact_type, storage_key, mime_type, size_bytes, sha256,
          retention_class, status, metadata_json, user_id, workspace_type,
          company_id, factory_id, access_level, created_at
        )
        SELECT md5(random()::text || clock_timestamp()::text || id), id, 'original',
          storage_key, mime_type, size_bytes, sha256, 'original', 'active',
          jsonb_build_object('filename', original_filename), user_id, workspace_type,
          company_id, factory_id, access_level, created_at
        FROM source_documents;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_artifacts CASCADE")

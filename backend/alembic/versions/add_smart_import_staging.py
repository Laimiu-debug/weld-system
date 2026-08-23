"""Add staged smart-import and evidence tables.

Revision ID: add_smart_import_staging
Revises: add_module_ai_metadata
Create Date: 2026-08-23
"""
from alembic import op


revision = "add_smart_import_staging"
down_revision = "add_module_ai_metadata"
branch_labels = None
depends_on = None


WORKSPACE_COLUMNS = """
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
    access_level VARCHAR(20) NOT NULL DEFAULT 'private'
"""


def upgrade() -> None:
    op.execute(
        f"""
        CREATE TABLE import_batches (
            id VARCHAR(36) PRIMARY KEY, name VARCHAR(200) NOT NULL,
            source_type VARCHAR(30) NOT NULL DEFAULT 'upload',
            target_entity_type VARCHAR(20) NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'draft', progress INTEGER NOT NULL DEFAULT 0,
            total_documents INTEGER NOT NULL DEFAULT 0, processed_documents INTEGER NOT NULL DEFAULT 0,
            error_message TEXT, created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(), {WORKSPACE_COLUMNS},
            CONSTRAINT ck_import_batch_target CHECK (target_entity_type IN ('wps','pqr','ppqr','welder')),
            CONSTRAINT ck_import_batch_status CHECK (status IN ('draft','queued','processing','review','completed','failed','cancelled')),
            CONSTRAINT ck_import_batch_progress CHECK (progress BETWEEN 0 AND 100)
        )
    """
    )
    op.execute(
        f"""
        CREATE TABLE source_documents (
            id VARCHAR(36) PRIMARY KEY, batch_id VARCHAR(36) NOT NULL REFERENCES import_batches(id) ON DELETE CASCADE,
            original_filename VARCHAR(255) NOT NULL, storage_key VARCHAR(500), sha256 VARCHAR(64) NOT NULL,
            mime_type VARCHAR(120), size_bytes INTEGER NOT NULL DEFAULT 0, document_type VARCHAR(20) NOT NULL,
            document_version VARCHAR(50), page_count INTEGER, status VARCHAR(30) NOT NULL DEFAULT 'registered',
            metadata_json JSONB NOT NULL DEFAULT '{{}}'::jsonb, created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(), {WORKSPACE_COLUMNS},
            CONSTRAINT ck_source_document_type CHECK (document_type IN ('wps','pqr','ppqr','welder','unknown')),
            CONSTRAINT ck_source_document_status CHECK (status IN ('registered','stored','parsing','ready','failed','archived'))
        )
    """
    )
    op.execute(
        f"""
        CREATE TABLE document_pages (
            id VARCHAR(36) PRIMARY KEY, document_id VARCHAR(36) NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
            page_number INTEGER NOT NULL, text_content TEXT, ocr_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            page_metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb, created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            {WORKSPACE_COLUMNS}, CONSTRAINT ck_document_page_number CHECK (page_number > 0),
            CONSTRAINT ck_document_page_ocr_status CHECK (ocr_status IN ('pending','processing','completed','failed','not_required')),
            CONSTRAINT uq_document_pages_document_page UNIQUE (document_id, page_number)
        )
    """
    )
    op.execute(
        f"""
        CREATE TABLE extraction_jobs (
            id VARCHAR(36) PRIMARY KEY, document_id VARCHAR(36) NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
            template_id VARCHAR(100), mode VARCHAR(20) NOT NULL DEFAULT 'platform', provider VARCHAR(80), model VARCHAR(120),
            schema_version VARCHAR(40) NOT NULL, schema_snapshot JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            prompt_version VARCHAR(40), request_trace_id VARCHAR(100), status VARCHAR(20) NOT NULL DEFAULT 'queued',
            attempt_count INTEGER NOT NULL DEFAULT 0, error_code VARCHAR(80), error_message TEXT,
            started_at TIMESTAMP, completed_at TIMESTAMP, created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            {WORKSPACE_COLUMNS}, CONSTRAINT ck_extraction_job_mode CHECK (mode IN ('platform','byok','manual','offline')),
            CONSTRAINT ck_extraction_job_status CHECK (status IN ('queued','processing','completed','failed','cancelled'))
        )
    """
    )
    op.execute(
        f"""
        CREATE TABLE extracted_entities (
            id VARCHAR(36) PRIMARY KEY, document_id VARCHAR(36) NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
            job_id VARCHAR(36) REFERENCES extraction_jobs(id) ON DELETE SET NULL, entity_type VARCHAR(20) NOT NULL,
            source_mode VARCHAR(20) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'draft',
            draft_data JSONB NOT NULL DEFAULT '{{}}'::jsonb, version INTEGER NOT NULL DEFAULT 1,
            is_current BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(), {WORKSPACE_COLUMNS},
            CONSTRAINT ck_extracted_entity_type CHECK (entity_type IN ('wps','pqr','ppqr','welder')),
            CONSTRAINT ck_extracted_entity_source CHECK (source_mode IN ('ai','manual','mixed')),
            CONSTRAINT ck_extracted_entity_status CHECK (status IN ('draft','review','approved','published','rejected'))
        )
    """
    )
    op.execute(
        f"""
        CREATE TABLE extracted_fields (
            id VARCHAR(36) PRIMARY KEY, entity_id VARCHAR(36) NOT NULL REFERENCES extracted_entities(id) ON DELETE CASCADE,
            module_id VARCHAR(100), instance_id VARCHAR(100), field_id VARCHAR(36), field_key VARCHAR(150) NOT NULL,
            canonical_field_key VARCHAR(180), raw_value JSONB, normalized_value JSONB, confidence DOUBLE PRECISION,
            review_status VARCHAR(20) NOT NULL DEFAULT 'pending', schema_version VARCHAR(40) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(), updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            {WORKSPACE_COLUMNS}, CONSTRAINT ck_extracted_field_confidence CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
            CONSTRAINT ck_extracted_field_review CHECK (review_status IN ('pending','accepted','corrected','rejected','not_required'))
        )
    """
    )
    op.execute(
        f"""
        CREATE TABLE field_evidence (
            id VARCHAR(36) PRIMARY KEY, extracted_field_id VARCHAR(36) NOT NULL REFERENCES extracted_fields(id) ON DELETE CASCADE,
            page_id VARCHAR(36) REFERENCES document_pages(id) ON DELETE SET NULL, page_number INTEGER NOT NULL,
            evidence_type VARCHAR(20) NOT NULL DEFAULT 'text', text_excerpt TEXT NOT NULL, bbox JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(), {WORKSPACE_COLUMNS},
            CONSTRAINT ck_field_evidence_page CHECK (page_number > 0),
            CONSTRAINT ck_field_evidence_type CHECK (evidence_type IN ('text','ocr','table','visual','manual'))
        )
    """
    )
    op.execute(
        f"""
        CREATE TABLE import_review_records (
            id VARCHAR(36) PRIMARY KEY, entity_id VARCHAR(36) NOT NULL REFERENCES extracted_entities(id) ON DELETE CASCADE,
            extracted_field_id VARCHAR(36) REFERENCES extracted_fields(id) ON DELETE SET NULL, action VARCHAR(30) NOT NULL,
            previous_value JSONB, new_value JSONB, reason TEXT,
            reviewer_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            {WORKSPACE_COLUMNS}, CONSTRAINT ck_import_review_action CHECK (action IN ('accept','correct','reject','submit','approve','reopen'))
        )
    """
    )
    op.execute(
        f"""
        CREATE TABLE entity_publish_records (
            id VARCHAR(36) PRIMARY KEY, entity_id VARCHAR(36) NOT NULL REFERENCES extracted_entities(id) ON DELETE CASCADE,
            target_entity_type VARCHAR(20) NOT NULL, target_entity_id VARCHAR(100) NOT NULL,
            published_snapshot JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            published_by INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            {WORKSPACE_COLUMNS}, CONSTRAINT ck_publish_target_type CHECK (target_entity_type IN ('wps','pqr','ppqr','welder')),
            CONSTRAINT uq_entity_publish_target UNIQUE (entity_id, target_entity_type, target_entity_id)
        )
    """
    )

    indexes = (
        "CREATE INDEX ix_import_batches_workspace_created ON import_batches(workspace_type, company_id, user_id, created_at)",
        "CREATE INDEX ix_source_documents_batch_id ON source_documents(batch_id)",
        "CREATE INDEX ix_source_documents_workspace_hash ON source_documents(workspace_type, company_id, user_id, sha256)",
        "CREATE INDEX ix_document_pages_document_id ON document_pages(document_id)",
        "CREATE INDEX ix_extraction_jobs_document_id ON extraction_jobs(document_id)",
        "CREATE INDEX ix_extraction_jobs_trace ON extraction_jobs(request_trace_id)",
        "CREATE INDEX ix_extracted_entities_document_current ON extracted_entities(document_id, is_current)",
        "CREATE INDEX ix_extracted_fields_entity_field ON extracted_fields(entity_id, field_id, field_key)",
        "CREATE INDEX ix_field_evidence_field_id ON field_evidence(extracted_field_id)",
        "CREATE INDEX ix_import_review_entity_id ON import_review_records(entity_id)",
        "CREATE INDEX ix_entity_publish_entity_id ON entity_publish_records(entity_id)",
    )
    for statement in indexes:
        op.execute(statement)

    workspace_tables = {
        "import_batches": "import_batch",
        "source_documents": "source_document",
        "document_pages": "document_page",
        "extraction_jobs": "extraction_job",
        "extracted_entities": "extracted_entity",
        "extracted_fields": "extracted_field",
        "field_evidence": "field_evidence",
        "import_review_records": "import_review",
        "entity_publish_records": "entity_publish",
    }
    for table, prefix in workspace_tables.items():
        op.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT ck_{prefix}_workspace_type "
            "CHECK (workspace_type IN ('personal','enterprise'))"
        )
        op.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT ck_{prefix}_access_level "
            "CHECK (access_level IN ('private','factory','company','public'))"
        )


def downgrade() -> None:
    for table in (
        "entity_publish_records",
        "import_review_records",
        "field_evidence",
        "extracted_fields",
        "extracted_entities",
        "extraction_jobs",
        "document_pages",
        "source_documents",
        "import_batches",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

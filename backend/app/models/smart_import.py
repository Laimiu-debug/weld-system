"""Models for staged, auditable document import."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


def _uuid() -> str:
    return str(uuid4())


def _workspace_constraints(prefix: str) -> tuple[CheckConstraint, CheckConstraint]:
    return (
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name=f"ck_{prefix}_workspace_type",
        ),
        CheckConstraint(
            "access_level IN ('private','factory','company','public')",
            name=f"ck_{prefix}_access_level",
        ),
    )


class WorkspaceOwnedMixin:
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workspace_type = Column(String(20), nullable=False, default="personal")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"))
    access_level = Column(String(20), nullable=False, default="private")


class ImportBatch(WorkspaceOwnedMixin, Base):
    __tablename__ = "import_batches"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(200), nullable=False)
    source_type = Column(String(30), nullable=False, default="upload")
    target_entity_type = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False, default="draft", index=True)
    progress = Column(Integer, nullable=False, default=0)
    total_documents = Column(Integer, nullable=False, default=0)
    processed_documents = Column(Integer, nullable=False, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        *_workspace_constraints("import_batch"),
        CheckConstraint(
            "target_entity_type IN ('wps','pqr','ppqr','welder')",
            name="ck_import_batch_target",
        ),
        CheckConstraint(
            "status IN ('draft','queued','processing','review','completed','failed','cancelled')",
            name="ck_import_batch_status",
        ),
        CheckConstraint(
            "progress >= 0 AND progress <= 100", name="ck_import_batch_progress"
        ),
        Index(
            "ix_import_batches_workspace_created",
            "workspace_type",
            "company_id",
            "user_id",
            "created_at",
        ),
    )


class SourceDocument(WorkspaceOwnedMixin, Base):
    __tablename__ = "source_documents"

    id = Column(String(36), primary_key=True, default=_uuid)
    batch_id = Column(
        String(36),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename = Column(String(255), nullable=False)
    storage_key = Column(String(500))
    sha256 = Column(String(64), nullable=False, index=True)
    mime_type = Column(String(120))
    size_bytes = Column(Integer, nullable=False, default=0)
    document_type = Column(String(20), nullable=False)
    document_version = Column(String(50))
    page_count = Column(Integer)
    status = Column(String(30), nullable=False, default="registered", index=True)
    metadata_json = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        *_workspace_constraints("source_document"),
        CheckConstraint(
            "document_type IN ('wps','pqr','ppqr','welder','unknown')",
            name="ck_source_document_type",
        ),
        CheckConstraint(
            "status IN ('registered','stored','parsing','ready','failed','archived')",
            name="ck_source_document_status",
        ),
        Index(
            "ix_source_documents_workspace_hash",
            "workspace_type",
            "company_id",
            "user_id",
            "sha256",
        ),
    )


class DocumentPage(WorkspaceOwnedMixin, Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(
        String(36),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text)
    ocr_status = Column(String(20), nullable=False, default="pending")
    page_metadata = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        *_workspace_constraints("document_page"),
        CheckConstraint("page_number > 0", name="ck_document_page_number"),
        CheckConstraint(
            "ocr_status IN ('pending','processing','completed','failed','not_required')",
            name="ck_document_page_ocr_status",
        ),
        Index(
            "uq_document_pages_document_page", "document_id", "page_number", unique=True
        ),
    )


class ExtractionJob(WorkspaceOwnedMixin, Base):
    __tablename__ = "extraction_jobs"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(
        String(36),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id = Column(String(100))
    mode = Column(String(20), nullable=False, default="platform")
    provider = Column(String(80))
    model = Column(String(120))
    schema_version = Column(String(40), nullable=False)
    schema_snapshot = Column(JSONB, nullable=False, default=dict)
    prompt_version = Column(String(40))
    request_trace_id = Column(String(100), index=True)
    external_response_id = Column(String(120), index=True)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="queued", index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    error_code = Column(String(80))
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        *_workspace_constraints("extraction_job"),
        CheckConstraint(
            "mode IN ('platform','byok','manual','offline')",
            name="ck_extraction_job_mode",
        ),
        CheckConstraint(
            "status IN ('queued','processing','completed','failed','cancelled')",
            name="ck_extraction_job_status",
        ),
    )


class ExtractedEntity(WorkspaceOwnedMixin, Base):
    __tablename__ = "extracted_entities"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(
        String(36),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id = Column(
        String(36), ForeignKey("extraction_jobs.id", ondelete="SET NULL"), index=True
    )
    entity_type = Column(String(20), nullable=False)
    source_mode = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)
    draft_data = Column(JSONB, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        *_workspace_constraints("extracted_entity"),
        CheckConstraint(
            "entity_type IN ('wps','pqr','ppqr','welder')",
            name="ck_extracted_entity_type",
        ),
        CheckConstraint(
            "source_mode IN ('ai','manual','mixed')", name="ck_extracted_entity_source"
        ),
        CheckConstraint(
            "status IN ('draft','review','approved','published','rejected')",
            name="ck_extracted_entity_status",
        ),
        Index("ix_extracted_entities_document_current", "document_id", "is_current"),
    )


class ExtractedField(WorkspaceOwnedMixin, Base):
    __tablename__ = "extracted_fields"

    id = Column(String(36), primary_key=True, default=_uuid)
    entity_id = Column(
        String(36),
        ForeignKey("extracted_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_id = Column(String(100))
    instance_id = Column(String(100))
    field_id = Column(String(36))
    field_key = Column(String(150), nullable=False)
    canonical_field_key = Column(String(180))
    raw_value = Column(JSONB)
    normalized_value = Column(JSONB)
    confidence = Column(Float)
    review_status = Column(String(20), nullable=False, default="pending", index=True)
    schema_version = Column(String(40), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        *_workspace_constraints("extracted_field"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_extracted_field_confidence",
        ),
        CheckConstraint(
            "review_status IN ('pending','accepted','corrected','rejected','not_required')",
            name="ck_extracted_field_review",
        ),
        Index("ix_extracted_fields_entity_field", "entity_id", "field_id", "field_key"),
    )


class FieldEvidence(WorkspaceOwnedMixin, Base):
    __tablename__ = "field_evidence"

    id = Column(String(36), primary_key=True, default=_uuid)
    extracted_field_id = Column(
        String(36),
        ForeignKey("extracted_fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_id = Column(String(36), ForeignKey("document_pages.id", ondelete="SET NULL"))
    page_number = Column(Integer, nullable=False)
    evidence_type = Column(String(20), nullable=False, default="text")
    text_excerpt = Column(Text, nullable=False)
    bbox = Column(JSONB)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        *_workspace_constraints("field_evidence"),
        CheckConstraint("page_number > 0", name="ck_field_evidence_page"),
        CheckConstraint(
            "evidence_type IN ('text','ocr','table','visual','manual')",
            name="ck_field_evidence_type",
        ),
    )


class ImportReviewRecord(WorkspaceOwnedMixin, Base):
    __tablename__ = "import_review_records"

    id = Column(String(36), primary_key=True, default=_uuid)
    entity_id = Column(
        String(36),
        ForeignKey("extracted_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    extracted_field_id = Column(
        String(36), ForeignKey("extracted_fields.id", ondelete="SET NULL"), index=True
    )
    action = Column(String(30), nullable=False)
    previous_value = Column(JSONB)
    new_value = Column(JSONB)
    reason = Column(Text)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        *_workspace_constraints("import_review"),
        CheckConstraint(
            "action IN ('accept','correct','reject','submit','approve','reopen')",
            name="ck_import_review_action",
        ),
    )


class EntityPublishRecord(WorkspaceOwnedMixin, Base):
    __tablename__ = "entity_publish_records"

    id = Column(String(36), primary_key=True, default=_uuid)
    entity_id = Column(
        String(36),
        ForeignKey("extracted_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_entity_type = Column(String(20), nullable=False)
    target_entity_id = Column(String(100), nullable=False)
    published_snapshot = Column(JSONB, nullable=False, default=dict)
    published_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        *_workspace_constraints("entity_publish"),
        CheckConstraint(
            "target_entity_type IN ('wps','pqr','ppqr','welder')",
            name="ck_publish_target_type",
        ),
        Index(
            "uq_entity_publish_target",
            "entity_id",
            "target_entity_type",
            "target_entity_id",
            unique=True,
        ),
    )

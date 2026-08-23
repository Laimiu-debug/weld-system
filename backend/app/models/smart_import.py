"""Models for staged, auditable document import."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
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
            "target_entity_type IN ('wps','pqr','ppqr','welder','drawing')",
            name="ck_import_batch_target",
        ),
        CheckConstraint(
            "status IN ('draft','queued','processing','review','partial_success','completed','failed','cancelled')",
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
            "document_type IN ('wps','pqr','ppqr','welder','drawing','unknown')",
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


class DocumentArtifact(WorkspaceOwnedMixin, Base):
    """Typed original, derived, evidence, and export artifacts."""

    __tablename__ = "document_artifacts"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(
        String(36),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_type = Column(String(30), nullable=False, index=True)
    storage_key = Column(String(500))
    reference_id = Column(String(100))
    mime_type = Column(String(120))
    size_bytes = Column(Integer, nullable=False, default=0)
    sha256 = Column(String(64))
    retention_class = Column(String(30), nullable=False)
    expires_at = Column(DateTime, index=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    metadata_json = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        *_workspace_constraints("document_artifact"),
        CheckConstraint(
            "artifact_type IN ('original','page_preview','ocr_text','extraction_result','formal_export')",
            name="ck_document_artifact_type",
        ),
        CheckConstraint(
            "retention_class IN ('original','temporary','evidence','export')",
            name="ck_document_artifact_retention",
        ),
        CheckConstraint(
            "status IN ('active','expired','deleted','failed')",
            name="ck_document_artifact_status",
        ),
        Index(
            "ix_document_artifacts_document_type_status",
            "document_id",
            "artifact_type",
            "status",
        ),
        Index(
            "ix_document_artifacts_workspace_expiry",
            "workspace_type",
            "company_id",
            "user_id",
            "expires_at",
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
    provider_config_id = Column(
        String(36),
        ForeignKey("ai_provider_configs.id", ondelete="SET NULL"),
        index=True,
    )
    retry_of_job_id = Column(
        String(36), ForeignKey("extraction_jobs.id", ondelete="SET NULL"), index=True
    )
    run_ocr = Column(Boolean, nullable=False, default=True)
    progress = Column(Integer, nullable=False, default=0)
    progress_detail = Column(JSONB, nullable=False, default=dict)
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
        CheckConstraint(
            "progress >= 0 AND progress <= 100", name="ck_extraction_job_progress"
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


class AIPlanEntitlement(Base):
    __tablename__ = "ai_plan_entitlements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tier_key = Column(String(50), nullable=False)
    workspace_type = Column(String(20), nullable=False)
    daily_points = Column(Integer, nullable=False, default=0)
    monthly_points = Column(Integer, nullable=False, default=0)
    max_points_per_task = Column(Integer, nullable=False, default=0)
    max_pages_per_task = Column(Integer, nullable=False, default=0)
    max_tasks_per_day = Column(Integer, nullable=False, default=0)
    max_tasks_per_month = Column(Integer, nullable=False, default=0)
    max_concurrent_tasks = Column(Integer, nullable=False, default=0)
    max_user_tasks_per_day = Column(Integer, nullable=False, default=0)
    max_user_tasks_per_month = Column(Integer, nullable=False, default=0)
    max_user_concurrent_tasks = Column(Integer, nullable=False, default=0)
    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_ai_entitlement_workspace_type",
        ),
        CheckConstraint(
            "daily_points >= 0 AND monthly_points >= 0 AND max_points_per_task >= 0 "
            "AND max_pages_per_task >= 0 AND max_tasks_per_day >= 0 "
            "AND max_tasks_per_month >= 0 AND max_concurrent_tasks >= 0 "
            "AND max_user_tasks_per_day >= 0 AND max_user_tasks_per_month >= 0 "
            "AND max_user_concurrent_tasks >= 0",
            name="ck_ai_entitlement_nonnegative",
        ),
        Index(
            "uq_ai_entitlement_tier_workspace",
            "tier_key",
            "workspace_type",
            unique=True,
        ),
    )


class AIProviderConfig(Base):
    """Encrypted user/company credentials; ciphertext is never exposed by schemas."""

    __tablename__ = "ai_provider_configs"

    id = Column(String(36), primary_key=True, default=_uuid)
    scope_type = Column(String(20), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    name = Column(String(100), nullable=False)
    provider = Column(String(80), nullable=False)
    base_url = Column(String(500), nullable=False)
    model = Column(String(120), nullable=False)
    encrypted_api_key = Column(Text, nullable=False)
    key_last_four = Column(String(8), nullable=False)
    key_version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    last_test_status = Column(String(20), nullable=False, default="untested")
    last_tested_at = Column(DateTime)
    last_error = Column(String(300))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "scope_type IN ('personal','enterprise','platform')",
            name="ck_ai_provider_config_scope",
        ),
        CheckConstraint(
            "(scope_type = 'personal' AND user_id IS NOT NULL AND company_id IS NULL) OR "
            "(scope_type = 'enterprise' AND user_id IS NULL AND company_id IS NOT NULL) OR "
            "(scope_type = 'platform' AND user_id IS NULL AND company_id IS NULL)",
            name="ck_ai_provider_config_owner",
        ),
        CheckConstraint(
            "last_test_status IN ('untested','success','failed')",
            name="ck_ai_provider_config_test_status",
        ),
    )


class EnterpriseAIPolicy(Base):
    __tablename__ = "enterprise_ai_policies"

    id = Column(String(36), primary_key=True, default=_uuid)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    allow_ai = Column(Boolean, nullable=False, default=True)
    allow_external_providers = Column(Boolean, nullable=False, default=True)
    allow_personal_keys = Column(Boolean, nullable=False, default=True)
    require_enterprise_key = Column(Boolean, nullable=False, default=False)
    allowed_hosts = Column(JSONB, nullable=False, default=list)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AIUsageLedger(WorkspaceOwnedMixin, Base):
    __tablename__ = "ai_usage_ledgers"

    id = Column(String(36), primary_key=True, default=_uuid)
    job_id = Column(
        String(36),
        ForeignKey("extraction_jobs.id", ondelete="SET NULL"),
        index=True,
    )
    source = Column(String(20), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    points = Column(Integer, nullable=False, default=0)
    balance_delta = Column(Integer, nullable=False, default=0)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    ocr_pages = Column(Integer, nullable=False, default=0)
    period_start = Column(Date, nullable=False, index=True)
    idempotency_key = Column(String(120), nullable=False, unique=True)
    metadata_json = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        *_workspace_constraints("ai_usage_ledger"),
        CheckConstraint("source IN ('platform','byok')", name="ck_ai_usage_source"),
        CheckConstraint(
            "transaction_type IN ('reservation','settlement','refund')",
            name="ck_ai_usage_transaction_type",
        ),
        CheckConstraint(
            "points >= 0 AND input_tokens >= 0 AND output_tokens >= 0 AND total_tokens >= 0 AND ocr_pages >= 0",
            name="ck_ai_usage_nonnegative",
        ),
        Index(
            "ix_ai_usage_workspace_period",
            "workspace_type",
            "company_id",
            "user_id",
            "period_start",
        ),
    )

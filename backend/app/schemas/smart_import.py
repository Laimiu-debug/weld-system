"""Schemas for staged smart-import APIs."""
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


EntityType = Literal["wps", "pqr", "ppqr", "welder"]


class ImportBatchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    target_entity_type: EntityType
    source_type: Literal["upload", "manual", "migration"] = "upload"
    access_level: Literal["private", "factory", "company"] = "private"


class ImportBatchResponse(BaseModel):
    id: str
    name: str
    source_type: str
    target_entity_type: str
    status: str
    progress: int
    total_documents: int
    processed_documents: int
    workspace_type: str
    company_id: int | None
    factory_id: int | None
    access_level: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceDocumentRegister(BaseModel):
    original_filename: str = Field(min_length=1, max_length=255)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    document_type: Literal["wps", "pqr", "ppqr", "welder", "unknown"]
    mime_type: str | None = Field(None, max_length=120)
    size_bytes: int = Field(default=0, ge=0)
    document_version: str | None = Field(None, max_length=50)
    storage_key: str | None = Field(None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("original_filename")
    @classmethod
    def filename_must_not_contain_path(cls, value: str) -> str:
        if "/" in value or "\\" in value or value in {".", ".."}:
            raise ValueError("文件名不能包含路径")
        return value


class SourceDocumentResponse(BaseModel):
    id: str
    batch_id: str
    original_filename: str
    sha256: str
    mime_type: str | None
    size_bytes: int
    document_type: str
    document_version: str | None
    page_count: int | None
    status: str
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentPageResponse(BaseModel):
    id: str
    document_id: str
    page_number: int
    text_content: str | None
    ocr_status: str
    page_metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentArtifactResponse(BaseModel):
    id: str
    document_id: str
    artifact_type: str
    reference_id: str | None
    mime_type: str | None
    size_bytes: int
    sha256: str | None
    retention_class: str
    expires_at: datetime | None
    status: str
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentParseResponse(BaseModel):
    document: SourceDocumentResponse
    pages: list[DocumentPageResponse]


class EvidenceDraft(BaseModel):
    page_number: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=2000)
    bbox: list[float] | None = Field(None, min_length=4, max_length=4)


class ManualFieldDraft(BaseModel):
    field_key: str = Field(min_length=1, max_length=150)
    value: Any = None
    module_id: str | None = Field(None, max_length=100)
    instance_id: str | None = Field(None, max_length=100)
    field_id: str | None = Field(None, max_length=36)
    canonical_field_key: str | None = Field(None, max_length=180)
    evidence: list[EvidenceDraft] = Field(default_factory=list)


class ManualDraftCreate(BaseModel):
    entity_type: EntityType
    schema_version: str = Field(min_length=1, max_length=40)
    schema_snapshot: dict[str, Any] = Field(default_factory=dict)
    draft_data: dict[str, Any] = Field(default_factory=dict)
    fields: list[ManualFieldDraft] = Field(default_factory=list, max_length=500)


class ManualWorkbenchFieldCreate(BaseModel):
    target_field_id: str | None = Field(None, max_length=36)
    target_module_id: str | None = Field(None, max_length=100)
    target_instance_id: str | None = Field(None, max_length=100)
    target_field_key: str = Field(min_length=1, max_length=150)
    value: Any = None
    reason: str | None = Field(None, max_length=1000)


class ExtractedEntityResponse(BaseModel):
    id: str
    document_id: str
    job_id: str | None
    entity_type: str
    source_mode: str
    status: str
    draft_data: dict[str, Any]
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FieldEvidenceResponse(BaseModel):
    id: str
    page_number: int
    evidence_type: str
    text_excerpt: str
    bbox: list[float] | None

    model_config = {"from_attributes": True}


class ExtractedFieldResponse(BaseModel):
    id: str
    module_id: str | None
    instance_id: str | None
    field_id: str | None
    field_key: str
    canonical_field_key: str | None
    raw_value: Any
    normalized_value: Any
    confidence: float | None
    review_status: str
    schema_version: str
    evidence: list[FieldEvidenceResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ExtractedEntityDetailResponse(ExtractedEntityResponse):
    fields: list[ExtractedFieldResponse] = Field(default_factory=list)


class FieldReviewRequest(BaseModel):
    action: Literal["accept", "correct", "reject"]
    value: Any = None
    reason: str | None = Field(None, max_length=1000)


class BulkFieldAcceptRequest(BaseModel):
    field_ids: list[str] = Field(default_factory=list, max_length=500)
    minimum_confidence: float | None = Field(None, ge=0, le=1)


class ImportReviewRecordResponse(BaseModel):
    id: str
    entity_id: str
    extracted_field_id: str | None
    action: str
    previous_value: Any
    new_value: Any
    reason: str | None
    reviewer_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EntityPublishResponse(BaseModel):
    entity_id: str
    target_entity_type: str
    target_entity_id: str
    status: str
    detail_url: str


class WelderImportDecision(BaseModel):
    record_key: str = Field(min_length=1, max_length=500)
    existing_welder_id: int | None = Field(None, gt=0)
    create_new: bool = False
    skip_duplicate: bool = False

    @model_validator(mode="after")
    def validate_identity_choice(self):
        if self.existing_welder_id is not None and self.create_new:
            raise ValueError("不能同时选择现有焊工和新建焊工")
        return self


class WelderImportPublishRequest(BaseModel):
    decisions: list[WelderImportDecision] = Field(default_factory=list, max_length=1000)


class WelderImportReviewResponse(BaseModel):
    entity_id: str
    records: list[dict[str, Any]] = Field(default_factory=list)


class UnmappedFieldBindRequest(BaseModel):
    action: Literal["bind_existing", "create_custom"]
    target_field_id: str | None = Field(None, max_length=100)
    target_module_id: str | None = Field(None, max_length=100)
    target_instance_id: str | None = Field(None, max_length=100)
    target_field_key: str | None = Field(None, max_length=150)
    field_label: str | None = Field(None, min_length=1, max_length=200)
    field_key: str | None = Field(None, min_length=1, max_length=150)
    field_type: Literal["text", "number", "date", "textarea"] = "text"
    module_name: str | None = Field(None, min_length=1, max_length=200)
    existing_custom_module_id: str | None = Field(None, max_length=100)

    @model_validator(mode="after")
    def validate_binding_action(self):
        if self.action == "bind_existing" and not (
            self.target_field_id or (self.target_module_id and self.target_field_key)
        ):
            raise ValueError("绑定已有字段时必须选择目标字段")
        if self.action == "create_custom" and not self.field_label:
            raise ValueError("创建自定义字段时必须填写字段名称")
        return self


class WorkbenchValidationResponse(BaseModel):
    entity_id: str
    can_publish: bool
    counts: dict[str, int] = Field(default_factory=dict)
    issues: list[dict[str, Any]] = Field(default_factory=list)
    field_states: dict[str, dict[str, Any]] = Field(default_factory=dict)
    binding_options: list[dict[str, Any]] = Field(default_factory=list)


class TemplateRecommendationItem(BaseModel):
    template_id: str
    name: str
    score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    welding_process: str | None = None
    standard: str | None = None


class DocumentClassification(BaseModel):
    document_type: str
    confidence: float = Field(ge=0, le=1)
    declared_type: str
    detected_processes: list[str] = Field(default_factory=list)
    detected_standards: list[str] = Field(default_factory=list)
    requires_confirmation: bool


class TemplateRecommendationResponse(BaseModel):
    classification: DocumentClassification
    recommendations: list[TemplateRecommendationItem] = Field(default_factory=list)


class SupportingPQRMatch(BaseModel):
    pqr_id: int
    pqr_number: str
    title: str
    status: str
    score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    eligible: bool


class FormHandoffResponse(BaseModel):
    entity_id: str
    entity_type: EntityType
    template_id: str | None = None
    form_values: dict[str, Any] = Field(default_factory=dict)
    supporting_pqr_candidates: list[SupportingPQRMatch] = Field(default_factory=list)


class FormPublishRequest(BaseModel):
    payload: dict[str, Any]
    supporting_pqr_decision: Literal[
        "matched", "no_match", "not_required"
    ] = "not_required"
    supporting_pqr_id: int | None = None

    @model_validator(mode="after")
    def validate_supporting_pqr(self):
        if self.supporting_pqr_decision == "matched" and self.supporting_pqr_id is None:
            raise ValueError("确认匹配时必须选择支持 PQR")
        if (
            self.supporting_pqr_decision != "matched"
            and self.supporting_pqr_id is not None
        ):
            raise ValueError("未选择匹配时不能提交支持 PQR ID")
        return self


class AIQuotaStatusResponse(BaseModel):
    tier_key: str
    workspace_type: str
    monthly_points: int
    daily_points: int
    daily_used_points: int
    daily_remaining_points: int
    used_points: int
    reserved_or_used_points: int
    remaining_points: int
    max_points_per_task: int
    max_pages_per_task: int
    max_tasks_per_day: int
    max_tasks_per_month: int
    max_concurrent_tasks: int
    max_user_tasks_per_day: int
    max_user_tasks_per_month: int
    max_user_concurrent_tasks: int
    tasks_today: int
    tasks_month: int
    active_tasks: int
    user_tasks_today: int
    user_tasks_month: int
    user_active_tasks: int
    period_start: date
    platform_enabled: bool
    estimated_points: int | None = None
    can_run_estimate: bool | None = None


class AIExtractionRequest(BaseModel):
    mode: Literal["platform", "byok"] = "platform"
    provider: Literal["openai_responses", "openai_compatible_chat"] | None = None
    model: str | None = Field(None, min_length=1, max_length=120)
    base_url: str | None = Field(None, min_length=8, max_length=500)
    api_key: SecretStr | None = Field(None, repr=False)
    provider_config_id: str | None = Field(None, max_length=36)
    template_id: str | None = Field(None, max_length=100)
    module_id: str | None = Field(None, max_length=100)
    run_ocr: bool = True

    @model_validator(mode="after")
    def validate_credential_source(self):
        if self.mode == "byok" and self.provider_config_id and self.api_key:
            raise ValueError("已保存配置与临时 API Key 不能同时使用")
        return self


class AIProviderConfigCreate(BaseModel):
    scope_type: Literal["personal", "enterprise"] = "personal"
    name: str = Field(min_length=1, max_length=100)
    provider: Literal["openai_responses", "openai_compatible_chat"]
    base_url: str = Field(
        default="https://api.openai.com/v1", min_length=8, max_length=500
    )
    model: str = Field(min_length=1, max_length=120)
    api_key: SecretStr = Field(repr=False)
    is_default: bool = False


class AIProviderConfigUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    provider: Literal["openai_responses", "openai_compatible_chat"] | None = None
    base_url: str | None = Field(None, min_length=8, max_length=500)
    model: str | None = Field(None, min_length=1, max_length=120)
    is_default: bool | None = None


class AIProviderKeyRotate(BaseModel):
    api_key: SecretStr = Field(repr=False)


class AIProviderConfigResponse(BaseModel):
    id: str
    scope_type: str
    name: str
    provider: str
    base_url: str
    model: str
    masked_api_key: str
    key_version: int
    is_active: bool
    is_default: bool
    last_test_status: str
    last_tested_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class EnterpriseAIPolicyUpdate(BaseModel):
    allow_ai: bool = True
    allow_external_providers: bool = True
    allow_personal_keys: bool = True
    require_enterprise_key: bool = False
    allowed_hosts: list[str] = Field(default_factory=list, max_length=50)


class EnterpriseAIPolicyResponse(EnterpriseAIPolicyUpdate):
    company_id: int
    updated_at: datetime | None = None


class ExtractionJobResponse(BaseModel):
    id: str
    document_id: str
    mode: str
    provider: str | None
    model: str | None
    provider_config_id: str | None
    retry_of_job_id: str | None
    template_id: str | None = None
    progress: int
    progress_detail: dict[str, Any] = Field(default_factory=dict)
    status: str
    schema_version: str
    request_trace_id: str | None
    external_response_id: str | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    error_code: str | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIExtractionQueuedResponse(BaseModel):
    job: ExtractionJobResponse
    message: str = "任务已进入后台队列"


class BatchAIExtractionRequest(AIExtractionRequest):
    document_ids: list[str] = Field(default_factory=list, max_length=100)


class BatchOperationItem(BaseModel):
    document_id: str
    resource_id: str | None = None
    status: Literal["queued", "published", "skipped", "failed"]
    message: str | None = None


class BatchOperationResponse(BaseModel):
    batch_id: str
    succeeded: int
    failed: int
    skipped: int
    items: list[BatchOperationItem]


class AIExtractionResponse(BaseModel):
    job: ExtractionJobResponse
    entity: ExtractedEntityDetailResponse
    pages: list[DocumentPageResponse]


class BatchDetailResponse(ImportBatchResponse):
    documents: list[SourceDocumentResponse] = Field(default_factory=list)

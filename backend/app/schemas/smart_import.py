"""Schemas for staged smart-import APIs."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr, field_validator


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


class AIExtractionRequest(BaseModel):
    mode: Literal["platform", "byok"] = "platform"
    provider: Literal["openai_responses", "openai_compatible_chat"] | None = None
    model: str | None = Field(None, min_length=1, max_length=120)
    base_url: str | None = Field(None, min_length=8, max_length=500)
    api_key: SecretStr | None = Field(None, repr=False)
    template_id: str | None = Field(None, max_length=100)
    module_id: str | None = Field(None, max_length=100)
    run_ocr: bool = True


class ExtractionJobResponse(BaseModel):
    id: str
    document_id: str
    mode: str
    provider: str | None
    model: str | None
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


class AIExtractionResponse(BaseModel):
    job: ExtractionJobResponse
    entity: ExtractedEntityResponse
    pages: list[DocumentPageResponse]


class BatchDetailResponse(ImportBatchResponse):
    documents: list[SourceDocumentResponse] = Field(default_factory=list)

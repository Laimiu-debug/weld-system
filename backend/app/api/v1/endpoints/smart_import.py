"""Smart-import extraction, review, and controlled publication endpoints."""
import logging
from datetime import datetime
from types import SimpleNamespace
from typing import Iterator, Optional
from urllib.parse import quote, urlsplit

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api import deps
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit
from app.core.module_permissions import ensure_module_permission
from app.models.smart_import import (
    ExtractedEntity,
    ExtractedField,
    ExtractionJob,
    FieldEvidence,
    ImportReviewRecord,
)
from app.models.user import User
from app.schemas.smart_import import (
    AIExtractionQueuedResponse,
    AIExtractionRequest,
    AIExtractionResponse,
    AIProviderConfigCreate,
    AIProviderConnectionTestRequest,
    AIProviderConnectionTestResponse,
    AIProviderConfigResponse,
    AIProviderConfigUpdate,
    AIProviderKeyRotate,
    AIQuotaStatusResponse,
    BatchAIExtractionRequest,
    BatchDetailResponse,
    BatchDeleteResponse,
    BatchOperationItem,
    BatchOperationResponse,
    BulkFieldAcceptRequest,
    DocumentArtifactResponse,
    DocumentPageResponse,
    DocumentParseResponse,
    EntityPublishResponse,
    EnterpriseAIPolicyResponse,
    EnterpriseAIPolicyUpdate,
    ExtractedEntityDetailResponse,
    ExtractedEntityResponse,
    ExtractedFieldResponse,
    ExtractionJobResponse,
    FieldEvidenceResponse,
    FieldReviewRequest,
    FormHandoffResponse,
    FormPublishRequest,
    ImportBatchCreate,
    ImportBatchResponse,
    ImportReviewRecordResponse,
    ManualDraftCreate,
    ManualWorkbenchFieldCreate,
    SourceDocumentRegister,
    SourceDocumentResponse,
    TemplateRecommendationResponse,
    WelderImportPublishRequest,
    WelderImportReviewResponse,
    UnmappedFieldBindRequest,
    WorkbenchValidationResponse,
)
from app.services.ai_extraction_service import (
    AIExtractionRunError,
    AIExtractionService,
    build_provider,
)
from app.services.ai_extraction_queue_service import AIExtractionQueueService
from app.services.ai_quota_service import AIQuotaService
from app.services.ai_credential_service import (
    AIProviderConfigService,
    provider_config_response,
    resolve_platform_ai_config,
)
from app.services.ai_provider_service import (
    AIProviderError,
    StructuredAIRequest,
    connection_test_request,
)
from app.services.custom_module_service import CustomModuleService
from app.services.document_parser_service import (
    DefaultDocumentParser,
    DocumentParseError,
    DocumentParser,
)
from app.services.document_page_renderer import DocumentPageRenderer
from app.services.document_storage_service import (
    DocumentStorage,
    DocumentUploadError,
    get_document_storage,
)
from app.services.extraction_schema_service import (
    build_builtin_extraction_schema,
    build_module_extraction_schema,
    build_template_extraction_schema,
)
from app.services.smart_import_service import SmartImportService
from app.services.smart_import_audit_service import SmartImportAuditService
from app.services.operations_service import OperationsService
from app.services.smart_import_review_service import SmartImportReviewService
from app.services.smart_import_template_service import SmartImportTemplateService
from app.services.workspace_service import WorkspaceService
from app.services.system_config_service import get_max_upload_bytes
from app.services.wps_template_service import WPSTemplateService
from app.services.welder_import_service import WelderImportService
from app.services.smart_import_workbench_service import SmartImportWorkbenchService
from app.tasks.celery_app import celery_app
from app.tasks.smart_import_tasks import (
    run_smart_import_extraction,
    run_smart_import_parse,
)

logger = logging.getLogger(__name__)


router = APIRouter()


def build_entity_detail(
    db: Session, entity: ExtractedEntity
) -> ExtractedEntityDetailResponse:
    fields = (
        db.query(ExtractedField)
        .filter(ExtractedField.entity_id == entity.id)
        .order_by(ExtractedField.created_at, ExtractedField.id)
        .all()
    )
    evidence_by_field: dict[str, list[FieldEvidenceResponse]] = {}
    if fields:
        evidence_rows = (
            db.query(FieldEvidence)
            .filter(
                FieldEvidence.extracted_field_id.in_([field.id for field in fields])
            )
            .order_by(FieldEvidence.page_number, FieldEvidence.created_at)
            .all()
        )
        for item in evidence_rows:
            evidence_by_field.setdefault(item.extracted_field_id, []).append(
                FieldEvidenceResponse.model_validate(item)
            )
    return ExtractedEntityDetailResponse(
        **ExtractedEntityResponse.model_validate(entity).model_dump(),
        fields=[
            ExtractedFieldResponse(
                **ExtractedFieldResponse.model_validate(field).model_dump(
                    exclude={"evidence"}
                ),
                evidence=evidence_by_field.get(field.id, []),
            )
            for field in fields
        ],
    )


def get_document_parser() -> DocumentParser:
    return DefaultDocumentParser()


@router.get("/ai-capabilities")
def get_ai_capabilities(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """Expose safe provider capabilities without returning credentials."""
    del current_user
    platform = resolve_platform_ai_config(db)
    return {
        "platform_available": bool(platform["key_configured"] and platform["model"]),
        "platform_provider": platform["provider"],
        "platform_model": platform["model"],
        "platform_host": (urlsplit(platform["base_url"]).hostname or "").lower(),
        "byok_providers": ["openai_responses", "openai_compatible_chat"],
        "byok_allowed_hosts": settings.AI_BYOK_ALLOWED_HOSTS,
        "max_document_pages": settings.AI_MAX_DOCUMENT_PAGES,
        "max_input_chars": settings.AI_MAX_INPUT_CHARS,
    }


@router.get("/ai-quota", response_model=AIQuotaStatusResponse)
def get_ai_quota(
    estimated_pages: int | None = Query(None, ge=1, le=1000),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> dict:
    context = resolve_workspace(db, current_user, workspace_id)
    service = AIQuotaService(db)
    result = service.get_status(current_user, context)
    if estimated_pages is not None:
        result["estimated_points"] = service.estimate(estimated_pages)
        result["can_run_estimate"] = (
            result["platform_enabled"]
            and estimated_pages <= result["max_pages_per_task"]
            and result["estimated_points"] <= result["remaining_points"]
            and result["estimated_points"] <= result["daily_remaining_points"]
            and result["tasks_today"] < result["max_tasks_per_day"]
            and result["tasks_month"] < result["max_tasks_per_month"]
            and result["active_tasks"] < result["max_concurrent_tasks"]
            and result["user_tasks_today"] < result["max_user_tasks_per_day"]
            and result["user_tasks_month"] < result["max_user_tasks_per_month"]
            and result["user_active_tasks"] < result["max_user_concurrent_tasks"]
        )
    return result


@router.get("/ai-usage")
def get_ai_usage(
    days: int = Query(30, ge=1, le=366),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> dict:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "view")
    return AIQuotaService(db).usage_report(current_user, context, days)


def build_requested_schema(
    request: AIExtractionRequest,
    db: Session,
    current_user: User,
    context: WorkspaceContext,
    document_type: str,
) -> tuple[dict, str | None]:
    if request.module_id:
        module = CustomModuleService(db).get_module(
            request.module_id, current_user, context
        )
        if module is None:
            raise HTTPException(status_code=404, detail="提取模块不存在或无权访问")
        return build_module_extraction_schema(module), None

    if not request.template_id:
        try:
            return build_builtin_extraction_schema(document_type), None
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    template = WPSTemplateService(db).get_template_by_id(
        template_id=request.template_id,
        current_user=current_user,
        workspace_context=context,
    )
    module_service = CustomModuleService(db)
    modules = []
    seen: set[str] = set()
    for instance in template.module_instances or []:
        module_id = instance["moduleId"]
        if module_id in seen:
            continue
        seen.add(module_id)
        module = module_service.get_module(module_id, current_user, context)
        if module is not None:
            modules.append(module)
    return build_template_extraction_schema(template, modules), template.id


def validate_ai_extraction_request(request: AIExtractionRequest) -> None:
    if request.template_id and request.module_id:
        raise HTTPException(status_code=422, detail="模板和模块不能同时选择")
    if request.mode == "byok":
        if request.provider_config_id:
            if request.api_key or request.model or request.base_url or request.provider:
                raise HTTPException(status_code=422, detail="使用已保存配置时无需再次填写模型或 Key")
            return
        api_key = request.api_key.get_secret_value() if request.api_key else ""
        if not api_key.strip() or len(api_key) > 500:
            raise HTTPException(status_code=422, detail="临时 API Key 无效")
        if not request.model or not request.model.strip():
            raise HTTPException(status_code=422, detail="BYOK 模式必须指定模型")
    elif request.mode == "offline":
        if (
            request.api_key is not None
            or request.base_url is not None
            or request.provider_config_id
            or request.model is not None
            or request.provider is not None
        ):
            raise HTTPException(
                status_code=422,
                detail="离线模式只使用服务端或企业本地模型配置",
            )
    elif (
        request.api_key is not None
        or request.base_url is not None
        or request.provider_config_id
    ):
        raise HTTPException(status_code=422, detail="平台模式不接收客户端 API Key 或服务地址")


def require_sensitive_document_consent(
    db, document, request, provider_config, current_user, context
) -> None:
    """Drawings and procedure records require explicit, versioned outbound consent."""
    if document.document_type not in {"drawing", "pqr"}:
        return
    if request.mode == "offline":
        return
    provider_url = (
        provider_config.base_url
        if provider_config is not None
        else request.base_url or settings.AI_PLATFORM_BASE_URL
    )
    OperationsService(db).require_consent(
        document.id,
        provider_url,
        current_user,
        context,
        request.outbound_consent_id,
    )


def resolve_offline_provider_config(db, context):
    profile = OperationsService(db).get_deployment_profile(context)
    base_url = (
        getattr(profile, "local_ai_base_url", None) or settings.AI_OFFLINE_BASE_URL
    )
    model = getattr(profile, "local_ai_model", None) or settings.AI_OFFLINE_MODEL
    if not base_url or not model:
        raise HTTPException(status_code=503, detail="本地离线模型尚未配置")
    return SimpleNamespace(
        id=None,
        provider=settings.AI_OFFLINE_PROVIDER,
        base_url=base_url,
        model=model,
    )


def platform_task_route(document) -> tuple[str, str]:
    task_type = f"{document.document_type}_import"
    pages = max(1, int(getattr(document, "page_count", 0) or 0))
    if document.document_type == "drawing" or pages > 12:
        complexity = "advanced"
    elif pages <= 3:
        complexity = "simple"
    else:
        complexity = "standard"
    return task_type, complexity


def resolve_platform_provider_config(db, document):
    task_type, complexity = platform_task_route(document)
    platform = resolve_platform_ai_config(
        db,
        include_key=True,
        task_type=task_type,
        complexity=complexity,
    )
    if not platform["key_configured"] or not platform["model"]:
        raise HTTPException(status_code=503, detail="平台 AI 服务尚未配置")
    return (
        SimpleNamespace(
            id=platform["id"],
            provider=platform["provider"],
            base_url=platform["base_url"],
            model=platform["model"],
            task_types=platform.get("task_types") or [],
            complexity_level=platform.get("complexity_level") or complexity,
            point_multiplier=float(platform.get("point_multiplier") or 1),
        ),
        platform["api_key"],
    )


def resolve_workspace(
    db: Session, current_user: User, workspace_id: Optional[str]
) -> WorkspaceContext:
    if workspace_id:
        # `enterprise_{id}` is the canonical ID emitted by WorkspaceService.
        # Keep the old `company_{id}` spelling only as a compatibility alias.
        canonical_id = (
            f"enterprise_{workspace_id.removeprefix('company_')}"
            if workspace_id.startswith("company_")
            else workspace_id
        )
        return WorkspaceService(db).create_workspace_context(
            current_user, canonical_id
        )
    return WorkspaceContext(
        user_id=current_user.id, workspace_type=WorkspaceType.PERSONAL
    )


def ensure_import_permission(
    db: Session, user: User, context: WorkspaceContext, action: str
) -> None:
    """Personal data is owner-only; enterprise actions use fine-grained roles."""
    if (
        getattr(context, "workspace_type", WorkspaceType.PERSONAL)
        != WorkspaceType.ENTERPRISE
    ):
        return
    ensure_module_permission(db, user, "import", action)


@router.get("/ai-provider-configs", response_model=list[AIProviderConfigResponse])
def list_ai_provider_configs(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> list[AIProviderConfigResponse]:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "key_manage")
    return [
        provider_config_response(item)
        for item in AIProviderConfigService(db).list(current_user, context)
    ]


@router.post(
    "/ai-provider-configs", response_model=AIProviderConfigResponse, status_code=201
)
def create_ai_provider_config(
    data: AIProviderConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> AIProviderConfigResponse:
    enforce_rate_limit(
        f"ai-provider-config:{current_user.id}", limit=10, window_seconds=60
    )
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "key_manage")
    return provider_config_response(
        AIProviderConfigService(db).create(data, current_user, context)
    )


@router.post(
    "/ai-provider-configs/test-connection",
    response_model=AIProviderConnectionTestResponse,
)
def test_unsaved_ai_provider_config(
    data: AIProviderConnectionTestRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> AIProviderConnectionTestResponse:
    enforce_rate_limit(
        f"ai-provider-draft-test:{current_user.id}", limit=5, window_seconds=60
    )
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "key_manage")
    credential_service = AIProviderConfigService(db)
    credential_service.enforce_policy("byok", None, context)
    base_url = credential_service._validate_url(data.base_url, context)
    transient = SimpleNamespace(
        provider=data.provider,
        base_url=base_url,
        model=data.model.strip(),
    )
    provider = build_provider(
        AIExtractionRequest(mode="byok"),
        transient,
        data.api_key.get_secret_value().strip(),
    )
    try:
        provider.structured_response(_connection_test_request())
        return AIProviderConnectionTestResponse(
            success=True, message="连接成功，API Key 与模型均可用"
        )
    except AIProviderError as exc:
        return AIProviderConnectionTestResponse(success=False, message=str(exc))
    finally:
        provider.close()


@router.patch(
    "/ai-provider-configs/{config_id}", response_model=AIProviderConfigResponse
)
def update_ai_provider_config(
    config_id: str,
    data: AIProviderConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> AIProviderConfigResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "key_manage")
    service = AIProviderConfigService(db)
    item = service.get(config_id, current_user, context)
    return provider_config_response(service.update(item, data, current_user, context))


@router.post(
    "/ai-provider-configs/{config_id}/rotate", response_model=AIProviderConfigResponse
)
def rotate_ai_provider_key(
    config_id: str,
    data: AIProviderKeyRotate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> AIProviderConfigResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "key_manage")
    service = AIProviderConfigService(db)
    item = service.get(config_id, current_user, context)
    return provider_config_response(
        service.rotate(item, data.api_key.get_secret_value(), current_user, context)
    )


@router.delete("/ai-provider-configs/{config_id}", status_code=204)
def disable_ai_provider_config(
    config_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> None:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "key_manage")
    service = AIProviderConfigService(db)
    service.disable(
        service.get(config_id, current_user, context), current_user, context
    )


@router.post(
    "/ai-provider-configs/{config_id}/test", response_model=AIProviderConfigResponse
)
def test_ai_provider_config(
    config_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> AIProviderConfigResponse:
    enforce_rate_limit(
        f"ai-provider-test:{current_user.id}", limit=5, window_seconds=60
    )
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "key_manage")
    service = AIProviderConfigService(db)
    item, key = service.resolve_for_use(config_id, current_user, context)
    provider = build_provider(
        AIExtractionRequest(mode="byok", provider_config_id=item.id), item, key
    )
    try:
        provider.structured_response(_connection_test_request())
        item.last_test_status = "success"
        item.last_error = None
    except AIProviderError as exc:
        item.last_test_status = "failed"
        item.last_error = str(exc)[:300]
    finally:
        provider.close()
    item.last_tested_at = datetime.utcnow()
    item.updated_by = current_user.id
    db.commit()
    db.refresh(item)
    return provider_config_response(item)


def _connection_test_request() -> StructuredAIRequest:
    return connection_test_request()


@router.get("/enterprise-ai-policy", response_model=EnterpriseAIPolicyResponse)
def get_enterprise_ai_policy(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> dict:
    context = resolve_workspace(db, current_user, workspace_id)
    service = AIProviderConfigService(db)
    service._company(context)
    return service.policy_payload(context)


@router.put("/enterprise-ai-policy", response_model=EnterpriseAIPolicyResponse)
def update_enterprise_ai_policy(
    data: EnterpriseAIPolicyUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> dict:
    context = resolve_workspace(db, current_user, workspace_id)
    service = AIProviderConfigService(db)
    service.update_policy(data, current_user, context)
    return service.policy_payload(context)


@router.post("/batches", response_model=ImportBatchResponse, status_code=201)
def create_batch(
    data: ImportBatchCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ImportBatchResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "upload")
    return SmartImportService(db).create_batch(data, current_user, context)


@router.get("/batches", response_model=list[ImportBatchResponse])
def list_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> list[ImportBatchResponse]:
    context = resolve_workspace(db, current_user, workspace_id)
    batches = SmartImportService(db).list_batches(current_user, context, skip, limit)
    queue = AIExtractionQueueService(db)
    return [queue.refresh_batch(item) for item in batches]


@router.get("/batches/{batch_id}", response_model=BatchDetailResponse)
def get_batch(
    batch_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> BatchDetailResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    service = SmartImportService(db)
    batch = service.get_batch(batch_id, current_user, context)
    batch = AIExtractionQueueService(db).refresh_batch(batch)
    documents = service.get_batch_documents(batch, current_user, context)
    return BatchDetailResponse(
        **ImportBatchResponse.model_validate(batch).model_dump(),
        documents=[SourceDocumentResponse.model_validate(item) for item in documents],
    )


@router.delete("/batches/{batch_id}", response_model=BatchDeleteResponse)
def delete_batch(
    batch_id: str,
    delete_related_data: bool = Query(False),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
) -> BatchDeleteResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "delete")
    result = SmartImportService(db).delete_batch(
        batch_id,
        current_user,
        context,
        storage,
        delete_related_data=delete_related_data,
    )
    for job_id in result["cancelled_job_ids"]:
        try:
            celery_app.control.revoke(job_id, terminate=False)
        except Exception:
            # The database deletion is already committed. A temporary broker
            # outage must not turn a successful delete into an HTTP 500.
            logger.exception("Could not revoke deleted smart-import job %s", job_id)
    return BatchDeleteResponse(**result)


@router.post(
    "/batches/{batch_id}/documents",
    response_model=SourceDocumentResponse,
    status_code=201,
)
def register_document(
    batch_id: str,
    data: SourceDocumentRegister,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> SourceDocumentResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    return SmartImportService(db).register_document(
        batch_id, data, current_user, context
    )


@router.post(
    "/batches/{batch_id}/upload",
    response_model=SourceDocumentResponse,
    status_code=201,
)
def upload_document(
    batch_id: str,
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    document_version: Optional[str] = Form(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
) -> SourceDocumentResponse:
    """流式保存私有原件，计算哈希后登记为暂存文档。"""
    enforce_rate_limit(
        f"smart-import-upload:{current_user.id}", limit=10, window_seconds=60
    )
    if not file.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "upload")
    service = SmartImportService(db)
    batch = service.get_batch(batch_id, current_user, context)
    stored = None
    try:
        OperationsService(db).ensure_document_storage_allowed(context)
        stored = storage.save_stream(
            file.file, file.filename, max_bytes=get_max_upload_bytes()
        )
        registration = SourceDocumentRegister(
            original_filename=stored.original_filename,
            storage_key=stored.storage_key,
            sha256=stored.sha256,
            mime_type=stored.mime_type,
            size_bytes=stored.size_bytes,
            document_type=document_type or batch.target_entity_type,
            document_version=document_version,
        )
        document = service.register_document(
            batch.id, registration, current_user, context
        )
        SmartImportAuditService(db).record_file_access(
            "upload", document, current_user.id, context
        )
        db.commit()
        return document
    except DocumentUploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValidationError as exc:
        if stored is not None:
            storage.delete(stored.storage_key)
        raise HTTPException(status_code=422, detail="文档类型或版本参数无效") from exc
    except Exception:
        if stored is not None:
            storage.delete(stored.storage_key)
        raise


@router.get("/documents/{document_id}/content")
def download_document(
    document_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
) -> StreamingResponse:
    """在工作区权限校验后流式读取私有原件。"""
    enforce_rate_limit(
        f"smart-import-download:{current_user.id}", limit=30, window_seconds=60
    )
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "view")
    document = SmartImportService(db).get_document(document_id, current_user, context)
    if not document.storage_key:
        raise HTTPException(status_code=404, detail="该记录没有可下载的原件")
    try:
        stream = storage.open_stream(document.storage_key)
    except DocumentUploadError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    SmartImportAuditService(db).record_file_access(
        "download", document, current_user.id, context
    )
    db.commit()

    def content() -> Iterator[bytes]:
        try:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            stream.close()

    filename = quote(document.original_filename)
    return StreamingResponse(
        content(),
        media_type=document.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/documents/{document_id}/pages/{page_number}/preview")
def preview_document_page(
    document_id: str,
    page_number: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
) -> StreamingResponse:
    """Render a private PDF/image page for evidence-region review."""
    enforce_rate_limit(
        f"smart-import-preview:{current_user.id}", limit=60, window_seconds=60
    )
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "view")
    document = SmartImportService(db).get_document(document_id, current_user, context)
    if not document.storage_key:
        raise HTTPException(status_code=404, detail="该记录没有可预览的原件")
    try:
        with storage.open_stream(document.storage_key) as stream:
            png = DocumentPageRenderer().render_png(
                stream, document.original_filename, page_number
            )
    except (DocumentUploadError, DocumentParseError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    SmartImportAuditService(db).record_file_access(
        "preview", document, current_user.id, context
    )
    db.commit()
    return StreamingResponse(iter([png]), media_type="image/png")


@router.post("/documents/{document_id}/parse", response_model=DocumentParseResponse)
def parse_document(
    document_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
    parser: DocumentParser = Depends(get_document_parser),
) -> DocumentParseResponse:
    """Extract page text and queue scanned pages for a later OCR provider."""
    enforce_rate_limit(
        f"smart-import-parse:{current_user.id}", limit=10, window_seconds=60
    )
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "extract")
    document, pages = SmartImportService(db).parse_document(
        document_id, current_user, context, storage, parser
    )
    return DocumentParseResponse(
        document=SourceDocumentResponse.model_validate(document),
        pages=[DocumentPageResponse.model_validate(page) for page in pages],
    )


def dispatch_parse_job(job: ExtractionJob) -> None:
    try:
        run_smart_import_parse.apply_async(args=[job.id], task_id=job.id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="后台解析队列暂时不可用") from exc


@router.post(
    "/documents/{document_id}/parse-async",
    response_model=AIExtractionQueuedResponse,
    status_code=202,
)
def queue_document_parse(
    document_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> AIExtractionQueuedResponse:
    """Queue private file pagination; OCR remains in the extraction worker."""
    enforce_rate_limit(
        f"smart-import-parse-queue:{current_user.id}", limit=20, window_seconds=60
    )
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "extract")
    job = AIExtractionQueueService(db).create_parse_job(
        document_id, current_user, context
    )
    try:
        dispatch_parse_job(job)
    except HTTPException:
        job.status = "failed"
        job.error_code = "queue_unavailable"
        job.error_message = "后台解析队列暂时不可用"
        job.completed_at = datetime.utcnow()
        db.commit()
        raise
    return AIExtractionQueuedResponse(
        job=ExtractionJobResponse.model_validate(job), message="文件已进入后台解析队列"
    )


@router.get("/documents/{document_id}/pages", response_model=list[DocumentPageResponse])
def list_document_pages(
    document_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> list[DocumentPageResponse]:
    context = resolve_workspace(db, current_user, workspace_id)
    return SmartImportService(db).get_document_pages(document_id, current_user, context)


@router.get(
    "/documents/{document_id}/template-recommendations",
    response_model=TemplateRecommendationResponse,
)
def recommend_document_templates(
    document_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> TemplateRecommendationResponse:
    """Classify parsed content and rank accessible templates without changing the draft."""
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "view")
    return SmartImportTemplateService(db).recommend_for_document(
        document_id, current_user, context
    )


@router.get(
    "/documents/{document_id}/artifacts",
    response_model=list[DocumentArtifactResponse],
)
def list_document_artifacts(
    document_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> list[DocumentArtifactResponse]:
    """List typed artifacts without exposing private storage keys."""
    context = resolve_workspace(db, current_user, workspace_id)
    return SmartImportService(db).get_document_artifacts(
        document_id, current_user, context
    )


@router.post("/documents/{document_id}/extract", response_model=AIExtractionResponse)
def extract_document(
    document_id: str,
    request: AIExtractionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    storage: DocumentStorage = Depends(get_document_storage),
) -> AIExtractionResponse:
    """Run optional OCR and dynamic-schema extraction into a review-only draft."""
    enforce_rate_limit(
        f"smart-import-extract:{current_user.id}", limit=5, window_seconds=60
    )
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "extract")
    validate_ai_extraction_request(request)
    document = SmartImportService(db).get_document(document_id, current_user, context)
    schema_snapshot, template_id = build_requested_schema(
        request, db, current_user, context, document.document_type
    )
    provider = None
    provider_config = None
    try:
        credential_service = AIProviderConfigService(db)
        saved_key = None
        if request.provider_config_id:
            provider_config, saved_key = credential_service.resolve_for_use(
                request.provider_config_id, current_user, context
            )
        elif request.mode == "offline":
            credential_service.enforce_policy("offline", None, context)
            provider_config = resolve_offline_provider_config(db, context)
            saved_key = settings.AI_OFFLINE_API_KEY
        else:
            credential_service.enforce_policy(request.mode, None, context)
            if request.mode == "platform":
                provider_config, saved_key = resolve_platform_provider_config(
                    db, document
                )
                schema_snapshot = {
                    **schema_snapshot,
                    "x-weld-routing": {
                        "config_id": provider_config.id,
                        "task_type": platform_task_route(document)[0],
                        "complexity": provider_config.complexity_level,
                        "point_multiplier": provider_config.point_multiplier,
                    },
                }
        require_sensitive_document_consent(
            db, document, request, provider_config, current_user, context
        )
        provider = build_provider(request, provider_config, saved_key)
        job, entity, pages = AIExtractionService(db, storage, provider).run(
            document_id=document_id,
            schema_snapshot=schema_snapshot,
            template_id=template_id,
            mode=request.mode,
            run_ocr=request.run_ocr,
            user=current_user,
            context=context,
            provider_config_id=(
                getattr(provider_config, "id", None) if request.mode == "byok" else None
            ),
        )
        return AIExtractionResponse(
            job=job,
            entity=build_entity_detail(db, entity),
            pages=pages,
        )
    except AIExtractionRunError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    finally:
        if provider is not None:
            provider.close()


def dispatch_extraction_job(job: ExtractionJob) -> None:
    try:
        run_smart_import_extraction.apply_async(args=[job.id], task_id=job.id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="后台任务队列暂时不可用") from exc


@router.post(
    "/documents/{document_id}/extract-async",
    response_model=AIExtractionQueuedResponse,
    status_code=202,
)
def queue_document_extraction(
    document_id: str,
    request: AIExtractionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> AIExtractionQueuedResponse:
    """Queue platform or saved-credential extraction without serializing secrets."""
    enforce_rate_limit(
        f"smart-import-extract-queue:{current_user.id}", limit=10, window_seconds=60
    )
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "extract")
    validate_ai_extraction_request(request)
    if request.mode == "byok" and not request.provider_config_id:
        raise HTTPException(
            status_code=422,
            detail="临时 API Key 不进入后台队列，请使用已保存配置或单次同步提取",
        )
    document = SmartImportService(db).get_document(document_id, current_user, context)
    schema_snapshot, template_id = build_requested_schema(
        request, db, current_user, context, document.document_type
    )
    credentials = AIProviderConfigService(db)
    provider_config = None
    if request.provider_config_id:
        provider_config, _ = credentials.resolve_for_use(
            request.provider_config_id, current_user, context
        )
        provider_name = provider_config.provider
        model_name = provider_config.model
    elif request.mode == "offline":
        credentials.enforce_policy("offline", None, context)
        provider_config = resolve_offline_provider_config(db, context)
        provider_name = provider_config.provider
        model_name = provider_config.model
    else:
        credentials.enforce_policy("platform", None, context)
        provider_config, _ = resolve_platform_provider_config(db, document)
        provider_name = provider_config.provider
        model_name = provider_config.model
    require_sensitive_document_consent(
        db, document, request, provider_config, current_user, context
    )
    schema_snapshot = {
        **schema_snapshot,
        "outbound_consent_id": request.outbound_consent_id,
    }
    if request.mode == "platform":
        schema_snapshot["x-weld-routing"] = {
            "config_id": provider_config.id,
            "task_type": platform_task_route(document)[0],
            "complexity": provider_config.complexity_level,
            "point_multiplier": provider_config.point_multiplier,
        }
    service = AIExtractionQueueService(db)
    job = service.create_job(
        document_id=document_id,
        schema_snapshot=schema_snapshot,
        template_id=template_id,
        mode=request.mode,
        provider=provider_name,
        model=model_name,
        provider_config_id=(
            getattr(provider_config, "id", None) if request.mode == "byok" else None
        ),
        run_ocr=request.run_ocr,
        user=current_user,
        context=context,
    )
    try:
        dispatch_extraction_job(job)
    except HTTPException:
        job.status = "failed"
        job.error_code = "queue_unavailable"
        job.error_message = "后台任务队列暂时不可用"
        job.completed_at = datetime.utcnow()
        db.commit()
        raise
    return AIExtractionQueuedResponse(job=ExtractionJobResponse.model_validate(job))


@router.get(
    "/documents/{document_id}/extraction-jobs",
    response_model=list[ExtractionJobResponse],
)
def list_document_extraction_jobs(
    document_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> list[ExtractionJob]:
    context = resolve_workspace(db, current_user, workspace_id)
    return AIExtractionQueueService(db).list_document_jobs(
        document_id, current_user, context
    )


@router.get("/extraction-jobs/{job_id}", response_model=ExtractionJobResponse)
def get_extraction_job(
    job_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ExtractionJob:
    context = resolve_workspace(db, current_user, workspace_id)
    return AIExtractionQueueService(db).get_job(job_id, current_user, context)


@router.post("/extraction-jobs/{job_id}/cancel", response_model=ExtractionJobResponse)
def cancel_extraction_job(
    job_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ExtractionJob:
    context = resolve_workspace(db, current_user, workspace_id)
    service = AIExtractionQueueService(db)
    job = service.cancel_job(service.get_job(job_id, current_user, context))
    celery_app.control.revoke(job.id, terminate=False)
    document = SmartImportService(db).get_document(
        job.document_id, current_user, context
    )
    batch = SmartImportService(db).get_batch(document.batch_id, current_user, context)
    service.refresh_batch(batch)
    return job


@router.post(
    "/extraction-jobs/{job_id}/retry",
    response_model=AIExtractionQueuedResponse,
    status_code=202,
)
def retry_extraction_job(
    job_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> AIExtractionQueuedResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    service = AIExtractionQueueService(db)
    source = service.get_job(job_id, current_user, context)
    if (source.schema_snapshot or {}).get("job_kind") == "parse":
        if source.status not in {"failed", "cancelled"}:
            raise HTTPException(status_code=409, detail="只有失败或已取消任务可以重试")
        job = service.create_parse_job(
            source.document_id,
            current_user,
            context,
            retry_of_job_id=source.id,
        )
        try:
            dispatch_parse_job(job)
        except HTTPException:
            job.status = "failed"
            job.error_code = "queue_unavailable"
            job.error_message = "后台解析队列暂时不可用"
            job.completed_at = datetime.utcnow()
            db.commit()
            raise
        return AIExtractionQueuedResponse(
            job=ExtractionJobResponse.model_validate(job),
            message="文件重新进入后台解析队列",
        )
    credentials = AIProviderConfigService(db)
    if source.provider_config_id:
        credentials.resolve_for_use(source.provider_config_id, current_user, context)
    else:
        credentials.enforce_policy(source.mode, None, context)
    job = service.retry_job(source, current_user, context)
    try:
        dispatch_extraction_job(job)
    except HTTPException:
        job.status = "failed"
        job.error_code = "queue_unavailable"
        job.error_message = "后台任务队列暂时不可用"
        job.completed_at = datetime.utcnow()
        db.commit()
        raise
    return AIExtractionQueuedResponse(job=ExtractionJobResponse.model_validate(job))


def _operation_error(exc: HTTPException) -> str:
    if isinstance(exc.detail, str):
        return exc.detail[:500]
    if isinstance(exc.detail, dict):
        return str(exc.detail.get("message") or "操作失败")[:500]
    return "操作失败"


@router.post(
    "/batches/{batch_id}/extract-async",
    response_model=BatchOperationResponse,
    status_code=202,
)
def queue_batch_extraction(
    batch_id: str,
    request: BatchAIExtractionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> BatchOperationResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "extract")
    validate_ai_extraction_request(request)
    if request.mode == "byok" and not request.provider_config_id:
        raise HTTPException(status_code=422, detail="批量任务必须使用平台额度或已保存配置")
    smart_import = SmartImportService(db)
    batch = smart_import.get_batch(batch_id, current_user, context)
    documents = smart_import.get_batch_documents(batch, current_user, context)
    requested = set(request.document_ids)
    if requested:
        unknown = requested - {item.id for item in documents}
        if unknown:
            raise HTTPException(status_code=422, detail="选择的文件不属于当前批次")
        documents = [item for item in documents if item.id in requested]
    if not documents:
        raise HTTPException(status_code=422, detail="当前批次没有可处理文件")
    schema_snapshot, template_id = build_requested_schema(
        request, db, current_user, context, batch.target_entity_type
    )
    credentials = AIProviderConfigService(db)
    provider_config = None
    if request.provider_config_id:
        provider_config, _ = credentials.resolve_for_use(
            request.provider_config_id, current_user, context
        )
        provider_name, model_name = provider_config.provider, provider_config.model
    elif request.mode == "offline":
        credentials.enforce_policy("offline", None, context)
        provider_config = resolve_offline_provider_config(db, context)
        provider_name, model_name = provider_config.provider, provider_config.model
    else:
        credentials.enforce_policy("platform", None, context)
        provider_config, _ = resolve_platform_provider_config(db)
        provider_name, model_name = provider_config.provider, provider_config.model
    queue = AIExtractionQueueService(db)
    items: list[BatchOperationItem] = []
    for document in documents:
        try:
            document_request = request.model_copy(
                update={
                    "outbound_consent_id": request.outbound_consent_ids.get(document.id)
                }
            )
            require_sensitive_document_consent(
                db,
                document,
                document_request,
                provider_config,
                current_user,
                context,
            )
            job = queue.create_job(
                document_id=document.id,
                schema_snapshot={
                    **schema_snapshot,
                    "outbound_consent_id": document_request.outbound_consent_id,
                },
                template_id=template_id,
                mode=request.mode,
                provider=provider_name,
                model=model_name,
                provider_config_id=(
                    getattr(provider_config, "id", None)
                    if request.mode == "byok"
                    else None
                ),
                run_ocr=request.run_ocr,
                user=current_user,
                context=context,
            )
            try:
                dispatch_extraction_job(job)
            except HTTPException:
                job.status = "failed"
                job.error_code = "queue_unavailable"
                job.error_message = "后台任务队列暂时不可用"
                job.completed_at = datetime.utcnow()
                db.commit()
                raise
            items.append(
                BatchOperationItem(
                    document_id=document.id,
                    resource_id=job.id,
                    status="queued",
                )
            )
        except HTTPException as exc:
            status = "skipped" if exc.status_code == 409 else "failed"
            items.append(
                BatchOperationItem(
                    document_id=document.id,
                    status=status,
                    message=_operation_error(exc),
                )
            )
    queue.refresh_batch(batch)
    return BatchOperationResponse(
        batch_id=batch.id,
        succeeded=sum(item.status == "queued" for item in items),
        failed=sum(item.status == "failed" for item in items),
        skipped=sum(item.status == "skipped" for item in items),
        items=items,
    )


@router.post(
    "/batches/{batch_id}/retry-failed",
    response_model=BatchOperationResponse,
    status_code=202,
)
def retry_failed_batch_jobs(
    batch_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> BatchOperationResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    smart_import = SmartImportService(db)
    batch = smart_import.get_batch(batch_id, current_user, context)
    documents = smart_import.get_batch_documents(batch, current_user, context)
    queue = AIExtractionQueueService(db)
    items: list[BatchOperationItem] = []
    for document in documents:
        jobs = queue.list_document_jobs(document.id, current_user, context)
        source = jobs[0] if jobs else None
        if not source or source.status not in {"failed", "cancelled"}:
            items.append(BatchOperationItem(document_id=document.id, status="skipped"))
            continue
        try:
            credentials = AIProviderConfigService(db)
            if source.provider_config_id:
                credentials.resolve_for_use(
                    source.provider_config_id, current_user, context
                )
            else:
                credentials.enforce_policy(source.mode, None, context)
            job = queue.retry_job(source, current_user, context)
            dispatch_extraction_job(job)
            items.append(
                BatchOperationItem(
                    document_id=document.id,
                    resource_id=job.id,
                    status="queued",
                )
            )
        except HTTPException as exc:
            items.append(
                BatchOperationItem(
                    document_id=document.id,
                    status="failed",
                    message=_operation_error(exc),
                )
            )
    queue.refresh_batch(batch)
    return BatchOperationResponse(
        batch_id=batch.id,
        succeeded=sum(item.status == "queued" for item in items),
        failed=sum(item.status == "failed" for item in items),
        skipped=sum(item.status == "skipped" for item in items),
        items=items,
    )


@router.post(
    "/batches/{batch_id}/publish-reviewed",
    response_model=BatchOperationResponse,
)
def publish_reviewed_batch_entities(
    batch_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> BatchOperationResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "publish")
    smart_import = SmartImportService(db)
    batch = smart_import.get_batch(batch_id, current_user, context)
    documents = smart_import.get_batch_documents(batch, current_user, context)
    review = SmartImportReviewService(db)
    items: list[BatchOperationItem] = []
    for document in documents:
        entity = (
            smart_import._scope_query(
                db.query(ExtractedEntity), ExtractedEntity, current_user, context
            )
            .filter(
                ExtractedEntity.document_id == document.id,
                ExtractedEntity.is_current.is_(True),
            )
            .order_by(ExtractedEntity.version.desc())
            .first()
        )
        if not entity or entity.status != "review":
            items.append(BatchOperationItem(document_id=document.id, status="skipped"))
            continue
        try:
            ensure_module_permission(db, current_user, entity.entity_type, "create")
            record = review.publish(entity.id, current_user, context)
            items.append(
                BatchOperationItem(
                    document_id=document.id,
                    resource_id=record.target_entity_id,
                    status="published",
                )
            )
        except HTTPException as exc:
            items.append(
                BatchOperationItem(
                    document_id=document.id,
                    status="failed",
                    message=_operation_error(exc),
                )
            )
    AIExtractionQueueService(db).refresh_batch(batch)
    return BatchOperationResponse(
        batch_id=batch.id,
        succeeded=sum(item.status == "published" for item in items),
        failed=sum(item.status == "failed" for item in items),
        skipped=sum(item.status == "skipped" for item in items),
        items=items,
    )


@router.get("/entities/{entity_id}", response_model=ExtractedEntityDetailResponse)
def get_extracted_entity(
    entity_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ExtractedEntityDetailResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    service = SmartImportService(db)
    entity = (
        service._scope_query(
            db.query(ExtractedEntity), ExtractedEntity, current_user, context
        )
        .filter(ExtractedEntity.id == entity_id)
        .first()
    )
    if entity is None:
        raise HTTPException(status_code=404, detail="提取草稿不存在或无权访问")
    return build_entity_detail(db, entity)


@router.get(
    "/documents/{document_id}/current-entity",
    response_model=ExtractedEntityDetailResponse,
)
def get_current_extracted_entity(
    document_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ExtractedEntityDetailResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    service = SmartImportService(db)
    document = service.get_document(document_id, current_user, context)
    entity = (
        service._scope_query(
            db.query(ExtractedEntity), ExtractedEntity, current_user, context
        )
        .filter(
            ExtractedEntity.document_id == document.id,
            ExtractedEntity.is_current.is_(True),
        )
        .order_by(ExtractedEntity.version.desc())
        .first()
    )
    if entity is None:
        raise HTTPException(status_code=404, detail="该文档尚无提取草稿")
    return build_entity_detail(db, entity)


@router.get("/entities/{entity_id}/form-handoff", response_model=FormHandoffResponse)
def get_form_handoff(
    entity_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> FormHandoffResponse:
    """Prepare an import draft for the existing WPS/PQR dynamic form."""
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "review")
    service = SmartImportReviewService(db)
    entity = service.get_entity(entity_id, current_user, context)
    if entity.entity_type not in {"wps", "pqr"}:
        raise HTTPException(status_code=422, detail="当前类型没有可复用的正式表单")
    fields = (
        db.query(ExtractedField).filter(ExtractedField.entity_id == entity.id).all()
    )
    form_values = {}
    for field in fields:
        if field.review_status == "rejected":
            continue
        form_values[field.field_key] = field.normalized_value
        if field.instance_id:
            form_values[
                f"{field.instance_id}_{field.field_key}"
            ] = field.normalized_value
    job = db.query(ExtractionJob).filter(ExtractionJob.id == entity.job_id).first()
    candidates = SmartImportTemplateService(db).match_supporting_pqrs(
        entity, current_user, context
    )
    return FormHandoffResponse(
        entity_id=entity.id,
        entity_type=entity.entity_type,
        template_id=job.template_id if job else None,
        form_values=form_values,
        supporting_pqr_candidates=candidates,
    )


@router.post(
    "/entities/{entity_id}/fields/{field_id}/review",
    response_model=ExtractedEntityDetailResponse,
)
def review_extracted_field(
    entity_id: str,
    field_id: str,
    request: FieldReviewRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ExtractedEntityDetailResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "review")
    service = SmartImportReviewService(db)
    entity = service.get_entity(entity_id, current_user, context)
    ensure_module_permission(db, current_user, entity.entity_type, "update")
    entity = service.review_field(entity_id, field_id, request, current_user, context)
    return build_entity_detail(db, entity)


@router.post(
    "/entities/{entity_id}/fields/bulk-accept",
    response_model=ExtractedEntityDetailResponse,
)
def bulk_accept_extracted_fields(
    entity_id: str,
    request: BulkFieldAcceptRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ExtractedEntityDetailResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "review")
    service = SmartImportReviewService(db)
    entity = service.get_entity(entity_id, current_user, context)
    ensure_module_permission(db, current_user, entity.entity_type, "update")
    entity = service.bulk_accept(entity_id, request, current_user, context)
    return build_entity_detail(db, entity)


@router.get(
    "/entities/{entity_id}/reviews",
    response_model=list[ImportReviewRecordResponse],
)
def list_import_reviews(
    entity_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> list[ImportReviewRecordResponse]:
    context = resolve_workspace(db, current_user, workspace_id)
    entity = SmartImportReviewService(db).get_entity(entity_id, current_user, context)
    return (
        db.query(ImportReviewRecord)
        .filter(ImportReviewRecord.entity_id == entity.id)
        .order_by(ImportReviewRecord.created_at.desc())
        .all()
    )


@router.get(
    "/entities/{entity_id}/workbench-validation",
    response_model=WorkbenchValidationResponse,
)
def validate_review_workbench(
    entity_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> WorkbenchValidationResponse:
    """Run local required/duplicate/range/semantic checks without another AI call."""
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "review")
    return WorkbenchValidationResponse(
        **SmartImportWorkbenchService(db).validate(entity_id, current_user, context)
    )


@router.post(
    "/entities/{entity_id}/fields/{field_id}/bind-unmapped",
    response_model=ExtractedEntityDetailResponse,
)
def bind_unmapped_import_field(
    entity_id: str,
    field_id: str,
    request: UnmappedFieldBindRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ExtractedEntityDetailResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "modify")
    entity = SmartImportReviewService(db).get_entity(entity_id, current_user, context)
    ensure_module_permission(db, current_user, entity.entity_type, "update")
    service = SmartImportWorkbenchService(db)
    entity = service.bind_unmapped(entity_id, field_id, request, current_user, context)
    return build_entity_detail(db, entity)


@router.post(
    "/entities/{entity_id}/manual-fields",
    response_model=ExtractedEntityDetailResponse,
    status_code=201,
)
def add_manual_workbench_field(
    entity_id: str,
    request: ManualWorkbenchFieldCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ExtractedEntityDetailResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "modify")
    entity = SmartImportReviewService(db).get_entity(entity_id, current_user, context)
    ensure_module_permission(db, current_user, entity.entity_type, "update")
    entity = SmartImportWorkbenchService(db).add_manual_field(
        entity_id, request, current_user, context
    )
    return build_entity_detail(db, entity)


@router.post("/entities/{entity_id}/publish", response_model=EntityPublishResponse)
def publish_extracted_entity(
    entity_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> EntityPublishResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "publish")
    service = SmartImportReviewService(db)
    entity = service.get_entity(entity_id, current_user, context)
    ensure_module_permission(db, current_user, entity.entity_type, "create")
    record = service.publish(entity_id, current_user, context)
    return EntityPublishResponse(
        entity_id=entity.id,
        target_entity_type=record.target_entity_type,
        target_entity_id=record.target_entity_id,
        status="published",
        detail_url=f"/{record.target_entity_type}/{record.target_entity_id}",
    )


@router.get(
    "/entities/{entity_id}/welder-review",
    response_model=WelderImportReviewResponse,
)
def review_welder_import(
    entity_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> WelderImportReviewResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "review")
    ensure_module_permission(db, current_user, "welder", "update")
    return WelderImportReviewResponse(
        **WelderImportService(db).review(entity_id, current_user, context)
    )


@router.post(
    "/entities/{entity_id}/welder-publish",
    response_model=EntityPublishResponse,
)
def publish_welder_import(
    entity_id: str,
    request: WelderImportPublishRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> EntityPublishResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "publish")
    ensure_module_permission(db, current_user, "welder", "create")
    record = WelderImportService(db).publish(
        entity_id,
        [item.model_dump() for item in request.decisions],
        current_user,
        context,
    )
    return EntityPublishResponse(
        entity_id=entity_id,
        target_entity_type="welder",
        target_entity_id=record.target_entity_id,
        status="published",
        detail_url=f"/welders/{record.target_entity_id}",
    )


@router.post("/entities/{entity_id}/form-publish", response_model=EntityPublishResponse)
def publish_import_from_existing_form(
    entity_id: str,
    request: FormPublishRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> EntityPublishResponse:
    """Publish a human-corrected existing form through the normal domain Service."""
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "publish")
    service = SmartImportReviewService(db)
    entity = service.get_entity(entity_id, current_user, context)
    ensure_module_permission(db, current_user, entity.entity_type, "create")
    record = service.publish_form(entity_id, request, current_user, context)
    return EntityPublishResponse(
        entity_id=entity.id,
        target_entity_type=record.target_entity_type,
        target_entity_id=record.target_entity_id,
        status="published",
        detail_url=f"/{record.target_entity_type}/{record.target_entity_id}",
    )


@router.post(
    "/documents/{document_id}/manual-drafts",
    response_model=ExtractedEntityResponse,
    status_code=201,
)
def create_manual_draft(
    document_id: str,
    data: ManualDraftCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ExtractedEntityResponse:
    context = resolve_workspace(db, current_user, workspace_id)
    ensure_import_permission(db, current_user, context, "modify")
    return SmartImportService(db).create_manual_draft(
        document_id, data, current_user, context
    )
    EntityPublishResponse,
    FieldReviewRequest,
    ImportReviewRecordResponse,

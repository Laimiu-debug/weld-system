"""Smart-import staging endpoints. No endpoint here publishes formal business data."""
from typing import Iterator, Optional
from urllib.parse import quote

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
from app.models.company import CompanyEmployee
from app.models.user import User
from app.schemas.smart_import import (
    AIExtractionRequest,
    AIExtractionResponse,
    BatchDetailResponse,
    DocumentPageResponse,
    DocumentParseResponse,
    ExtractedEntityResponse,
    ImportBatchCreate,
    ImportBatchResponse,
    ManualDraftCreate,
    SourceDocumentRegister,
    SourceDocumentResponse,
)
from app.services.ai_extraction_service import (
    AIExtractionRunError,
    AIExtractionService,
    build_provider,
)
from app.services.custom_module_service import CustomModuleService
from app.services.document_parser_service import DefaultDocumentParser, DocumentParser
from app.services.document_storage_service import (
    DocumentStorage,
    DocumentUploadError,
    get_document_storage,
)
from app.services.extraction_schema_service import (
    build_module_extraction_schema,
    build_template_extraction_schema,
)
from app.services.smart_import_service import SmartImportService
from app.services.system_config_service import get_max_upload_bytes
from app.services.wps_template_service import WPSTemplateService


router = APIRouter()


def get_document_parser() -> DocumentParser:
    return DefaultDocumentParser()


@router.get("/ai-capabilities")
def get_ai_capabilities(
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """Expose safe provider capabilities without returning credentials."""
    del current_user
    return {
        "platform_available": bool(
            settings.AI_PLATFORM_API_KEY and settings.AI_PLATFORM_MODEL
        ),
        "platform_provider": settings.AI_PLATFORM_PROVIDER,
        "platform_model": settings.AI_PLATFORM_MODEL,
        "byok_providers": ["openai_responses", "openai_compatible_chat"],
        "byok_allowed_hosts": settings.AI_BYOK_ALLOWED_HOSTS,
        "max_document_pages": settings.AI_MAX_DOCUMENT_PAGES,
        "max_input_chars": settings.AI_MAX_INPUT_CHARS,
    }


def build_requested_schema(
    request: AIExtractionRequest,
    db: Session,
    current_user: User,
    context: WorkspaceContext,
) -> tuple[dict, str | None]:
    if request.module_id:
        module = CustomModuleService(db).get_module(
            request.module_id, current_user, context
        )
        if module is None:
            raise HTTPException(status_code=404, detail="提取模块不存在或无权访问")
        return build_module_extraction_schema(module), None

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
    if bool(request.template_id) == bool(request.module_id):
        raise HTTPException(status_code=422, detail="必须且只能选择一个模板或模块")
    if request.mode == "byok":
        api_key = request.api_key.get_secret_value() if request.api_key else ""
        if not api_key.strip() or len(api_key) > 500:
            raise HTTPException(status_code=422, detail="临时 API Key 无效")
        if not request.model or not request.model.strip():
            raise HTTPException(status_code=422, detail="BYOK 模式必须指定模型")
    elif request.api_key is not None or request.base_url is not None:
        raise HTTPException(status_code=422, detail="平台模式不接收客户端 API Key 或服务地址")


def resolve_workspace(
    db: Session, current_user: User, workspace_id: Optional[str]
) -> WorkspaceContext:
    if workspace_id and workspace_id.startswith("company_"):
        try:
            company_id = int(workspace_id.removeprefix("company_"))
        except ValueError:
            company_id = None
        employee = (
            db.query(CompanyEmployee)
            .filter(
                CompanyEmployee.user_id == current_user.id,
                CompanyEmployee.company_id == company_id,
                CompanyEmployee.status == "active",
            )
            .first()
        )
        if employee:
            return WorkspaceContext(
                user_id=current_user.id,
                workspace_type=WorkspaceType.ENTERPRISE,
                company_id=employee.company_id,
                factory_id=employee.factory_id,
            )
    return WorkspaceContext(
        user_id=current_user.id, workspace_type=WorkspaceType.PERSONAL
    )


@router.post("/batches", response_model=ImportBatchResponse, status_code=201)
def create_batch(
    data: ImportBatchCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> ImportBatchResponse:
    context = resolve_workspace(db, current_user, workspace_id)
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
    return SmartImportService(db).list_batches(current_user, context, skip, limit)


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
    documents = service.get_batch_documents(batch, current_user, context)
    return BatchDetailResponse(
        **ImportBatchResponse.model_validate(batch).model_dump(),
        documents=[SourceDocumentResponse.model_validate(item) for item in documents],
    )


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
    service = SmartImportService(db)
    batch = service.get_batch(batch_id, current_user, context)
    stored = None
    try:
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
        return service.register_document(batch.id, registration, current_user, context)
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
    document = SmartImportService(db).get_document(document_id, current_user, context)
    if not document.storage_key:
        raise HTTPException(status_code=404, detail="该记录没有可下载的原件")
    try:
        stream = storage.open_stream(document.storage_key)
    except DocumentUploadError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

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
    document, pages = SmartImportService(db).parse_document(
        document_id, current_user, context, storage, parser
    )
    return DocumentParseResponse(
        document=SourceDocumentResponse.model_validate(document),
        pages=[DocumentPageResponse.model_validate(page) for page in pages],
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
    validate_ai_extraction_request(request)
    schema_snapshot, template_id = build_requested_schema(
        request, db, current_user, context
    )
    provider = None
    try:
        provider = build_provider(request)
        job, entity, pages = AIExtractionService(db, storage, provider).run(
            document_id=document_id,
            schema_snapshot=schema_snapshot,
            template_id=template_id,
            mode=request.mode,
            run_ocr=request.run_ocr,
            user=current_user,
            context=context,
        )
        return AIExtractionResponse(
            job=job,
            entity=entity,
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
    return SmartImportService(db).create_manual_draft(
        document_id, data, current_user, context
    )

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
from app.core.rate_limit import enforce_rate_limit
from app.models.company import CompanyEmployee
from app.models.user import User
from app.schemas.smart_import import (
    BatchDetailResponse,
    ExtractedEntityResponse,
    ImportBatchCreate,
    ImportBatchResponse,
    ManualDraftCreate,
    SourceDocumentRegister,
    SourceDocumentResponse,
)
from app.services.document_storage_service import (
    DocumentStorage,
    DocumentUploadError,
    get_document_storage,
)
from app.services.smart_import_service import SmartImportService
from app.services.system_config_service import get_max_upload_bytes


router = APIRouter()


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

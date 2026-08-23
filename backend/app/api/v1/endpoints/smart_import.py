"""Smart-import staging endpoints. No endpoint here publishes formal business data."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core.data_access import WorkspaceContext, WorkspaceType
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
from app.services.smart_import_service import SmartImportService


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

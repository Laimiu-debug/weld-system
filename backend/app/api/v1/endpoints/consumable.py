"""P6 consumable issue-list, inventory-link and export endpoints."""
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.smart_import import resolve_workspace
from app.core.data_access import WorkspaceType
from app.core.module_permissions import ensure_module_permission
from app.core.rate_limit import enforce_export_limit
from app.models.user import User
from app.schemas.consumable import ConsumableActualEventCreate
from app.schemas.consumable_calculator import CalculatorQuoteRequest
from app.services.consumable_calculator_api_service import ConsumableCalculatorApiService
from app.services.consumable_export_service import ConsumableExportService
from app.services.consumable_issue_service import ConsumableIssueService

router = APIRouter()


def _permission(db, user, context, action="view"):
    if context.workspace_type == WorkspaceType.ENTERPRISE:
        ensure_module_permission(db, user, "material", action)


def row(item):
    return {
        column.name: getattr(item, column.name) for column in item.__table__.columns
    }


@router.get("/usage")
def list_consumable_usage(
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return ConsumableIssueService(db).list_usage(
        current_user, context, event_type, skip, limit
    )


@router.post("/calculator/quote")
def calculator_quote(
    payload: CalculatorQuoteRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "view")
    try:
        return ConsumableCalculatorApiService.quote(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/issue-lists")
def list_issue_lists(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return ConsumableIssueService(db).list_issue_lists(
        current_user, context, status=status, skip=skip, limit=limit
    )


@router.post("/quota-runs/{run_id}/issue-list", status_code=201)
def generate_issue_list(
    run_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "create")
    result, created = ConsumableIssueService(db).generate_issue_list(
        run_id, current_user, context
    )
    return {"created": created, "issue_list": row(result)}


@router.get("/issue-lists/{issue_list_id}")
def issue_list_detail(
    issue_list_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    detail = ConsumableIssueService(db).detail(issue_list_id, current_user, context)
    return {
        "issue_list": row(detail["issue_list"]),
        "items": [row(item) for item in detail["items"]],
        "events": [row(item) for item in detail["events"]],
    }


@router.post("/issue-lists/{issue_list_id}/approve")
def approve_issue_list(
    issue_list_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "approve")
    return row(ConsumableIssueService(db).approve(issue_list_id, current_user, context))


@router.post("/issue-items/{issue_item_id}/actual-events", status_code=201)
def record_actual_event(
    issue_item_id: str,
    data: ConsumableActualEventCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    result, created = ConsumableIssueService(db).record_actual_event(
        issue_item_id=issue_item_id,
        user=current_user,
        context=context,
        **data.model_dump(),
    )
    return {"created": created, "event": row(result)}


@router.get("/issue-lists/{issue_list_id}/calibration")
def calibration_report(
    issue_list_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return ConsumableIssueService(db).calibration_report(
        issue_list_id, current_user, context
    )


@router.get("/issue-lists/{issue_list_id}/export/{export_type}")
def export_issue_list(
    issue_list_id: str,
    export_type: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "export")
    enforce_export_limit(current_user.id)
    detail = ConsumableIssueService(db).detail(issue_list_id, current_user, context)
    exporters = {
        "weld-detail": ConsumableExportService.weld_detail,
        "product-summary": ConsumableExportService.product_summary,
        "formal-issue-list": ConsumableExportService.formal_issue_list,
    }
    if export_type not in exporters:
        from fastapi import HTTPException

        raise HTTPException(422, "不支持的焊材定额导出类型")
    payload = exporters[export_type](detail)
    filename = quote(f"{detail['issue_list'].document_number}-{export_type}.csv")
    return StreamingResponse(
        iter([payload]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )

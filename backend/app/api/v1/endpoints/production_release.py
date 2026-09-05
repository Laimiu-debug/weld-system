"""P7 approved sequence to production execution endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.smart_import import resolve_workspace
from app.core.data_access import WorkspaceType
from app.core.module_permissions import ensure_module_permission
from app.models.user import User
from app.schemas.production_release import (
    ExecutionRecordRequest,
    ReleaseSequenceRequest,
    ResourceAssignmentRequest,
    ResourceOverrideDecision,
    SequenceChangeApply,
    SequenceChangeRequestCreate,
)
from app.services.production_release_service import ProductionReleaseService

router = APIRouter()


def _permission(db, user, context, action="view"):
    if context.workspace_type == WorkspaceType.ENTERPRISE:
        ensure_module_permission(db, user, "production", action)


def _row(item):
    return {
        column.name: getattr(item, column.name) for column in item.__table__.columns
    }


@router.post("/sequences/{sequence_id}/release")
def release_sequence(
    sequence_id: str,
    data: ReleaseSequenceRequest,
    response: Response,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "create")
    item, created = ProductionReleaseService(db).release(
        sequence_id, data.consumable_issue_list_id, current_user, context
    )
    response.status_code = 201 if created else 200
    return {"created": created, "release": _row(item)}


@router.get("/sequences/{sequence_id}/release")
def sequence_release_detail(
    sequence_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return ProductionReleaseService(db).for_sequence(sequence_id, current_user, context)


@router.get("/releases/{release_id}")
def release_detail(
    release_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return ProductionReleaseService(db).detail(release_id, current_user, context)


@router.post("/tasks/{task_id}/assign")
def assign_resource(
    task_id: int,
    data: ResourceAssignmentRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    return _row(
        ProductionReleaseService(db).assign(
            task_id,
            data.welder_id,
            data.equipment_id,
            data.override_reason,
            current_user,
            context,
        )
    )


@router.post("/resource-authorizations/{authorization_id}/decision")
def decide_resource_override(
    authorization_id: str,
    data: ResourceOverrideDecision,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    return _row(
        ProductionReleaseService(db).authorize_override(
            authorization_id, data.approve, current_user, context
        )
    )


@router.post("/tasks/{task_id}/execution")
def record_execution(
    task_id: int,
    data: ExecutionRecordRequest,
    response: Response,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    item, created = ProductionReleaseService(db).record_execution(
        task_id, data.model_dump(), current_user, context
    )
    response.status_code = 201 if created else 200
    return {"created": created, "execution": _row(item)}


@router.post("/releases/{release_id}/change-requests", status_code=201)
def request_sequence_change(
    release_id: str,
    data: SequenceChangeRequestCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    return _row(
        ProductionReleaseService(db).request_change(
            release_id,
            data.reason,
            data.impact_snapshot,
            data.workflow_id,
            current_user,
            context,
        )
    )


@router.post("/change-requests/{request_id}/apply")
def apply_sequence_change(
    request_id: str,
    data: SequenceChangeApply,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    return _row(
        ProductionReleaseService(db).apply_change(
            request_id, data.proposed_sequence_revision_id, current_user, context
        )
    )

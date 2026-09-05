"""P5 weld sequence planning and approval endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.smart_import import resolve_workspace
from app.core.data_access import WorkspaceType
from app.core.module_permissions import ensure_module_permission
from app.models.user import User
from app.models.sequence import WeldSequenceRevision
from app.schemas.sequence import (
    SequenceGenerate,
    SequenceRecalculate,
    SequenceReorder,
    SequenceSubmit,
)
from app.services.sequence_service import WeldSequenceService

router = APIRouter()


def _permission(db, user, context, action="view"):
    if context.workspace_type == WorkspaceType.ENTERPRISE:
        ensure_module_permission(db, user, "engineering", action)


def row(item):
    return {
        column.name: getattr(item, column.name) for column in item.__table__.columns
    }


@router.post("/product-revisions/{revision_id}/generate", status_code=201)
def generate(
    revision_id: str,
    data: SequenceGenerate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "create")
    return row(
        WeldSequenceService(db).generate(
            revision_id,
            data.strategies,
            data.ai_step_codes,
            data.ai_explanation,
            current_user,
            context,
            structure=data.structure.model_dump(),
        )
    )


@router.get("/product-revisions/{revision_id}")
def list_revisions(
    revision_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return [
        row(item)
        for item in WeldSequenceService(db).list_revisions(
            revision_id, current_user, context
        )
    ]


@router.get("/product-revisions/{revision_id}/production-release")
def production_release(
    revision_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return WeldSequenceService(db).production_release(
        revision_id, current_user, context
    )


@router.get("/revisions/{sequence_id}")
def detail(
    sequence_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    result = WeldSequenceService(db).detail(sequence_id, current_user, context)
    return {
        "revision": row(result["revision"]),
        "steps": [row(item) for item in result["steps"]],
        "dependencies": [row(item) for item in result["dependencies"]],
    }


@router.post("/revisions/{sequence_id}/reorder", status_code=201)
def reorder(
    sequence_id: str,
    data: SequenceReorder,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    return row(
        WeldSequenceService(db).reorder(
            sequence_id,
            data.ordered_step_ids,
            data.locked_step_ids,
            data.change_summary,
            current_user,
            context,
        )
    )


@router.post("/revisions/{sequence_id}/recalculate", status_code=201)
def recalculate(
    sequence_id: str,
    data: SequenceRecalculate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    service = WeldSequenceService(db)
    parent = service._get(
        WeldSequenceRevision,
        sequence_id,
        current_user,
        context,
        True,
    )
    return row(
        service.generate(
            parent.product_revision_id,
            data.strategies
            if data.strategies is not None
            else {
                key: value
                for key, value in parent.strategy_snapshot.items()
                if not key.startswith("_")
            },
            None,
            None,
            current_user,
            context,
            parent_id=parent.id,
            change_summary=data.change_summary,
            change_request_id=data.change_request_id,
            structure=data.structure.model_dump()
            if data.structure
            else parent.strategy_snapshot.get("_structure"),
        )
    )


@router.get("/comparisons")
def compare(
    left_id: str,
    right_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return WeldSequenceService(db).compare(left_id, right_id, current_user, context)


@router.post("/revisions/{sequence_id}/submit")
def submit(
    sequence_id: str,
    data: SequenceSubmit,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    return row(
        WeldSequenceService(db).submit(
            sequence_id,
            data.notes,
            data.priority,
            data.workflow_id,
            current_user,
            context,
        )
    )

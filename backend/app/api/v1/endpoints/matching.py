"""P4 explainable WPS/PQR matching endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.smart_import import resolve_workspace
from app.core.data_access import WorkspaceType
from app.core.module_permissions import ensure_module_permission
from app.models.user import User
from app.schemas.matching import (
    CapabilityGapLink,
    CandidateConfirm,
    MatchRunApprove,
    MatchRunCreate,
)
from app.services.matching_service import WPSMatchingService

router = APIRouter()


def _permission(db, user, context, action="view"):
    if context.workspace_type == WorkspaceType.ENTERPRISE:
        ensure_module_permission(db, user, "capability", action)


def row(item):
    return {
        column.name: getattr(item, column.name) for column in item.__table__.columns
    }


@router.post("/revisions/{revision_id}/runs", status_code=201)
def run_matching(
    revision_id: str,
    data: MatchRunCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "create")
    return row(
        WPSMatchingService(db).run(
            revision_id,
            data.joint_ids,
            data.affected_only,
            data.trigger_type,
            data.policy_weights,
            current_user,
            context,
        )
    )


@router.get("/revisions/{revision_id}/runs")
def list_runs(
    revision_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return [
        row(x)
        for x in WPSMatchingService(db).list_runs(revision_id, current_user, context)
    ]


@router.get("/revisions/{revision_id}/approved-matches")
def approved_matches(
    revision_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    return [
        row(x)
        for x in WPSMatchingService(db).approved_freezes(
            revision_id, current_user, context
        )
    ]


@router.get("/runs/{run_id}")
def run_detail(
    run_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context)
    data = WPSMatchingService(db).detail(run_id, current_user, context)
    return {
        "run": row(data["run"]),
        "candidates": [
            {
                **row(item),
                "criteria": [row(x) for x in data["criteria"].get(item.id, [])],
            }
            for item in data["candidates"]
        ],
        "gaps": [row(x) for x in data["gaps"]],
        "freezes": [row(x) for x in data["freezes"]],
    }


@router.post("/candidates/{candidate_id}/confirm")
def confirm_candidate(
    candidate_id: str,
    data: CandidateConfirm,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    return row(
        WPSMatchingService(db).confirm(
            candidate_id, data.status, data.note, current_user, context
        )
    )


@router.post("/runs/{run_id}/approve")
def approve_run(
    run_id: str,
    data: MatchRunApprove,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "approve")
    return row(WPSMatchingService(db).approve(run_id, data.note, current_user, context))


@router.post("/gaps/{gap_id}/link")
def link_gap(
    gap_id: str,
    data: CapabilityGapLink,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    _permission(db, current_user, context, "edit")
    return row(
        WPSMatchingService(db).link_gap(
            gap_id,
            data.ppqr_id,
            data.qualification_plan_reference,
            current_user,
            context,
        )
    )

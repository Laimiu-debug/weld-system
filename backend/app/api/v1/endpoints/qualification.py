"""P2 procedure-qualification rule, result, and WPS/PQR relationship APIs."""
from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api import deps
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.core.module_permissions import ensure_module_permission
from app.models.company import CompanyEmployee
from app.models.user import User
from app.schemas.qualification import (
    PQRQualificationCalculateRequest,
    PQRQualificationResultResponse,
    QualificationRulePackResponse,
    QualificationRulePackStatusUpdate,
    WPSPQRSupportConfirm,
    WPSPQRSupportCreate,
    WPSPQRSupportResponse,
    WPSQualificationTraceResponse,
)
from app.schemas.capability import (
    CapabilityCheckRequest,
    CapabilityCheckResponse,
    CapabilityFilters,
    CapabilityOverviewResponse,
)
from app.services.capability_service import CapabilityLibraryService
from app.services.qualification_service import QualificationService
from app.services.workspace_service import WorkspaceService


router = APIRouter()


def _workspace(
    db: Session, user: User, workspace_id: Optional[str]
) -> WorkspaceContext:
    if workspace_id:
        return WorkspaceService(db).create_workspace_context(user, workspace_id)
    if user.membership_type == "enterprise":
        employee = (
            db.query(CompanyEmployee)
            .filter(
                CompanyEmployee.user_id == user.id,
                CompanyEmployee.status == "active",
            )
            .first()
        )
        if employee:
            return WorkspaceContext(
                user_id=user.id,
                workspace_type=WorkspaceType.ENTERPRISE,
                company_id=employee.company_id,
                factory_id=employee.factory_id,
            )
    return WorkspaceContext(user_id=user.id, workspace_type=WorkspaceType.PERSONAL)


@router.get("/rule-packs", response_model=list[QualificationRulePackResponse])
def list_rule_packs(
    include_inactive: bool = False,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> list:
    return QualificationService(db).list_rule_packs(
        include_inactive=include_inactive and bool(current_user.is_superuser)
    )


@router.get("/rule-packs/{pack_id}", response_model=QualificationRulePackResponse)
def get_rule_pack(
    pack_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return QualificationService(db).get_rule_pack(
        pack_id, published_only=not bool(current_user.is_superuser)
    )


@router.put(
    "/rule-packs/{pack_id}/status", response_model=QualificationRulePackResponse
)
def update_rule_pack_status(
    pack_id: str,
    request: QualificationRulePackStatusUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
):
    del current_user
    return QualificationService(db).transition_rule_pack(pack_id, request.status)


@router.post(
    "/pqr/{pqr_id}/calculate",
    response_model=PQRQualificationResultResponse,
)
def calculate_pqr_qualification(
    pqr_id: int,
    request: PQRQualificationCalculateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = _workspace(db, current_user, workspace_id)
    ensure_module_permission(db, current_user, "pqr", "update")
    return QualificationService(db).calculate_pqr(
        pqr_id,
        current_user,
        context,
        rule_pack_id=request.rule_pack_id,
        fact_overrides=request.fact_overrides,
        force_recalculate=request.force_recalculate,
    )


@router.get(
    "/pqr/{pqr_id}/results",
    response_model=list[PQRQualificationResultResponse],
)
def list_pqr_qualification_results(
    pqr_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    return QualificationService(db).list_pqr_results(
        pqr_id, current_user, _workspace(db, current_user, workspace_id)
    )


@router.post(
    "/wps/{wps_id}/support-links",
    response_model=WPSPQRSupportResponse,
    status_code=201,
)
def create_wps_pqr_support_link(
    wps_id: int,
    request: WPSPQRSupportCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = _workspace(db, current_user, workspace_id)
    ensure_module_permission(db, current_user, "wps", "update")
    return QualificationService(db).create_support_link(
        wps_id, request, current_user, context
    )


@router.put(
    "/support-links/{link_id}/confirmation",
    response_model=WPSPQRSupportResponse,
)
def confirm_wps_pqr_support_link(
    link_id: str,
    request: WPSPQRSupportConfirm,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = _workspace(db, current_user, workspace_id)
    ensure_module_permission(db, current_user, "wps", "update")
    return QualificationService(db).confirm_support_link(
        link_id, request, current_user, context
    )


@router.get(
    "/wps/{wps_id}/trace",
    response_model=WPSQualificationTraceResponse,
)
def get_wps_qualification_trace(
    wps_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    return QualificationService(db).wps_trace(
        wps_id, current_user, _workspace(db, current_user, workspace_id)
    )


@router.get(
    "/capabilities/overview",
    response_model=CapabilityOverviewResponse,
)
def get_capability_overview(
    filters: CapabilityFilters = Depends(),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    ensure_module_permission(db, current_user, "capability", "read")
    return CapabilityLibraryService(db).overview(
        current_user,
        _workspace(db, current_user, workspace_id),
        filters,
    )


@router.post(
    "/capabilities/check",
    response_model=CapabilityCheckResponse,
)
def check_capability(
    request: CapabilityCheckRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    ensure_module_permission(db, current_user, "capability", "read")
    return CapabilityLibraryService(db).check(
        current_user,
        _workspace(db, current_user, workspace_id),
        request,
    )

"""P8 operations, privacy, deployment and lifecycle endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.smart_import import resolve_workspace
from app.core.config import settings
from app.models.user import User
from app.schemas.operations import (
    AlertDecision,
    BackupVerificationCreate,
    DeploymentProfileUpdate,
    OutboundConsentCreate,
    ProviderFallbackRequest,
    TenantLifecycleCreate,
    TenantLifecycleDecision,
    TenantLifecycleExecute,
)
from app.services.operations_service import OperationsService, deployment_capabilities

router = APIRouter()


def row(item):
    return {
        column.name: getattr(item, column.name) for column in item.__table__.columns
    }


@router.get("/dashboard")
def dashboard(
    hours: int = Query(24, ge=1, le=24 * 90),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return OperationsService(db).dashboard(current_user, context, hours)


@router.post("/alerts/detect")
def detect_alerts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return [
        row(item)
        for item in OperationsService(db).detect_usage_anomalies(current_user, context)
    ]


@router.get("/alerts")
def list_alerts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return [
        row(item) for item in OperationsService(db).list_alerts(current_user, context)
    ]


@router.post("/alerts/{alert_id}/decision")
def decide_alert(
    alert_id: str,
    data: AlertDecision,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return row(
        OperationsService(db).decide_alert(alert_id, data.action, current_user, context)
    )


@router.post("/providers/{config_id}/health-check")
def provider_health_check(
    config_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return row(OperationsService(db).health_check(config_id, current_user, context))


@router.post("/providers/fallback-plan")
def provider_fallback_plan(
    data: ProviderFallbackRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return OperationsService(db).fallback_plan(
        data.preferred_config_id, data.allow_manual_fallback, current_user, context
    )


@router.post("/outbound-consents", status_code=201)
def create_outbound_consent(
    data: OutboundConsentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return row(OperationsService(db).create_consent(data, current_user, context))


@router.post("/outbound-consents/{consent_id}/revoke")
def revoke_outbound_consent(
    consent_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return row(OperationsService(db).revoke_consent(consent_id, current_user, context))


@router.get("/deployment-profile")
def get_deployment_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    item = OperationsService(db).get_deployment_profile(context)
    if item:
        return row(item)
    mode = settings.DEPLOYMENT_MODE
    network = "offline" if mode == "offline" else "external_allowed"
    return {
        "company_id": context.company_id,
        "deployment_mode": mode,
        "network_policy": network,
        "capabilities": deployment_capabilities(
            mode,
            network,
            bool(settings.AI_OFFLINE_BASE_URL),
            settings.OCR_OFFLINE_ENABLED,
        ),
    }


@router.put("/deployment-profile")
def update_deployment_profile(
    data: DeploymentProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return row(
        OperationsService(db).update_deployment_profile(data, current_user, context)
    )


@router.post("/backup-verifications", status_code=201)
def verify_backup(
    data: BackupVerificationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return row(OperationsService(db).verify_backup(data, current_user))


@router.post("/tenant-lifecycle", status_code=201)
def create_tenant_lifecycle_job(
    data: TenantLifecycleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return row(OperationsService(db).create_lifecycle_job(data, current_user, context))


@router.post("/tenant-lifecycle/{job_id}/decision")
def decide_tenant_lifecycle_job(
    job_id: str,
    data: TenantLifecycleDecision,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return row(
        OperationsService(db).decide_lifecycle_job(
            job_id, data.approve, current_user, context
        )
    )


@router.post("/tenant-lifecycle/{job_id}/execute")
def execute_tenant_lifecycle_job(
    job_id: str,
    data: TenantLifecycleExecute,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
):
    context = resolve_workspace(db, current_user, workspace_id)
    return row(
        OperationsService(db).execute_lifecycle_job(
            job_id, data.confirmation, data.dry_run, current_user, context
        )
    )

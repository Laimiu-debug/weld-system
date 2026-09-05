"""MVP endpoints: production plans, quality standards, performances, report templates."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.data_access import WorkspaceContext
from app.services.workspace_entity_service import (
    paginated_payload,
    performance_service,
    plan_service,
    report_template_service,
    run_report_template,
    standard_service,
)

from app.schemas.business_workflows import PlanTasksInput

router = APIRouter()


def _workspace(
    current_user: Any,
    workspace_type: str,
    company_id: Optional[int],
    factory_id: Optional[int],
) -> WorkspaceContext:
    ctx = WorkspaceContext(
        user_id=current_user.id,
        workspace_type=workspace_type,
        company_id=company_id,
        factory_id=factory_id,
    )
    try:
        ctx.validate()
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return ctx


@router.get("/reports/field-catalog")
def report_field_catalog(current_user: Any = Depends(deps.get_current_active_user)):
    from app.services.report_template_runner import catalog
    return {"success": True, "data": catalog()}


@router.get("/employees/performance-options")
def performance_employee_options(workspace_type: str = Query(...), company_id: Optional[int] = None,
                                 factory_id: Optional[int] = None, db: Session = Depends(deps.get_db),
                                 current_user: Any = Depends(deps.get_current_active_user)):
    from app.services.business_workflow_service import employee_options
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    return {"success": True, "data": employee_options(db, current_user, ctx)}


@router.get("/production/plan-task-options")
def plan_task_options(workspace_type: str = Query(...), company_id: Optional[int] = None,
                      factory_id: Optional[int] = None, plan_id: Optional[int] = None,
                      search: Optional[str] = None, db: Session = Depends(deps.get_db),
                      current_user: Any = Depends(deps.get_current_active_user)):
    from app.models.production import ProductionTask
    from app.core.data_access import DataAccessMiddleware
    from sqlalchemy import or_
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    access = DataAccessMiddleware(db)
    query = access.apply_workspace_filter(db.query(ProductionTask), ProductionTask, current_user, ctx)
    query = query.filter(ProductionTask.is_active == True)
    # Always include current assignments, even when searching or limiting candidates.
    # Otherwise saving the selector can silently drop tasks outside the first page.
    assigned = query.filter(ProductionTask.plan_id == plan_id).order_by(ProductionTask.id).all() if plan_id else []
    query = query.filter(ProductionTask.plan_id == None)
    if search:
        query = query.filter(or_(ProductionTask.task_name.ilike(f"%{search}%"), ProductionTask.task_number.ilike(f"%{search}%")))
    rows = assigned + query.order_by(ProductionTask.id).limit(200).all()
    return {"success": True, "data": [{"id": row.id, "task_name": row.task_name, "task_number": row.task_number,
            "plan_id": row.plan_id, "status": row.status, "progress_percentage": row.progress_percentage} for row in rows]}


@router.put("/production/plans/{plan_id}/tasks")
def link_plan_tasks(plan_id: int, payload: PlanTasksInput, workspace_type: str = Query(...),
                    company_id: Optional[int] = None, factory_id: Optional[int] = None,
                    db: Session = Depends(deps.get_db), current_user: Any = Depends(deps.get_current_active_user)):
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    return {"success": True, "data": plan_service(db).set_tasks(plan_id, payload.task_ids, current_user, ctx)}


# -------------------- Production plans --------------------

@router.get("/production/plans")
def list_production_plans(
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    overdue: Optional[bool] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    items, total = plan_service(db).list_items(
        current_user,
        ctx,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        search_fields=["plan_number", "plan_name", "plan_type", "assigned_team"],
        overdue=overdue,
    )
    return {"success": True, "data": paginated_payload(items, total, skip, limit)}


@router.post("/production/plans")
def create_production_plan(
    payload: Dict[str, Any],
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = plan_service(db).create_item(payload, current_user, ctx)
    return {"success": True, "data": item, "message": "创建生产计划成功"}


@router.get("/production/plans/{plan_id}")
def get_production_plan(
    plan_id: int,
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = plan_service(db).get_item(plan_id, current_user, ctx)
    return {"success": True, "data": item}


@router.put("/production/plans/{plan_id}")
def update_production_plan(
    plan_id: int,
    payload: Dict[str, Any],
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = plan_service(db).update_item(plan_id, payload, current_user, ctx)
    return {"success": True, "data": item, "message": "更新生产计划成功"}


@router.delete("/production/plans/{plan_id}")
def delete_production_plan(
    plan_id: int,
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    plan_service(db).delete_item(plan_id, current_user, ctx)
    return {"success": True, "message": "删除生产计划成功"}


# -------------------- Quality standards --------------------

@router.get("/quality/standards")
def list_quality_standards(
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    items, total = standard_service(db).list_items(
        current_user,
        ctx,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        search_fields=["standard_code", "standard_name", "category", "level"],
    )
    return {"success": True, "data": paginated_payload(items, total, skip, limit)}


@router.post("/quality/standards")
def create_quality_standard(
    payload: Dict[str, Any],
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = standard_service(db).create_item(payload, current_user, ctx)
    return {"success": True, "data": item, "message": "创建质量标准成功"}


@router.get("/quality/standards/{standard_id}")
def get_quality_standard(
    standard_id: int,
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = standard_service(db).get_item(standard_id, current_user, ctx)
    return {"success": True, "data": item}


@router.put("/quality/standards/{standard_id}")
def update_quality_standard(
    standard_id: int,
    payload: Dict[str, Any],
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = standard_service(db).update_item(standard_id, payload, current_user, ctx)
    return {"success": True, "data": item, "message": "更新质量标准成功"}


@router.delete("/quality/standards/{standard_id}")
def delete_quality_standard(
    standard_id: int,
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    standard_service(db).delete_item(standard_id, current_user, ctx)
    return {"success": True, "message": "删除质量标准成功"}


# -------------------- Employee performances --------------------

@router.get("/employees/performances")
def list_performances(
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    items, total = performance_service(db).list_items(
        current_user,
        ctx,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        search_fields=["employee_name", "department", "position", "review_period"],
    )
    return {"success": True, "data": paginated_payload(items, total, skip, limit)}


@router.post("/employees/performances")
def create_performance(
    payload: Dict[str, Any],
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = performance_service(db).create_item(payload, current_user, ctx)
    return {"success": True, "data": item, "message": "创建绩效记录成功"}


@router.get("/employees/performances/{record_id}")
def get_performance(
    record_id: int,
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = performance_service(db).get_item(record_id, current_user, ctx)
    return {"success": True, "data": item}


@router.put("/employees/performances/{record_id}")
def update_performance(
    record_id: int,
    payload: Dict[str, Any],
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = performance_service(db).update_item(record_id, payload, current_user, ctx)
    return {"success": True, "data": item, "message": "更新绩效记录成功"}


@router.delete("/employees/performances/{record_id}")
def delete_performance(
    record_id: int,
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    performance_service(db).delete_item(record_id, current_user, ctx)
    return {"success": True, "message": "删除绩效记录成功"}


# -------------------- Report templates --------------------

@router.get("/reports/templates")
def list_report_templates(
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    items, total = report_template_service(db).list_items(
        current_user,
        ctx,
        skip=skip,
        limit=limit,
        search=search,
        search_fields=["name", "description", "chart_type"],
    )
    return {"success": True, "data": paginated_payload(items, total, skip, limit)}


@router.post("/reports/templates")
def create_report_template(
    payload: Dict[str, Any],
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = report_template_service(db).create_item(payload, current_user, ctx)
    return {"success": True, "data": item, "message": "创建报表模板成功"}


@router.get("/reports/templates/{template_id}")
def get_report_template(
    template_id: int,
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = report_template_service(db).get_item(template_id, current_user, ctx)
    return {"success": True, "data": item}


@router.put("/reports/templates/{template_id}")
def update_report_template(
    template_id: int,
    payload: Dict[str, Any],
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    item = report_template_service(db).update_item(template_id, payload, current_user, ctx)
    return {"success": True, "data": item, "message": "更新报表模板成功"}


@router.delete("/reports/templates/{template_id}")
def delete_report_template(
    template_id: int,
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    report_template_service(db).delete_item(template_id, current_user, ctx)
    return {"success": True, "message": "删除报表模板成功"}


@router.post("/reports/templates/{template_id}/run")
def run_report_template_endpoint(
    template_id: int,
    workspace_type: str = Query(...),
    company_id: Optional[int] = Query(None),
    factory_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user),
) -> Any:
    ctx = _workspace(current_user, workspace_type, company_id, factory_id)
    template = report_template_service(db).get_item(template_id, current_user, ctx)
    result = run_report_template(db, template, current_user, ctx)
    return {"success": True, "data": result}

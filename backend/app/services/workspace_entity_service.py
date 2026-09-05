"""
Generic workspace-scoped CRUD helpers for MVP business entities.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from math import ceil
from typing import Any, Dict, List, Optional, Tuple, Type

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.models.business_extensions import EmployeePerformance, ReportTemplate
from app.models.production import ProductionPlan, ProductionTask
from app.models.quality import QualityInspection, QualityStandard
from app.models.user import User
from app.models.wps import WPS
from app.models.pqr import PQR


def _model_to_dict(obj: Any) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            data[column.name] = value.isoformat()
        elif hasattr(value, "isoformat"):
            data[column.name] = value.isoformat()
        else:
            data[column.name] = value
    return data


class WorkspaceEntityService:
    """CRUD for workspace-isolated entities."""

    def __init__(self, db: Session, model: Type[Any], code_field: Optional[str] = None):
        self.db = db
        self.model = model
        self.code_field = code_field
        self.data_access = DataAccessMiddleware(db)

    def prepare(self, payload, current_user, workspace_context, item=None):
        return payload

    def serialize(self, item, current_user, workspace_context):
        return _model_to_dict(item)

    def before_delete(self, item, current_user, workspace_context):
        pass

    def list_items(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        *,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        overdue: Optional[bool] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        workspace_context.validate()
        query = self.db.query(self.model).filter(self.model.is_active == True)  # noqa: E712
        query = self.data_access.apply_workspace_filter(
            query=query,
            model=self.model,
            user=current_user,
            workspace_context=workspace_context,
        )
        if status and hasattr(self.model, "status"):
            query = query.filter(self.model.status == status)
        if search and search_fields:
            from sqlalchemy import or_

            clauses = []
            for field in search_fields:
                column = getattr(self.model, field, None)
                if column is not None:
                    clauses.append(column.ilike(f"%{search}%"))
            if clauses:
                query = query.filter(or_(*clauses))
        if overdue is not None and self.model is ProductionPlan:
            condition = (ProductionPlan.plan_end_date < date.today()) & ProductionPlan.status.notin_(["completed", "cancelled"])
            query = query.filter(condition if overdue else ~condition)
        total = query.count()
        rows = (
            query.order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self.serialize(row, current_user, workspace_context) for row in rows], total

    def get_item(
        self,
        item_id: int,
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> Dict[str, Any]:
        item = self.db.query(self.model).filter(self.model.id == item_id).first()
        if not item or not getattr(item, "is_active", True):
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="记录不存在")
        self.data_access.check_access(current_user, item, "VIEW", workspace_context)
        return self.serialize(item, current_user, workspace_context)

    def create_item(
        self,
        payload: Dict[str, Any],
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> Dict[str, Any]:
        from app.services.workspace_service import WorkspaceService

        workspace_context.validate()
        WorkspaceService(self.db).validate_workspace_access(current_user, workspace_context)
        payload = self.prepare(payload, current_user, workspace_context)
        valid = {c.name for c in self.model.__table__.columns}
        data = {k: v for k, v in payload.items() if k in valid and k not in {
            "id", "user_id", "workspace_type", "company_id", "factory_id",
            "created_by", "updated_by", "created_at", "updated_at",
        }}
        if self.code_field and data.get(self.code_field):
            existing = (
                self.db.query(self.model)
                .filter(
                    getattr(self.model, self.code_field) == data[self.code_field],
                    self.model.is_active == True,  # noqa: E712
                )
            )
            existing = self.data_access.apply_workspace_filter(
                query=existing,
                model=self.model,
                user=current_user,
                workspace_context=workspace_context,
            ).first()
            if existing:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"{self.code_field} 已存在",
                )

        item = self.model(**data)
        item.user_id = current_user.id
        item.workspace_type = workspace_context.workspace_type
        item.company_id = workspace_context.company_id
        item.factory_id = workspace_context.factory_id
        item.created_by = current_user.id
        item.updated_by = current_user.id
        item.is_active = True
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return self.serialize(item, current_user, workspace_context)

    def update_item(
        self,
        item_id: int,
        payload: Dict[str, Any],
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> Dict[str, Any]:
        item = self.db.query(self.model).filter(self.model.id == item_id).with_for_update().first()
        if not item or not getattr(item, "is_active", True):
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="记录不存在")
        self.data_access.check_access(current_user, item, "EDIT", workspace_context)
        payload = self.prepare(payload, current_user, workspace_context, item)
        if self.code_field and payload.get(self.code_field) != getattr(item, self.code_field):
            duplicate = self.db.query(self.model).filter(
                getattr(self.model, self.code_field) == payload[self.code_field], self.model.id != item.id,
                self.model.is_active == True)
            duplicate = self.data_access.apply_workspace_filter(duplicate, self.model, current_user, workspace_context)
            if duplicate.first():
                raise HTTPException(400, f"{self.code_field} 已存在")
        valid = {c.name for c in self.model.__table__.columns}
        for key, value in payload.items():
            if key in valid and key not in {
                "id", "user_id", "workspace_type", "company_id", "factory_id",
                "created_by", "created_at",
            }:
                setattr(item, key, value)
        item.updated_by = current_user.id
        item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)
        return self.serialize(item, current_user, workspace_context)

    def delete_item(
        self,
        item_id: int,
        current_user: User,
        workspace_context: WorkspaceContext,
    ) -> None:
        item = self.db.query(self.model).filter(self.model.id == item_id).with_for_update().first()
        if not item or not getattr(item, "is_active", True):
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="记录不存在")
        self.data_access.check_access(current_user, item, "DELETE", workspace_context)
        self.before_delete(item, current_user, workspace_context)
        item.is_active = False
        item.updated_by = current_user.id
        item.updated_at = datetime.utcnow()
        self.db.commit()


def run_report_template(
    db: Session,
    template: Dict[str, Any],
    current_user: User,
    workspace_context: WorkspaceContext,
) -> Dict[str, Any]:
    from app.services.report_template_runner import run_report
    return run_report(db, template, current_user, workspace_context)


def paginated_payload(items: List[Any], total: int, skip: int, limit: int) -> Dict[str, Any]:
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = ceil(total / limit) if limit > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": limit,
        "total_pages": total_pages,
    }


def plan_service(db: Session) -> WorkspaceEntityService:
    from app.services.business_workflow_service import PlanService
    return PlanService(db, ProductionPlan, code_field="plan_number")


def standard_service(db: Session) -> WorkspaceEntityService:
    from app.services.business_workflow_service import StandardService
    return StandardService(db, QualityStandard, code_field="standard_code")


def performance_service(db: Session) -> WorkspaceEntityService:
    from app.services.business_workflow_service import PerformanceService
    return PerformanceService(db, EmployeePerformance)


def report_template_service(db: Session) -> WorkspaceEntityService:
    from app.services.business_workflow_service import ReportService
    return ReportService(db, ReportTemplate)

"""
Reports endpoints for the welding system backend.
"""
from datetime import date as date_cls
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.dashboard import get_workspace_context
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/")
async def get_reports(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """获取可用报表目录."""
    del current_user
    return {
        "success": True,
        "data": {
            "items": ReportService.get_catalog(),
        },
        "message": "获取报表目录成功",
    }


@router.get("/statistics")
async def get_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
) -> Any:
    """获取工作区业务统计."""
    workspace_context = get_workspace_context(db, current_user, workspace_id)
    service = ReportService(db)
    parsed_start = date_cls.fromisoformat(start_date) if start_date else None
    parsed_end = date_cls.fromisoformat(end_date) if end_date else None
    return {
        "success": True,
        "data": service.get_statistics(
            current_user, workspace_context, parsed_start, parsed_end
        ),
        "message": "获取报表统计成功",
    }

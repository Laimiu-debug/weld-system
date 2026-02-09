"""
仪表盘API端点
提供仪表盘数据接口
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.company import CompanyEmployee
from app.services.dashboard_service import DashboardService
from app.services.workspace_service import WorkspaceService
from app.core.data_access import WorkspaceContext, WorkspaceType

router = APIRouter()


def get_workspace_context(
    db: Session,
    current_user: User,
    workspace_id: Optional[str] = None
) -> WorkspaceContext:
    """
    获取工作区上下文

    Args:
        db: 数据库会话
        current_user: 当前用户
        workspace_id: 工作区ID（可选）

    Returns:
        WorkspaceContext对象
    """
    workspace_service = WorkspaceService(db)

    # 如果提供了workspace_id，使用它
    if workspace_id:
        return workspace_service.create_workspace_context(current_user, workspace_id)

    # 否则，根据用户的会员类型确定默认工作区
    if current_user.membership_type == "enterprise":
        # 企业用户，查找其企业
        employee = db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.status == "active"
        ).first()

        if employee:
            return WorkspaceContext(
                user_id=current_user.id,
                workspace_type=WorkspaceType.ENTERPRISE,
                company_id=employee.company_id,
                factory_id=employee.factory_id
            )

    # 默认使用个人工作区
    return WorkspaceContext(
        user_id=current_user.id,
        workspace_type=WorkspaceType.PERSONAL
    )


@router.get("/stats")
def get_dashboard_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    获取仪表盘统计数据
    
    Returns:
        统计数据，包括：
        - wps_count: WPS记录数
        - pqr_count: PQR记录数
        - ppqr_count: pPQR记录数
        - materials_count: 焊材数量
        - welders_count: 焊工数量
        - equipment_count: 设备数量
        - production_count: 生产任务数
        - quality_count: 质量检验数
        - storage_used_mb: 已用存储(MB)
        - storage_limit_mb: 存储限制(MB)
        - membership_usage: 会员配额使用情况
    """
    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)
    
    # 创建仪表盘服务
    dashboard_service = DashboardService(db)
    
    # 获取统计数据
    stats = dashboard_service.get_overview_stats(current_user, workspace_context)
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/recent-activities")
def get_recent_activities(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    limit: int = 10
) -> Any:
    """
    获取最近活动记录
    
    Args:
        limit: 返回记录数，默认10条
        
    Returns:
        最近活动列表
    """
    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)
    
    # 创建仪表盘服务
    dashboard_service = DashboardService(db)
    
    # 获取最近活动
    activities = dashboard_service.get_recent_activities(
        current_user,
        workspace_context,
        limit
    )
    
    return {
        "success": True,
        "data": activities
    }


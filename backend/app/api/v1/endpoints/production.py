"""
Production Management API endpoints for the welding system backend.
"""
from typing import Any, List, Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.production import ProductionTaskCreate, ProductionTaskUpdate, ProductionTaskResponse, ProductionTaskListResponse
from app.services.production_service import ProductionService
from app.core.data_access import WorkspaceContext

router = APIRouter()


@router.get("/tasks", response_model=dict)
async def get_production_tasks(
    db: Session = Depends(deps.get_db),
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="任务状态"),
    priority: Optional[str] = Query(None, description="优先级"),
    assigned_welder_id: Optional[int] = Query(None, description="分配焊工ID"),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取生产任务列表

    - **workspace_type**: 工作区类型（personal/enterprise）
    - **company_id**: 企业ID（企业工作区必填）
    - **factory_id**: 工厂ID（可选）
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **search**: 搜索关键词
    - **status**: 任务状态筛选
    - **priority**: 优先级筛选
    - **assigned_welder_id**: 分配焊工ID筛选
    """
    try:
        # 构建工作区上下文
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # 调用服务层
        service = ProductionService(db)
        tasks, total = service.get_production_task_list(
            current_user=current_user,
            workspace_context=workspace_context,
            skip=skip,
            limit=limit,
            search=search,
            status=status,
            priority=priority,
            assigned_welder_id=assigned_welder_id
        )

        # 计算分页信息
        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = ceil(total / limit) if limit > 0 else 0

        return {
            "success": True,
            "data": {
                "items": [ProductionTaskResponse.model_validate(t) for t in tasks],
                "total": total,
                "page": page,
                "page_size": limit,
                "total_pages": total_pages
            },
            "message": "获取生产任务列表成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/tasks", response_model=dict)
async def create_production_task(
    task_in: ProductionTaskCreate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    创建生产任务

    - **workspace_type**: 工作区类型（personal/enterprise）
    - **company_id**: 企业ID（企业工作区必填）
    - **factory_id**: 工厂ID（可选）
    """
    try:
        # 构建工作区上下文
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # 调用服务层
        service = ProductionService(db)
        task = service.create_production_task(
            current_user=current_user,
            task_data=task_in.model_dump(),
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": ProductionTaskResponse.model_validate(task),
            "message": "生产任务创建成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/tasks/{task_id}", response_model=dict)
async def get_production_task_detail(
    task_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取生产任务详情

    - **task_id**: 任务ID
    - **workspace_type**: 工作区类型（personal/enterprise）
    - **company_id**: 企业ID（企业工作区必填）
    - **factory_id**: 工厂ID（可选）
    """
    try:
        # 构建工作区上下文
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # 调用服务层
        service = ProductionService(db)
        task = service.get_production_task_by_id(
            task_id=task_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": ProductionTaskResponse.model_validate(task),
            "message": "获取生产任务详情成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/tasks/{task_id}", response_model=dict)
async def update_production_task(
    task_id: int,
    task_in: ProductionTaskUpdate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新生产任务

    - **task_id**: 任务ID
    - **workspace_type**: 工作区类型（personal/enterprise）
    - **company_id**: 企业ID（企业工作区必填）
    - **factory_id**: 工厂ID（可选）
    """
    try:
        # 构建工作区上下文
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # 调用服务层
        service = ProductionService(db)
        task = service.update_production_task(
            task_id=task_id,
            current_user=current_user,
            task_data=task_in.model_dump(exclude_unset=True),
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": ProductionTaskResponse.model_validate(task),
            "message": "生产任务更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/tasks/{task_id}", response_model=dict)
async def delete_production_task(
    task_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    删除生产任务

    - **task_id**: 任务ID
    - **workspace_type**: 工作区类型（personal/enterprise）
    - **company_id**: 企业ID（企业工作区必填）
    - **factory_id**: 工厂ID（可选）
    """
    try:
        # 构建工作区上下文
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        # 调用服务层
        service = ProductionService(db)
        service.delete_production_task(
            task_id=task_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "message": "生产任务删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/tasks/{task_id}/progress")
async def update_task_progress(
    task_id: str,
    progress_data: dict,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新任务进度
    """
    # TODO: 实现实际的进度更新逻辑
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            **progress_data
        },
        "message": "任务进度更新成功"
    }


@router.post("/tasks/{task_id}/records")
async def create_production_record(
    task_id: str,
    record_data: dict,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    创建生产记录
    """
    # TODO: 实现实际的记录创建逻辑
    return {
        "success": True,
        "data": {
            "id": "record-id",
            "task_id": task_id,
            **record_data
        },
        "message": "生产记录创建成功"
    }


@router.get("/tasks/{task_id}/records")
async def get_production_records(
    task_id: str,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取生产记录
    """
    # TODO: 实现实际的查询逻辑
    return {
        "success": True,
        "data": {
            "items": [],
            "total": 0
        },
        "message": "获取生产记录成功"
    }


@router.get("/statistics/overview")
async def get_production_statistics(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取生产统计信息
    """
    # TODO: 实现实际的统计逻辑
    return {
        "success": True,
        "data": {
            "total_tasks": 0,
            "pending_tasks": 0,
            "in_progress_tasks": 0,
            "completed_tasks": 0,
            "cancelled_tasks": 0,
            "average_completion_rate": 0.0
        },
        "message": "获取统计信息成功"
    }


@router.get("/statistics/efficiency")
async def get_production_efficiency(
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取生产效率统计
    """
    # TODO: 实现实际的效率统计逻辑
    return {
        "success": True,
        "data": {
            "total_production_hours": 0.0,
            "completed_tasks_count": 0,
            "average_task_duration": 0.0,
            "efficiency_rate": 0.0
        },
        "message": "获取生产效率统计成功"
    }


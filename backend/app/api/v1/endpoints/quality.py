"""
Quality Management API endpoints for the welding system backend.
"""
from typing import Any, List, Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.quality import QualityInspectionCreate, QualityInspectionUpdate, QualityInspectionResponse, QualityInspectionListResponse
from app.services.quality_service import QualityService
from app.core.data_access import WorkspaceContext

router = APIRouter()


@router.get("/inspections", response_model=dict)
async def get_quality_inspections(
    db: Session = Depends(deps.get_db),
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    result: Optional[str] = Query(None, description="检验结果"),
    inspection_type: Optional[str] = Query(None, description="检验类型"),
    inspector_id: Optional[int] = Query(None, description="检验员ID"),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取质量检验列表

    - **workspace_type**: 工作区类型（personal/enterprise）
    - **company_id**: 企业ID（企业工作区必填）
    - **factory_id**: 工厂ID（可选）
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **search**: 搜索关键词
    - **result**: 检验结果筛选
    - **inspection_type**: 检验类型筛选
    - **inspector_id**: 检验员ID筛选
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
        service = QualityService(db)
        inspections, total = service.get_quality_inspection_list(
            current_user=current_user,
            workspace_context=workspace_context,
            skip=skip,
            limit=limit,
            search=search,
            inspection_type=inspection_type,
            result=result,
            inspector_id=inspector_id
        )

        # 计算分页信息
        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = ceil(total / limit) if limit > 0 else 0

        return {
            "success": True,
            "data": {
                "items": [QualityInspectionResponse.model_validate(i) for i in inspections],
                "total": total,
                "page": page,
                "page_size": limit,
                "total_pages": total_pages
            },
            "message": "获取质量检验列表成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/inspections", response_model=dict)
async def create_quality_inspection(
    inspection_in: QualityInspectionCreate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    创建质量检验

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

        # 打印接收到的数据
        print(f"DEBUG API: 接收到的inspection_in数据: {inspection_in}")
        dumped_data = inspection_in.model_dump(exclude_unset=True)
        print(f"DEBUG API: model_dump后的数据: {dumped_data}")

        # 调用服务层 - 使用exclude_unset=True排除未设置的字段
        service = QualityService(db)
        inspection = service.create_quality_inspection(
            current_user=current_user,
            inspection_data=dumped_data,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": QualityInspectionResponse.model_validate(inspection),
            "message": "质量检验创建成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating quality inspection: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建质量检验失败: {str(e)}"
        )


@router.get("/inspections/{inspection_id}", response_model=dict)
async def get_quality_inspection_detail(
    inspection_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取质量检验详情

    - **inspection_id**: 检验ID
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
        service = QualityService(db)
        inspection = service.get_quality_inspection_by_id(
            inspection_id=inspection_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": QualityInspectionResponse.model_validate(inspection),
            "message": "获取质量检验详情成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/inspections/{inspection_id}", response_model=dict)
async def update_quality_inspection(
    inspection_id: int,
    inspection_in: QualityInspectionUpdate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新质量检验

    - **inspection_id**: 检验ID
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
        service = QualityService(db)
        inspection = service.update_quality_inspection(
            inspection_id=inspection_id,
            current_user=current_user,
            inspection_data=inspection_in.model_dump(exclude_unset=True),
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": QualityInspectionResponse.model_validate(inspection),
            "message": "质量检验更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/inspections/{inspection_id}", response_model=dict)
async def delete_quality_inspection(
    inspection_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    删除质量检验

    - **inspection_id**: 检验ID
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
        service = QualityService(db)
        service.delete_quality_inspection(
            inspection_id=inspection_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "message": "质量检验删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/nonconformance")
async def get_nonconformance_records(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="处理状态"),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取不合格品记录列表
    """
    # TODO: 实现实际的数据库查询
    return {
        "success": True,
        "data": {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": limit,
            "total_pages": 0
        },
        "message": "获取不合格品记录列表成功"
    }


@router.post("/nonconformance")
async def create_nonconformance_record(
    record_data: dict,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    创建不合格品记录
    """
    # TODO: 实现实际的创建逻辑
    return {
        "success": True,
        "data": {
            "id": "new-nonconformance-id",
            **record_data,
            "created_at": "2025-01-01T00:00:00Z"
        },
        "message": "不合格品记录创建成功"
    }


@router.get("/nonconformance/{record_id}")
async def get_nonconformance_detail(
    record_id: str,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取不合格品记录详情
    """
    # TODO: 实现实际的查询逻辑
    return {
        "success": True,
        "data": {
            "id": record_id,
            "record_number": "NCR-2025-001",
            "status": "pending"
        },
        "message": "获取不合格品记录详情成功"
    }


@router.put("/nonconformance/{record_id}")
async def update_nonconformance_record(
    record_id: str,
    record_data: dict,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新不合格品记录
    """
    # TODO: 实现实际的更新逻辑
    return {
        "success": True,
        "data": {
            "id": record_id,
            **record_data,
            "updated_at": "2025-01-01T00:00:00Z"
        },
        "message": "不合格品记录更新成功"
    }


@router.get("/statistics/overview")
async def get_quality_statistics(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取质量统计信息
    """
    # TODO: 实现实际的统计逻辑
    return {
        "success": True,
        "data": {
            "total_inspections": 0,
            "pass_count": 0,
            "fail_count": 0,
            "conditional_count": 0,
            "pass_rate": 0.0,
            "total_nonconformance": 0,
            "pending_nonconformance": 0
        },
        "message": "获取质量统计信息成功"
    }


@router.get("/statistics/trends")
async def get_quality_trends(
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取质量趋势统计
    """
    # TODO: 实现实际的趋势统计逻辑
    return {
        "success": True,
        "data": {
            "daily_pass_rate": [],
            "defect_types_distribution": {},
            "inspector_performance": []
        },
        "message": "获取质量趋势统计成功"
    }


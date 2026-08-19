"""
Welder Management API endpoints for the welding system backend.
"""
from typing import Any, List, Optional
from uuid import UUID
from math import ceil
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.welder import (
    WelderCreate, WelderUpdate, WelderResponse, WelderListResponse,
    WelderCertificationCreate, WelderCertificationUpdate, WelderCertificationResponse,
    WelderWorkRecordCreate, WelderWorkRecordResponse,
    WelderTrainingCreate, WelderTrainingResponse,
    WelderAssessmentCreate, WelderAssessmentResponse,
    WelderWorkHistoryCreate, WelderWorkHistoryResponse
)
from app.services.welder_service import WelderService
from app.core.data_access import WorkspaceContext

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=dict)
def get_welders_list(
    db: Session = Depends(deps.get_db),
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    skill_level: Optional[str] = Query(None, description="技能等级筛选"),
    welder_status: Optional[str] = Query(None, description="状态筛选"),
    certification_status: Optional[str] = Query(None, description="证书状态筛选"),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取焊工列表

    - **workspace_type**: 工作区类型（personal/enterprise）
    - **company_id**: 企业ID（企业工作区必填）
    - **factory_id**: 工厂ID（可选）
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **search**: 搜索关键词
    - **skill_level**: 技能等级筛选
    - **welder_status**: 状态筛选
    - **certification_status**: 证书状态筛选
    """
    try:
        logger.info(f"[焊工列表] 开始获取焊工列表 - workspace_type={workspace_type}, company_id={company_id}, factory_id={factory_id}, user_id={current_user.id}")
        logger.info(f"[焊工列表] 查询参数 - skip={skip}, limit={limit}, search={search}, skill_level={skill_level}, welder_status={welder_status}, certification_status={certification_status}")

        # 构建工作区上下文
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )
        logger.info(f"[焊工列表] 工作区上下文创建成功: {workspace_context}")

        # 调用服务层
        service = WelderService(db)
        logger.info(f"[焊工列表] 调用服务层获取焊工列表...")
        welders, total = service.get_welder_list(
            current_user=current_user,
            workspace_context=workspace_context,
            skip=skip,
            limit=limit,
            search=search,
            skill_level=skill_level,
            welder_status=welder_status,
            certification_status=certification_status
        )
        logger.info(f"[焊工列表] 服务层返回成功 - 获取到 {len(welders)} 条记录, 总数: {total}")

        # 计算分页信息
        page = (skip // limit) + 1 if limit > 0 else 1
        total_pages = ceil(total / limit) if limit > 0 else 0

        logger.info(f"[焊工列表] 准备返回数据 - page={page}, total_pages={total_pages}")
        return {
            "success": True,
            "data": {
                "items": [WelderResponse.model_validate(w) for w in welders],
                "total": total,
                "page": page,
                "page_size": limit,
                "total_pages": total_pages
            },
            "message": "获取焊工列表成功"
        }

    except HTTPException as he:
        logger.error(f"[焊工列表] HTTPException: {he.detail}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"[焊工列表] 未知错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取焊工列表失败: {str(e)}"
        )


@router.post("/", response_model=dict)
def create_welder(
    welder_in: WelderCreate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    创建新焊工

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
        service = WelderService(db)
        welder = service.create_welder(
            current_user=current_user,
            welder_data=welder_in.model_dump(),
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": WelderResponse.model_validate(welder),
            "message": "焊工创建成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{welder_id}", response_model=dict)
def get_welder_detail(
    welder_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取焊工详情

    - **welder_id**: 焊工ID
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
        service = WelderService(db)
        welder = service.get_welder_by_id(
            welder_id=welder_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": WelderResponse.model_validate(welder),
            "message": "获取焊工详情成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{welder_id}", response_model=dict)
def update_welder(
    welder_id: int,
    welder_in: WelderUpdate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新焊工信息

    - **welder_id**: 焊工ID
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
        service = WelderService(db)
        welder = service.update_welder(
            welder_id=welder_id,
            current_user=current_user,
            welder_data=welder_in.model_dump(exclude_unset=True),
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": WelderResponse.model_validate(welder),
            "message": "焊工信息更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{welder_id}", response_model=dict)
def delete_welder(
    welder_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    删除焊工

    - **welder_id**: 焊工ID
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
        service = WelderService(db)
        service.delete_welder(
            welder_id=welder_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "message": "焊工删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== 证书管理端点 ====================


@router.get("/{welder_id}/certifications", response_model=dict)
def get_welder_certifications(
    welder_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取焊工证书列表

    - **welder_id**: 焊工ID
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
        service = WelderService(db)
        certifications, total = service.get_certifications(
            welder_id=welder_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": {
                "items": certifications,
                "total": total
            },
            "message": "获取证书列表成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{welder_id}/certifications", response_model=dict)
def add_welder_certification(
    welder_id: int,
    certification_data: WelderCertificationCreate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    添加焊工证书

    - **welder_id**: 焊工ID
    - **certification_data**: 证书数据
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
        service = WelderService(db)
        certification = service.add_certification(
            welder_id=welder_id,
            certification_data=certification_data.model_dump(),
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": certification,
            "message": "证书添加成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{welder_id}/certifications/{certification_id}", response_model=dict)
def update_welder_certification(
    welder_id: int,
    certification_id: int,
    certification_data: WelderCertificationUpdate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    更新焊工证书

    - **welder_id**: 焊工ID
    - **certification_id**: 证书ID
    - **certification_data**: 证书数据
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
        service = WelderService(db)
        certification = service.update_certification(
            welder_id=welder_id,
            certification_id=certification_id,
            certification_data=certification_data.model_dump(exclude_unset=True),
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": certification,
            "message": "证书更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{welder_id}/certifications/{certification_id}", response_model=dict)
def delete_welder_certification(
    welder_id: int,
    certification_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    删除焊工证书

    - **welder_id**: 焊工ID
    - **certification_id**: 证书ID
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
        service = WelderService(db)
        service.delete_certification(
            welder_id=welder_id,
            certification_id=certification_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": None,
            "message": "证书删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== 统计分析端点 ====================


@router.get("/statistics/overview", response_model=dict)
def get_welders_statistics(
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """
    获取焊工统计信息

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
        service = WelderService(db)
        statistics = service.get_statistics(
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": statistics,
            "message": "获取统计信息成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== 工作经历管理 ====================

@router.get("/{welder_id}/work-records", response_model=dict)
def get_welder_work_records(
    welder_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """获取焊工工作记录列表"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        records, total = service.get_work_records(
            welder_id=welder_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": {
                "items": records,
                "total": total
            },
            "message": "获取工作记录成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in get_welder_work_records: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{welder_id}/work-records", response_model=dict)
def add_welder_work_record(
    welder_id: int,
    record_data: WelderWorkRecordCreate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """添加焊工工作记录"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        record = service.add_work_record(
            welder_id=welder_id,
            record_data=record_data.model_dump(),
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": record,
            "message": "工作记录添加成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{welder_id}/work-records/{record_id}", response_model=dict)
def delete_welder_work_record(
    welder_id: int,
    record_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """删除焊工工作记录"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        service.delete_work_record(
            welder_id=welder_id,
            record_id=record_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "message": "工作记录删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== 培训记录管理 ====================

@router.get("/{welder_id}/training-records", response_model=dict)
def get_welder_training_records(
    welder_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """获取焊工培训记录列表"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        records, total = service.get_training_records(
            welder_id=welder_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": {
                "items": records,
                "total": total
            },
            "message": "获取培训记录成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in get_welder_training_records: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{welder_id}/training-records", response_model=dict)
def add_welder_training_record(
    welder_id: int,
    record_data: WelderTrainingCreate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """添加焊工培训记录"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        record = service.add_training_record(
            welder_id=welder_id,
            record_data=record_data.model_dump(),
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": record,
            "message": "培训记录添加成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{welder_id}/training-records/{record_id}", response_model=dict)
def delete_welder_training_record(
    welder_id: int,
    record_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """删除焊工培训记录"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        service.delete_training_record(
            welder_id=welder_id,
            record_id=record_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "message": "培训记录删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== 考核记录管理 ====================

@router.get("/{welder_id}/assessment-records", response_model=dict)
def get_welder_assessment_records(
    welder_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """获取焊工考核记录列表"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        records, total = service.get_assessment_records(
            welder_id=welder_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": {
                "items": records,
                "total": total
            },
            "message": "获取考核记录成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in get_welder_assessment_records: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{welder_id}/assessment-records", response_model=dict)
def add_welder_assessment_record(
    welder_id: int,
    record_data: WelderAssessmentCreate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """添加焊工考核记录"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        record = service.add_assessment_record(
            welder_id=welder_id,
            record_data=record_data.model_dump(),
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": record,
            "message": "考核记录添加成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{welder_id}/assessment-records/{record_id}", response_model=dict)
def delete_welder_assessment_record(
    welder_id: int,
    record_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """删除焊工考核记录"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        service.delete_assessment_record(
            welder_id=welder_id,
            record_id=record_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "message": "考核记录删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== 工作履历管理 ====================

@router.get("/{welder_id}/work-histories", response_model=dict)
def get_welder_work_histories(
    welder_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """获取焊工工作履历列表"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        histories, total = service.get_work_histories(
            welder_id=welder_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": {
                "items": histories,
                "total": total
            },
            "message": "获取工作履历列表成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{welder_id}/work-histories", response_model=dict)
def add_welder_work_history(
    welder_id: int,
    history_data: WelderWorkHistoryCreate,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """添加焊工工作履历"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        history = service.add_work_history(
            welder_id=welder_id,
            history_data=history_data.model_dump(),
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "data": history,
            "message": "工作履历添加成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{welder_id}/work-histories/{history_id}", response_model=dict)
def delete_welder_work_history(
    welder_id: int,
    history_id: int,
    workspace_type: str = Query(..., description="工作区类型：personal/enterprise"),
    company_id: Optional[int] = Query(None, description="企业ID（企业工作区必填）"),
    factory_id: Optional[int] = Query(None, description="工厂ID（可选）"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """删除焊工工作履历"""
    try:
        workspace_context = WorkspaceContext(
            workspace_type=workspace_type,
            user_id=current_user.id,
            company_id=company_id,
            factory_id=factory_id
        )

        service = WelderService(db)
        service.delete_work_history(
            welder_id=welder_id,
            history_id=history_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return {
            "success": True,
            "message": "工作履历删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


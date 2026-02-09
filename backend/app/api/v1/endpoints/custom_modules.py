"""
自定义模块API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.company import CompanyEmployee
from app.schemas.custom_module import (
    CustomModuleCreate,
    CustomModuleUpdate,
    CustomModuleResponse,
    CustomModuleSummary
)
from app.services.custom_module_service import CustomModuleService
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


@router.get("/", response_model=List[CustomModuleSummary])
def get_custom_modules(
    module_type: Optional[str] = Query(None, description="模块类型 (wps/pqr/ppqr/common)"),
    category: Optional[str] = Query(None, description="模块分类"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """
    获取可用的自定义模块列表（带工作区上下文数据隔离）
    包括：系统模块 + 用户自己的模块 + 企业共享模块

    参数:
        module_type: 模块类型筛选，如果指定则返回该类型和common类型的模块
        category: 模块分类筛选
    """
    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # 创建Service实例
    module_service = CustomModuleService(db)

    # 获取模块列表
    modules = module_service.get_available_modules(
        current_user=current_user,
        workspace_context=workspace_context,
        module_type=module_type,
        category=category,
        skip=skip,
        limit=limit
    )

    # 转换为摘要格式
    summaries = []
    for module in modules:
        summary = CustomModuleSummary(
            id=module.id,
            name=module.name,
            description=module.description,
            icon=module.icon,
            module_type=module.module_type,  # 添加module_type
            category=module.category,
            repeatable=module.repeatable,
            field_count=len(module.fields) if module.fields else 0,
            usage_count=module.usage_count,
            is_shared=module.is_shared,
            access_level=module.access_level,
            created_at=module.created_at
        )
        summaries.append(summary)

    return summaries


@router.get("/{module_id}", response_model=CustomModuleResponse)
def get_custom_module(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """获取单个自定义模块详情（带工作区上下文权限检查）"""
    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # 创建Service实例
    module_service = CustomModuleService(db)

    # 获取模块
    module = module_service.get_module(module_id, current_user, workspace_context)
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在或无权访问")

    return module


@router.post("/", response_model=CustomModuleResponse)
def create_custom_module(
    module_data: CustomModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """创建自定义模块（带工作区上下文）"""
    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # 创建Service实例
    module_service = CustomModuleService(db)

    # 创建模块
    module = module_service.create_module(
        module_data=module_data,
        current_user=current_user,
        workspace_context=workspace_context
    )

    return module


@router.put("/{module_id}", response_model=CustomModuleResponse)
def update_custom_module(
    module_id: str,
    module_data: CustomModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """更新自定义模块（带工作区上下文权限检查）"""
    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # 创建Service实例
    module_service = CustomModuleService(db)

    # 更新模块
    module = module_service.update_module(
        module_id=module_id,
        module_data=module_data,
        current_user=current_user,
        workspace_context=workspace_context
    )
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在或无权修改")

    return module


@router.delete("/{module_id}")
def delete_custom_module(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    """删除自定义模块（带工作区上下文权限检查）"""
    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # 创建Service实例
    module_service = CustomModuleService(db)

    # 删除模块
    success = module_service.delete_module(
        module_id=module_id,
        current_user=current_user,
        workspace_context=workspace_context
    )
    if not success:
        raise HTTPException(status_code=404, detail="模块不存在或无权删除")

    return {"message": "模块删除成功"}


@router.post("/{module_id}/increment-usage")
def increment_module_usage(
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """增加模块使用次数"""
    # 创建Service实例
    module_service = CustomModuleService(db)

    # 增加使用次数
    module_service.increment_usage(module_id)

    return {"message": "使用次数已更新"}


"""
工作区管理API端点
Workspace Management API Endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_verified_user
from app.models.user import User
from app.services.workspace_service import get_workspace_service


router = APIRouter()


class WorkspaceResponse(BaseModel):
    """工作区响应模型"""
    type: str
    id: str
    name: str
    description: str
    user_id: int
    company_id: int | None = None
    factory_id: int | None = None
    factory_name: str | None = None
    is_default: bool
    role: str | None = None
    company_role_id: int | None = None
    membership_tier: str
    quota_info: dict


class WorkspaceSwitchRequest(BaseModel):
    """工作区切换请求模型"""
    workspace_id: str


class WorkspaceSwitchResponse(BaseModel):
    """工作区切换响应模型"""
    success: bool
    message: str
    workspace: WorkspaceResponse


@router.get("/workspaces", response_model=List[WorkspaceResponse])
async def get_user_workspaces(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    获取用户所有可用的工作区
    
    返回用户的个人工作区和所有企业工作区列表
    """
    workspace_service = get_workspace_service(db)
    workspaces = workspace_service.get_user_workspaces(current_user)
    return workspaces


@router.get("/workspaces/default", response_model=WorkspaceResponse)
async def get_default_workspace(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的默认工作区
    
    通常是个人工作区
    """
    workspace_service = get_workspace_service(db)
    workspace = workspace_service.get_default_workspace(current_user)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到默认工作区"
        )
    
    return workspace


@router.post("/workspaces/switch", response_model=WorkspaceSwitchResponse)
async def switch_workspace(
    request: WorkspaceSwitchRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    切换工作区
    
    Args:
        request: 包含目标工作区ID的请求
        
    Returns:
        切换后的工作区信息
        
    工作区ID格式：
    - 个人工作区: personal_{user_id}
    - 企业工作区: enterprise_{company_id}
    """
    workspace_service = get_workspace_service(db)
    
    try:
        workspace = workspace_service.switch_workspace(
            current_user,
            request.workspace_id
        )
        
        return {
            "success": True,
            "message": f"已切换到工作区: {workspace['name']}",
            "workspace": workspace
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换工作区失败: {str(e)}"
        )


@router.get("/workspaces/current", response_model=WorkspaceResponse)
async def get_current_workspace(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的当前工作区

    Returns:
        当前工作区信息
    """
    workspace_service = get_workspace_service(db)

    try:
        # 首先尝试从用户会话或令牌中获取当前工作区
        # 如果没有设置，则返回默认工作区
        workspaces = workspace_service.get_user_workspaces(current_user)

        if not workspaces:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到可用工作区"
            )

        # 返回默认工作区（通常是个人工作区）
        current_workspace = None
        for workspace in workspaces:
            if workspace.get("is_default", False):
                current_workspace = workspace
                break

        # 如果没有找到默认工作区，返回第一个
        if not current_workspace:
            current_workspace = workspaces[0]

        return current_workspace

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取当前工作区失败: {str(e)}"
        )


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace_detail(
    workspace_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    获取指定工作区的详细信息
    
    Args:
        workspace_id: 工作区ID
        
    Returns:
        工作区详细信息
    """
    workspace_service = get_workspace_service(db)
    
    # 验证访问权限
    workspace_context = workspace_service.create_workspace_context(
        current_user,
        workspace_id
    )
    
    workspace_service.validate_workspace_access(current_user, workspace_context)
    
    # 获取工作区信息
    workspaces = workspace_service.get_user_workspaces(current_user)
    for workspace in workspaces:
        if workspace["id"] == workspace_id:
            return workspace
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="工作区不存在"
    )


@router.get("/workspaces/{workspace_id}/quota")
async def get_workspace_quota(
    workspace_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    获取工作区的配额使用情况
    
    Args:
        workspace_id: 工作区ID
        
    Returns:
        配额详细信息
    """
    workspace_service = get_workspace_service(db)
    
    # 验证访问权限
    workspace_context = workspace_service.create_workspace_context(
        current_user,
        workspace_id
    )
    
    workspace_service.validate_workspace_access(current_user, workspace_context)
    
    # 获取工作区信息
    workspaces = workspace_service.get_user_workspaces(current_user)
    for workspace in workspaces:
        if workspace["id"] == workspace_id:
            return {
                "workspace_id": workspace_id,
                "workspace_name": workspace["name"],
                "workspace_type": workspace["type"],
                "membership_tier": workspace["membership_tier"],
                "quota": workspace["quota_info"]
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="工作区不存在"
    )


@router.get("/context")
async def get_workspace_context_info(
    workspace_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    获取工作区上下文信息（用于前端状态管理）
    
    Args:
        workspace_id: 工作区ID
        
    Returns:
        工作区上下文信息
    """
    workspace_service = get_workspace_service(db)
    
    # 创建工作区上下文
    workspace_context = workspace_service.create_workspace_context(
        current_user,
        workspace_id
    )
    
    return {
        "user_id": workspace_context.user_id,
        "workspace_type": workspace_context.workspace_type,
        "company_id": workspace_context.company_id,
        "factory_id": workspace_context.factory_id,
        "is_personal": workspace_context.is_personal(),
        "is_enterprise": workspace_context.is_enterprise()
    }


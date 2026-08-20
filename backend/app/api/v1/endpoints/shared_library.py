"""
共享库API端点
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.api.admin_deps import get_current_active_admin
from app.core.auth import oauth2_scheme
from app.models.user import User
from app.models.admin import Admin
from app.models.shared_library import SharedModule, SharedTemplate, SharedComment
from app.services.shared_library_service import SharedLibraryService
from app.schemas.shared_library import (
    SharedModule as SharedModuleSchema,
    SharedTemplate as SharedTemplateSchema,
    SharedModuleCreate,
    SharedTemplateCreate,
    SharedModuleUpdate,
    SharedTemplateUpdate,
    UserRatingCreate,
    SharedCommentCreate,
    SharedComment as SharedCommentSchema,
    LibrarySearchQuery,
    ReviewAction,
    FeaturedAction,
    LibraryStats
)

router = APIRouter()


def get_client_ip(request: Request) -> Optional[str]:
    """获取客户端IP地址"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选） - 用于共享库等允许匿名访问的端点"""
    if not token or token == "":
        return None

    try:
        # 直接使用get_current_user的逻辑，但不抛出异常
        from jose import JWTError, jwt
        from app.core.config import settings

        # 解码JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            return None

        # 从数据库获取用户
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except (JWTError, ValueError, KeyError, AttributeError, TypeError):
        # 如果token无效或过期，返回None而不是抛出异常
        return None


# ==================== 共享模块相关API ====================

@router.post("/modules/share", response_model=SharedModuleSchema)
def share_module(
    module_data: SharedModuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """共享自定义模块到共享库"""
    service = SharedLibraryService(db)
    return service.create_shared_module(module_data, current_user.id)


@router.get("/modules", response_model=dict)
def get_shared_modules(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    difficulty_level: Optional[str] = Query(None, description="难度筛选"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    status: str = Query("approved", description="状态筛选，使用'all'查询所有状态"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    featured_only: bool = Query(False, description="只显示推荐内容"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """获取共享模块列表"""
    # 如果status是'all'，则设置为None以查询所有状态
    query_status = None if status == "all" else status

    query = LibrarySearchQuery(
        keyword=keyword,
        category=category,
        difficulty_level=difficulty_level,
        tags=tags,
        status=query_status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        featured_only=featured_only
    )

    service = SharedLibraryService(db)
    modules, total = service.get_shared_modules(query, current_user.id if current_user else None)

    # 使用Pydantic序列化SQLAlchemy对象
    from pydantic import TypeAdapter
    from app.schemas.shared_library import SharedModule as SharedModuleSchema

    adapter = TypeAdapter(list[SharedModuleSchema])
    serialized_modules = adapter.dump_python(modules, mode='json')

    return {
        "items": serialized_modules,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/modules/{module_id}", response_model=SharedModuleSchema)
def get_shared_module(
    module_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """获取共享模块详情"""
    service = SharedLibraryService(db)
    module = service.get_shared_module_by_id(module_id, current_user.id if current_user else None)

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="共享模块不存在"
        )

    return module


@router.post("/modules/{module_id}/download")
def download_shared_module(
    module_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    db: Session = Depends(get_db)
):
    """下载共享模块到当前工作区"""
    from app.api.v1.endpoints.wps_templates import get_workspace_context

    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    service = SharedLibraryService(db)
    ip_address = get_client_ip(request)

    try:
        result = service.download_shared_module(
            module_id,
            current_user.id,
            ip_address,
            workspace_context.workspace_type,
            workspace_context.company_id,
            workspace_context.factory_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载失败: {str(e)}"
        )


@router.put("/modules/{module_id}", response_model=SharedModuleSchema)
def update_shared_module(
    module_id: str,
    module_data: SharedModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新共享模块信息（仅上传者可操作）"""
    service = SharedLibraryService(db)
    module = service.get_shared_module_by_id(module_id)

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="共享模块不存在"
        )

    if module.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作此模块"
        )

    # 更新模块信息
    update_data = module_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(module, field, value)

    db.commit()
    db.refresh(module)
    return module


@router.delete("/modules/{module_id}")
def delete_shared_module(
    module_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除共享模块（仅上传者可操作）"""
    service = SharedLibraryService(db)

    try:
        success = service.delete_shared_module(module_id, current_user.id)
        if success:
            return {"message": "模块删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


# ==================== 共享模板相关API ====================

@router.post("/templates/share")
def share_template(
    template_data: SharedTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """共享WPS模板到共享库"""
    import logging
    logger = logging.getLogger(__name__)

    # 详细调试信息
    logger.info(f"=== 开始处理模板分享请求 ===")
    logger.info(f"请求用户ID: {current_user.id}")
    logger.info(f"请求用户名: {current_user.username}")
    logger.info(f"原始模板ID: {template_data.original_template_id}")
    logger.info(f"模板名称: {template_data.name}")
    logger.info(f"模板描述: {template_data.description}")
    logger.info(f"焊接工艺: {template_data.welding_process}")
    logger.info(f"模块实例数量: {len(template_data.module_instances) if template_data.module_instances else 0}")

    try:
        service = SharedLibraryService(db)
        logger.info("开始创建共享模板...")
        result = service.create_shared_template(template_data, current_user.id)
        logger.info(f"模板分享成功，共享模板ID: {result.id}")
        return result
    except Exception as e:
        logger.error(f"模板分享失败，错误详情: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise


@router.get("/templates", response_model=dict)
def get_shared_templates(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    welding_process: Optional[str] = Query(None, description="焊接工艺筛选"),
    standard: Optional[str] = Query(None, description="标准筛选"),
    difficulty_level: Optional[str] = Query(None, description="难度筛选"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    status: str = Query("approved", description="状态筛选，使用'all'查询所有状态"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    featured_only: bool = Query(False, description="只显示推荐内容"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """获取共享模板列表"""
    # 如果status是'all'，则设置为None以查询所有状态
    query_status = None if status == "all" else status

    query = LibrarySearchQuery(
        keyword=keyword,
        difficulty_level=difficulty_level,
        tags=tags,
        status=query_status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        featured_only=featured_only
    )

    # 添加额外的筛选参数
    if welding_process:
        query.welding_process = welding_process
    if standard:
        query.standard = standard

    service = SharedLibraryService(db)
    templates, total = service.get_shared_templates(query, current_user.id if current_user else None)

    # 使用Pydantic序列化SQLAlchemy对象
    from pydantic import TypeAdapter
    from app.schemas.shared_library import SharedTemplate as SharedTemplateSchema

    adapter = TypeAdapter(list[SharedTemplateSchema])
    serialized_templates = adapter.dump_python(templates, mode='json')

    return {
        "items": serialized_templates,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/templates/{template_id}", response_model=SharedTemplateSchema)
def get_shared_template(
    template_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """获取共享模板详情"""
    service = SharedLibraryService(db)
    template = service.get_shared_template_by_id(template_id, current_user.id if current_user else None)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="共享模板不存在"
        )

    return template


@router.post("/templates/{template_id}/download")
def download_shared_template(
    template_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    db: Session = Depends(get_db)
):
    """下载共享模板到当前工作区"""
    from app.api.v1.endpoints.wps_templates import get_workspace_context

    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    service = SharedLibraryService(db)
    ip_address = get_client_ip(request)

    try:
        result = service.download_shared_template(
            template_id,
            current_user.id,
            ip_address,
            workspace_context.workspace_type,
            workspace_context.company_id,
            workspace_context.factory_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载失败: {str(e)}"
        )


@router.put("/templates/{template_id}", response_model=SharedTemplateSchema)
def update_shared_template(
    template_id: str,
    template_data: SharedTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新共享模板信息（仅上传者可操作）"""
    service = SharedLibraryService(db)
    template = service.get_shared_template_by_id(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="共享模板不存在"
        )

    if template.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作此模板"
        )

    # 更新模板信息
    update_data = template_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}")
def delete_shared_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除共享模板（仅上传者可操作）"""
    service = SharedLibraryService(db)

    try:
        success = service.delete_shared_template(template_id, current_user.id)
        if success:
            return {"message": "模板删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


# ==================== 评分相关API ====================

@router.post("/rate", response_model=dict)
def rate_shared_resource(
    rating_data: UserRatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """对共享资源进行评分（点赞/点踩）"""
    service = SharedLibraryService(db)
    rating = service.rate_shared_resource(rating_data, current_user.id)

    return {
        "message": "评分成功",
        "rating_type": rating.rating_type
    }


# ==================== 评论相关API ====================

@router.post("/comments", response_model=SharedCommentSchema)
def create_comment(
    comment_data: SharedCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建评论"""
    service = SharedLibraryService(db)
    comment = service.create_comment(comment_data, current_user.id)
    return comment


@router.get("/comments/{target_type}/{target_id}", response_model=dict)
def get_comments(
    target_type: str,
    target_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取评论列表"""
    if target_type not in ["module", "template"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的评论对象类型"
        )

    service = SharedLibraryService(db)
    comments, total = service.get_comments(target_type, target_id, page, page_size)

    return {
        "items": comments,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


# ==================== 管理员API（管理门户 Admin Token） ====================

@router.post("/admin/review/{resource_type}/{resource_id}")
def review_shared_resource(
    resource_type: str,
    resource_id: str,
    review_action: ReviewAction,
    current_admin: Admin = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """审核共享资源（管理门户）"""
    if resource_type not in ["module", "template"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的资源类型"
        )

    # reviewer_id 外键指向 users.id；未绑定门户用户时留空，避免 FK 失败
    reviewer_id = current_admin.user_id
    service = SharedLibraryService(db)
    success = service.review_shared_resource(resource_type, resource_id, review_action, reviewer_id)

    if success:
        return {"message": "审核成功"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="审核失败"
        )


@router.post("/admin/featured/{resource_type}/{resource_id}")
def set_featured_resource(
    resource_type: str,
    resource_id: str,
    featured_action: FeaturedAction,
    current_admin: Admin = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """设置/取消推荐共享资源（管理门户）"""
    if resource_type not in ["module", "template"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的资源类型"
        )

    service = SharedLibraryService(db)
    success = service.set_featured_resource(resource_type, resource_id, featured_action)

    if success:
        return {"message": "推荐设置成功"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="推荐设置失败"
        )


@router.get("/admin/stats", response_model=LibraryStats)
def get_library_stats(
    current_admin: Admin = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """获取共享库统计信息（管理门户）"""
    service = SharedLibraryService(db)
    stats = service.get_library_stats()
    return stats


@router.get("/admin/pending/{resource_type}")
def get_pending_resources(
    resource_type: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_admin: Admin = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """获取待审核资源列表（管理门户）"""
    if resource_type not in ["module", "template"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的资源类型"
        )

    query = LibrarySearchQuery(
        status="pending",
        page=page,
        page_size=page_size,
        sort_by="created_at",
        sort_order="desc"
    )

    service = SharedLibraryService(db)

    if resource_type == "module":
        resources, total = service.get_shared_modules(query)
        from pydantic import TypeAdapter
        from app.schemas.shared_library import SharedModule as SharedModuleSchema
        adapter = TypeAdapter(list[SharedModuleSchema])
        serialized_resources = adapter.dump_python(resources, mode='json')
    else:
        resources, total = service.get_shared_templates(query)
        from pydantic import TypeAdapter
        from app.schemas.shared_library import SharedTemplate as SharedTemplateSchema
        adapter = TypeAdapter(list[SharedTemplateSchema])
        serialized_resources = adapter.dump_python(resources, mode='json')

    return {
        "items": serialized_resources,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/admin/resources/{resource_type}")
def get_admin_resources(
    resource_type: str,
    status: Optional[str] = Query(None, description="状态筛选，空或 all 表示全部"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    current_admin: Admin = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """管理端资源列表（含全部状态）"""
    if resource_type not in ["module", "template"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的资源类型"
        )

    query_status = None if (not status or status == "all") else status
    query = LibrarySearchQuery(
        keyword=keyword,
        status=query_status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    service = SharedLibraryService(db)
    if resource_type == "module":
        resources, total = service.get_shared_modules(query)
        from pydantic import TypeAdapter
        from app.schemas.shared_library import SharedModule as SharedModuleSchema
        adapter = TypeAdapter(list[SharedModuleSchema])
        serialized_resources = adapter.dump_python(resources, mode="json")
    else:
        resources, total = service.get_shared_templates(query)
        from pydantic import TypeAdapter
        from app.schemas.shared_library import SharedTemplate as SharedTemplateSchema
        adapter = TypeAdapter(list[SharedTemplateSchema])
        serialized_resources = adapter.dump_python(resources, mode="json")

    return {
        "items": serialized_resources,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/admin/resources/{resource_type}/{resource_id}")
def get_admin_resource_detail(
    resource_type: str,
    resource_id: str,
    current_admin: Admin = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """管理端资源详情（不增加浏览量）"""
    if resource_type not in ["module", "template"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的资源类型"
        )

    service = SharedLibraryService(db)
    if resource_type == "module":
        resource = service.get_shared_module_by_id(resource_id, user_id=None)
    else:
        resource = service.get_shared_template_by_id(resource_id, user_id=None)

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="共享资源不存在"
        )

    return resource
"""
WPS Template API endpoints for the welding system backend.
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.company import CompanyEmployee
from app.schemas.wps_template import (
    WPSTemplateCreate,
    WPSTemplateUpdate,
    WPSTemplateResponse,
    WPSTemplateSummary,
    WPSTemplateListResponse
)
from app.services.wps_template_service import WPSTemplateService
from app.services.custom_module_service import CustomModuleService
from app.services.extraction_schema_service import build_template_extraction_schema
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


@router.get("/", response_model=WPSTemplateListResponse)
def get_templates(
    *,
    db: Session = Depends(deps.get_db),
    welding_process: Optional[str] = Query(None, description="焊接工艺代码过滤"),
    standard: Optional[str] = Query(None, description="标准过滤"),
    module_type: Optional[str] = Query(None, description="模块类型过滤: wps/pqr/ppqr"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    获取用户可用的WPS模板列表（带工作区上下文数据隔离）
    包括：系统模板 + 用户自己的模板 + 企业共享模板

    权限说明：
    - 所有激活用户都可以访问（系统模板对所有人可见）
    - 个人工作区：可以看到系统模板 + 自己的模板
    - 企业工作区：可以看到系统模板 + 企业共享模板 + 自己的模板
    """
    try:
        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)

        # 创建Service实例
        template_service = WPSTemplateService(db)

        # 获取模板列表
        templates, total = template_service.get_available_templates(
            current_user=current_user,
            workspace_context=workspace_context,
            welding_process=welding_process,
            standard=standard,
            module_type=module_type,
            skip=skip,
            limit=limit
        )

        return {
            "total": total,
            "items": templates
        }
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 记录未预期的错误
        print(f"获取WPS模板列表时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取WPS模板列表失败，请稍后重试"
        )


@router.get("/{template_id}", response_model=WPSTemplateResponse)
def get_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    获取WPS模板详情（带工作区上下文权限检查）

    权限说明：
    - 系统模板：所有人可访问
    - 个人模板：仅创建者可访问
    - 企业模板：企业成员可访问（如果是共享模板）
    """
    try:
        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)

        # 创建Service实例
        template_service = WPSTemplateService(db)

        # 获取模板
        template = template_service.get_template_by_id(
            template_id=template_id,
            current_user=current_user,
            workspace_context=workspace_context
        )
        return template
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 记录未预期的错误
        print(f"获取WPS模板详情时发生错误 (template_id={template_id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取WPS模板详情失败，请稍后重试"
        )


@router.get("/{template_id}/extraction-schema")
def get_template_extraction_schema(
    *,
    db: Session = Depends(deps.get_db),
    template_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> dict[str, Any]:
    """汇总模板中的可访问模块，生成动态结构化提取 Schema。"""
    workspace_context = get_workspace_context(db, current_user, workspace_id)
    template = WPSTemplateService(db).get_template_by_id(
        template_id=template_id,
        current_user=current_user,
        workspace_context=workspace_context,
    )
    module_service = CustomModuleService(db)
    modules = []
    seen: set[str] = set()
    for instance in template.module_instances or []:
        module_id = instance["moduleId"]
        if module_id in seen:
            continue
        seen.add(module_id)
        module = module_service.get_module(module_id, current_user, workspace_context)
        if module is not None:
            modules.append(module)
    return build_template_extraction_schema(template, modules)


@router.post("/", response_model=WPSTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: WPSTemplateCreate,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """创建用户自定义WPS模板（带工作区上下文）"""
    try:
        print(f"\n========== 创建模板请求 ==========")
        print(f"当前用户: {current_user.id} ({current_user.username})")
        print(f"用户会员类型: {current_user.membership_type}")
        print(f"X-Workspace-ID header: {workspace_id}")
        print(f"创建模板请求数据: {template_in}")

        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)
        print(f"工作区上下文:")
        print(f"  - workspace_type: {workspace_context.workspace_type}")
        print(f"  - user_id: {workspace_context.user_id}")
        print(f"  - company_id: {workspace_context.company_id}")
        print(f"  - factory_id: {workspace_context.factory_id}")

        # 创建Service实例
        template_service = WPSTemplateService(db)

        # 创建模板
        template = template_service.create_template(
            template_in=template_in,
            current_user=current_user,
            workspace_context=workspace_context
        )
        print(f"模板创建成功:")
        print(f"  - ID: {template.id}")
        print(f"  - 名称: {template.name}")
        print(f"  - workspace_type: {template.workspace_type}")
        print(f"  - template_source: {template.template_source}")
        print(f"========== 创建模板完成 ==========\n")
        return template
    except Exception as e:
        print(f"创建模板时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建WPS模板失败: {str(e)}"
        )


@router.put("/{template_id}", response_model=WPSTemplateResponse)
def update_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: str,
    template_in: WPSTemplateUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """更新WPS模板（带工作区上下文权限检查）"""
    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # 创建Service实例
    template_service = WPSTemplateService(db)

    # 更新模板
    template = template_service.update_template(
        template_id=template_id,
        template_in=template_in,
        current_user=current_user,
        workspace_context=workspace_context
    )
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> None:
    """删除WPS模板（软删除，带工作区上下文权限检查）"""
    # 获取工作区上下文
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # 创建Service实例
    template_service = WPSTemplateService(db)

    # 删除模板
    template_service.delete_template(
        template_id=template_id,
        current_user=current_user,
        workspace_context=workspace_context
    )
    return None


@router.get("/welding-processes/list")
def get_welding_processes(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """获取所有可用的焊接工艺列表"""
    processes = [
        {"code": "111", "name": "手工电弧焊", "name_en": "SMAW"},
        {"code": "114", "name": "无保护气的药芯焊", "name_en": "FCAW"},
        {"code": "121", "name": "埋弧焊", "name_en": "SAW"},
        {"code": "135", "name": "熔化极活性气体保护焊", "name_en": "MAG"},
        {"code": "141", "name": "钨极惰性气体保护焊", "name_en": "TIG/GTAW"},
        {"code": "15", "name": "等离子焊", "name_en": "Plasma Welding"},
        {"code": "311", "name": "氧乙炔焊", "name_en": "Oxy-acetylene Welding"}
    ]
    return processes


@router.get("/standards/list")
def get_standards(
    *,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_active_user)
) -> Any:
    """获取所有可用的焊接标准列表"""
    standards = [
        {"code": "EN_ISO_15609_1", "name": "EN ISO 15609-1"},
        {"code": "AWS_D1_1", "name": "AWS D1.1"},
        {"code": "ASME_IX", "name": "ASME Section IX"},
        {"code": "GB_T", "name": "GB/T"},
        {"code": "CUSTOM", "name": "自定义标准"}
    ]
    return standards


"""
pPQR (preliminary Procedure Qualification Record) API endpoints for the welding system backend.
"""
from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.company import CompanyEmployee
from app.models.ppqr import PPQR
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.services.workspace_service import WorkspaceService
from app.services.ppqr_service import PPQRService
from app.services.approval_service import ApprovalService
from app.services.approval_lookup import load_latest_approvals
from app.schemas.ppqr import (
    PPQRCreate,
    PPQRUpdate,
    PPQRResponse,
    PPQRSummary,
    PPQRListResponse
)

router = APIRouter()


def get_workspace_context(
    db: Session,
    current_user: User,
    workspace_id: Optional[str] = None
) -> WorkspaceContext:
    """
    Get workspace context from header or user's default workspace.

    Args:
        db: Database session
        current_user: Current user
        workspace_id: Workspace ID from header (optional)

    Returns:
        WorkspaceContext object
    """
    workspace_service = WorkspaceService(db)

    # If workspace_id is provided in header, use it
    if workspace_id:
        return workspace_service.create_workspace_context(current_user, workspace_id)

    # Otherwise, determine default workspace based on user's membership type
    if current_user.membership_type == "enterprise":
        # Enterprise user, find their company
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

    # Default to personal workspace
    return WorkspaceContext(
        user_id=current_user.id,
        workspace_type=WorkspaceType.PERSONAL
    )


@router.get("/")
def get_ppqr_list(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页记录数"),
    skip: int = Query(None, ge=0, description="跳过记录数（可选，优先使用page）"),
    limit: int = Query(None, ge=1, le=1000, description="返回记录数（可选，优先使用page_size）"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    test_conclusion: Optional[str] = Query(None, description="试验结论筛选"),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    获取pPQR列表（带工作区上下文数据隔离和分页）

    - **page**: 页码（从1开始）
    - **page_size**: 每页记录数
    - **keyword**: 搜索关键词（搜索pPQR编号、标题、试验目的）
    - **status**: 状态筛选 (draft, review, approved, rejected)
    - **test_conclusion**: 试验结论筛选
    """
    try:
        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)

        # 计算 skip 和 limit（优先使用 page 和 page_size）
        actual_skip = skip if skip is not None else (page - 1) * page_size
        actual_limit = limit if limit is not None else page_size

        # 初始化pPQR服务
        ppqr_service = PPQRService(db)

        # 获取总数
        total = ppqr_service.count(
            db,
            current_user=current_user,
            workspace_context=workspace_context,
            status=status,
            test_conclusion=test_conclusion,
            search_term=keyword
        )

        # 获取pPQR列表
        ppqr_list = ppqr_service.get_multi(
            db,
            skip=actual_skip,
            limit=actual_limit,
            current_user=current_user,
            workspace_context=workspace_context,
            status=status,
            test_conclusion=test_conclusion,
            search_term=keyword
        )

        approval_service = ApprovalService(db)
        latest, workflows = load_latest_approvals(db, "ppqr", [item.id for item in ppqr_list])
        can_submit_default = approval_service.should_require_approval("ppqr", workspace_context)
        approver_perms = approval_service.load_approver_permissions(current_user)
        ppqr_summaries = []
        for ppqr in ppqr_list:
            approval_instance = latest.get(ppqr.id)
            workflow = workflows.get(approval_instance.workflow_id) if approval_instance else None
            can_approve = False
            can_submit_approval = False
            if approval_instance:
                if approval_instance.status in ["pending", "in_progress"]:
                    can_approve = approval_service._can_approve(
                        approval_instance, current_user, approver_perms
                    )
            else:
                can_submit_approval = can_submit_default

            convert_to_pqr_value = None
            if hasattr(ppqr, "convert_to_pqr"):
                if isinstance(ppqr.convert_to_pqr, bool):
                    convert_to_pqr_value = "yes" if ppqr.convert_to_pqr else "no"
                elif isinstance(ppqr.convert_to_pqr, str):
                    convert_to_pqr_value = ppqr.convert_to_pqr

            test_date_value = None
            if hasattr(ppqr, "actual_test_date") and ppqr.actual_test_date:
                test_date_value = ppqr.actual_test_date
            elif hasattr(ppqr, "planned_test_date") and ppqr.planned_test_date:
                test_date_value = ppqr.planned_test_date

            ppqr_summaries.append(PPQRSummary(
                id=ppqr.id,
                ppqr_number=ppqr.ppqr_number,
                title=ppqr.title,
                revision=ppqr.revision if ppqr.revision else "A",
                status=ppqr.status if ppqr.status else "draft",
                test_date=test_date_value,
                test_conclusion=ppqr.test_conclusion,
                convert_to_pqr=convert_to_pqr_value,
                created_at=ppqr.created_at,
                updated_at=ppqr.updated_at,
                approval_instance_id=approval_instance.id if approval_instance else None,
                approval_status=approval_instance.status if approval_instance else None,
                workflow_name=workflow.name if workflow else None,
                can_approve=can_approve,
                can_submit_approval=can_submit_approval,
                submitter_id=approval_instance.submitter_id if approval_instance else None,
            ))

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        return PPQRListResponse(
            items=ppqr_summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        print(f"[ERROR] 获取pPQR列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取pPQR列表失败: {str(e)}"
        )


@router.post("/")
def create_ppqr(
    ppqr_data: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    创建新pPQR（带工作区上下文）
    """
    try:
        # 打印接收到的数据用于调试
        print(f"[DEBUG] 接收到的pPQR数据: {ppqr_data}")

        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)

        # 检查会员配额（仅个人工作区）
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            from app.services.membership_service import MembershipService
            membership_service = MembershipService(db)

            if not membership_service.check_quota_available(current_user, "ppqr"):
                limits = membership_service.get_membership_limits(current_user.member_tier)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"已达到pPQR配额限制 ({limits.get('ppqr', 0)}个)，请升级会员等级"
                )

        # 初始化pPQR服务
        ppqr_service = PPQRService(db)

        # 创建pPQR
        ppqr = ppqr_service.create(
            db,
            ppqr_data=ppqr_data,
            current_user=current_user,
            workspace_context=workspace_context
        )

        # 更新配额使用情况（仅个人工作区）
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            from app.services.membership_service import MembershipService
            membership_service = MembershipService(db)
            membership_service.update_quota_usage(current_user, "ppqr", 1)

        # 构建响应数据
        response_data = {
            "id": ppqr.id,
            "title": ppqr.title,
            "ppqr_number": ppqr.ppqr_number,
            "revision": ppqr.revision,
            "status": ppqr.status,
            "template_id": ppqr.template_id,
            "module_data": ppqr.module_data,
            "owner_id": ppqr.user_id,
            "created_at": ppqr.created_at.isoformat() if ppqr.created_at else None,
            "updated_at": ppqr.updated_at.isoformat() if ppqr.updated_at else None
        }

        print(f"[DEBUG] 返回的pPQR数据: {response_data}")

        return response_data

    except ValueError as e:
        # 业务逻辑错误（如pPQR编号重复）
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] 创建pPQR失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建pPQR失败: {str(e)}"
        )


@router.get("/statistics")
@router.get("/statistics/overview")
def get_ppqr_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """获取pPQR统计信息"""
    workspace_context = get_workspace_context(db, current_user, workspace_id)
    ppqr_service = PPQRService(db)
    return {
        "success": True,
        "data": ppqr_service.get_statistics(
            db, current_user=current_user, workspace_context=workspace_context
        ),
        "message": "获取pPQR统计成功"
    }


@router.get("/{ppqr_id}")
def get_ppqr_detail(
    ppqr_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    获取pPQR详情（带工作区上下文）
    """
    try:
        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)

        # 初始化pPQR服务
        ppqr_service = PPQRService(db)

        # 获取pPQR
        ppqr = ppqr_service.get(
            db,
            id=ppqr_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        if not ppqr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="pPQR不存在或无权访问"
            )

        # 查询关联的审批实例和工作流信息
        from app.models.approval import ApprovalInstance, ApprovalWorkflowDefinition
        from app.services.approval_service import ApprovalService

        approval_instance = db.query(ApprovalInstance).filter(
            ApprovalInstance.document_type == "ppqr",
            ApprovalInstance.document_id == ppqr.id
        ).order_by(ApprovalInstance.created_at.desc()).first()

        # 初始化审批服务
        approval_service = ApprovalService(db)

        # 获取审批相关信息
        workflow_name = None
        approval_status = None
        approval_instance_id = None
        submitter_id = None
        can_approve = False
        can_submit_approval = False

        if approval_instance:
            approval_instance_id = approval_instance.id
            approval_status = approval_instance.status
            submitter_id = approval_instance.submitter_id

            # 查询工作流定义
            workflow = db.query(ApprovalWorkflowDefinition).filter(
                ApprovalWorkflowDefinition.id == approval_instance.workflow_id
            ).first()

            if workflow:
                workflow_name = workflow.name

            # 检查当前用户是否可以审批
            if approval_instance.status in ['pending', 'in_progress']:
                can_approve = approval_service._can_approve(approval_instance, current_user)
        else:
            # 没有审批实例，检查是否可以提交审批
            can_submit_approval = approval_service.should_require_approval('ppqr', workspace_context)

        # 构建响应数据
        response_data = {
            "id": ppqr.id,
            "title": ppqr.title,
            "ppqr_number": ppqr.ppqr_number,
            "revision": ppqr.revision,
            "status": ppqr.status,
            "template_id": ppqr.template_id,
            "module_data": ppqr.module_data,
            "modules_data": ppqr.module_data,  # 兼容前端
            "test_date": ppqr.planned_test_date.isoformat() if ppqr.planned_test_date else None,
            "test_conclusion": ppqr.test_conclusion,
            "convert_to_pqr": "yes" if ppqr.converted_to_pqr else "no",
            "owner_id": ppqr.user_id,
            "created_at": ppqr.created_at.isoformat() if ppqr.created_at else None,
            "updated_at": ppqr.updated_at.isoformat() if ppqr.updated_at else None,
            "created_by": ppqr.created_by,
            "updated_by": ppqr.updated_by,
            "approval_instance_id": approval_instance_id,
            "approval_status": approval_status,
            "workflow_name": workflow_name,
            "can_approve": can_approve,
            "can_submit_approval": can_submit_approval,
            "submitter_id": submitter_id
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 获取pPQR详情失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取pPQR详情失败: {str(e)}"
        )


@router.put("/{ppqr_id}")
def update_ppqr(
    ppqr_id: int,
    ppqr_data: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    更新pPQR（带工作区上下文）
    """
    try:
        print(f"[DEBUG] 更新pPQR {ppqr_id}，数据: {ppqr_data}")

        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)

        # 初始化pPQR服务
        ppqr_service = PPQRService(db)

        # 更新pPQR
        ppqr = ppqr_service.update(
            db,
            id=ppqr_id,
            ppqr_data=ppqr_data,
            current_user=current_user,
            workspace_context=workspace_context
        )

        if not ppqr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="pPQR不存在或无权访问"
            )

        # 构建响应数据
        response_data = {
            "id": ppqr.id,
            "title": ppqr.title,
            "ppqr_number": ppqr.ppqr_number,
            "revision": ppqr.revision,
            "status": ppqr.status,
            "template_id": ppqr.template_id,
            "module_data": ppqr.module_data,
            "modules_data": ppqr.module_data,  # 兼容前端
            "owner_id": ppqr.user_id,
            "created_at": ppqr.created_at.isoformat() if ppqr.created_at else None,
            "updated_at": ppqr.updated_at.isoformat() if ppqr.updated_at else None
        }

        print(f"[DEBUG] pPQR更新成功: {response_data}")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 更新pPQR失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新pPQR失败: {str(e)}"
        )


@router.delete("/{ppqr_id}")
def delete_ppqr(
    ppqr_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    删除pPQR（带工作区上下文）
    """
    try:
        print(f"[DEBUG] 开始删除pPQR {ppqr_id}")

        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)
        print(f"[DEBUG] 工作区上下文: {workspace_context.workspace_type}")

        # 初始化pPQR服务
        ppqr_service = PPQRService(db)

        # 删除pPQR
        print(f"[DEBUG] 调用删除服务...")
        success = ppqr_service.delete(
            db,
            id=ppqr_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        print(f"[DEBUG] 删除结果: {success}")

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="pPQR不存在或无权访问"
            )

        # 更新配额使用情况（仅个人工作区）
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            print(f"[DEBUG] 更新配额使用情况...")
            try:
                from app.services.membership_service import MembershipService
                membership_service = MembershipService(db)
                membership_service.update_quota_usage(current_user, "ppqr", -1)
                print(f"[DEBUG] 配额更新成功")
            except Exception as quota_error:
                # 配额更新失败不应该阻止删除操作
                print(f"[WARNING] 配额更新失败: {str(quota_error)}")
                import traceback
                traceback.print_exc()

        print(f"[DEBUG] pPQR删除成功")

        return {
            "success": True,
            "message": "pPQR删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 删除pPQR失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除pPQR失败: {str(e)}"
        )


@router.post("/{ppqr_id}/duplicate")
def duplicate_ppqr(
    ppqr_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    复制pPQR（带工作区上下文）
    """
    try:
        import time

        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)

        # 初始化pPQR服务
        ppqr_service = PPQRService(db)

        # 获取原始pPQR
        original_ppqr = ppqr_service.get(
            db,
            id=ppqr_id,
            current_user=current_user,
            workspace_context=workspace_context
        )

        if not original_ppqr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="pPQR不存在或无权访问"
            )

        # 检查配额（个人和企业工作区）
        from app.services.quota_service import QuotaService, QuotaType
        quota_service = QuotaService(db)

        try:
            quota_service.check_quota(
                current_user,
                workspace_context,
                QuotaType.PPQR,
                1
            )
        except HTTPException:
            raise

        # 构建新的pPQR数据
        ppqr_data = {
            "title": f"{original_ppqr.title} (副本)",
            "ppqr_number": f"{original_ppqr.ppqr_number}-COPY-{int(time.time())}",
            "revision": "A",  # 副本从A版本开始
            "status": "draft",  # 副本默认为草稿状态
            "template_id": original_ppqr.template_id,
            "module_data": original_ppqr.module_data,
        }

        # 创建新pPQR
        new_ppqr = ppqr_service.create(
            db,
            ppqr_data=ppqr_data,
            current_user=current_user,
            workspace_context=workspace_context
        )

        # 更新配额使用情况（仅个人工作区）
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            from app.services.membership_service import MembershipService
            membership_service = MembershipService(db)
            membership_service.update_quota_usage(current_user, "ppqr", 1)

        # 构建响应数据
        response_data = {
            "id": new_ppqr.id,
            "title": new_ppqr.title,
            "ppqr_number": new_ppqr.ppqr_number,
            "revision": new_ppqr.revision,
            "status": new_ppqr.status,
            "template_id": new_ppqr.template_id,
            "module_data": new_ppqr.module_data,
            "modules_data": new_ppqr.module_data,  # 兼容前端
            "owner_id": new_ppqr.user_id,
            "created_at": new_ppqr.created_at.isoformat() if new_ppqr.created_at else None,
            "updated_at": new_ppqr.updated_at.isoformat() if new_ppqr.updated_at else None
        }

        print(f"[DEBUG] pPQR复制成功: {response_data}")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 复制pPQR失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"复制pPQR失败: {str(e)}"
        )


# 注意：pPQR的审批功能使用统一的审批系统 API
# 请使用 /api/v1/approvals/submit 提交审批
# 请使用 /api/v1/approvals/{instance_id}/approve 批准
# 请使用 /api/v1/approvals/{instance_id}/reject 拒绝
# 详见 backend/app/api/v1/endpoints/approvals.py


@router.post("/{ppqr_id}/convert-to-pqr")
def convert_ppqr_to_pqr(
    ppqr_id: int,
    payload: dict = Body(default={}),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """将pPQR转换为PQR。"""
    workspace_context = get_workspace_context(db, current_user, workspace_id)
    ppqr_service = PPQRService(db)
    result = ppqr_service.convert_to_pqr(
        db,
        ppqr_id=ppqr_id,
        current_user=current_user,
        workspace_context=workspace_context,
        overrides=payload or {},
    )
    message = "该pPQR已转换过" if result.get("already_converted") else "转换成功"
    return {
        "success": True,
        "data": result,
        "message": message,
    }


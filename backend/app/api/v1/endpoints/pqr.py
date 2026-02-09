"""
PQR (Procedure Qualification Record) API endpoints for the welding system backend.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.company import CompanyEmployee
from app.schemas.pqr import (
    PQRCreate, PQRResponse, PQRUpdate, PQRSummary, PQRListResponse,
    PQRTestSpecimenCreate, PQRTestSpecimenResponse,
    PQRQualificationUpdate, PQRSearchParams, PQRExportRequest
)
from app.services.user_service import user_service
from app.services.workspace_service import WorkspaceService
from app.core.data_access import WorkspaceContext, WorkspaceType

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
        # For enterprise users, find their company
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


@router.get("/", response_model=PQRListResponse)
def read_pqr_list(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页记录数"),
    skip: int = Query(None, ge=0, description="跳过记录数（可选，优先使用page）"),
    limit: int = Query(None, ge=1, le=1000, description="返回记录数（可选，优先使用page_size）"),
    owner_id: int = Query(None, description="所有者ID过滤"),
    qualification_result: str = Query(None, description="评定结果过滤"),
    search_term: str = Query(None, description="搜索关键词"),
    keyword: str = Query(None, description="搜索关键词（别名）"),
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    检索PQR列表（带工作区上下文数据隔离和分页）.

    - 个人工作区：只返回用户自己的PQR
    - 企业工作区：只返回企业内的PQR
    """
    try:
        # Get workspace context
        print(f"DEBUG PQR: 开始获取工作区上下文, workspace_id={workspace_id}")
        workspace_context = get_workspace_context(db, current_user, workspace_id)
        print(f"DEBUG PQR: 工作区上下文获取成功: type={workspace_context.workspace_type}, user_id={workspace_context.user_id}")

        # Debug information
        print(f"DEBUG PQR: User {current_user.id}, membership_type={current_user.membership_type}, workspace_id={workspace_id}")

        # For now, allow all authenticated users to access PQR
        # TODO: Implement proper permission checking
        print(f"DEBUG PQR: User authenticated, allowing access")

        # 计算 skip 和 limit（优先使用 page 和 page_size）
        actual_skip = skip if skip is not None else (page - 1) * page_size
        actual_limit = limit if limit is not None else page_size

        # 使用 keyword 作为 search_term 的别名
        actual_search_term = search_term or keyword

        # Initialize PQR service
        from app.services.pqr_service import PQRService
        pqr_service_instance = PQRService(db)

        # Get total count with workspace filtering
        total = pqr_service_instance.count(
            db,
            current_user=current_user,
            workspace_context=workspace_context,
            owner_id=owner_id,
            qualification_result=qualification_result,
            search_term=actual_search_term
        )

        # Get PQR list with workspace filtering
        pqr_list = pqr_service_instance.get_multi(
            db,
            skip=actual_skip,
            limit=actual_limit,
            current_user=current_user,
            workspace_context=workspace_context,
            owner_id=owner_id,
            qualification_result=qualification_result,
            search_term=actual_search_term
        )

        # Convert to summary format with approval workflow info
        from app.models.approval import ApprovalInstance, ApprovalWorkflowDefinition
        from app.services.approval_service import ApprovalService

        approval_service = ApprovalService(db)
        pqr_summaries = []
        for pqr in pqr_list:
            # 查询关联的审批实例
            approval_instance = db.query(ApprovalInstance).filter(
                ApprovalInstance.document_type == "pqr",
                ApprovalInstance.document_id == pqr.id
            ).order_by(ApprovalInstance.created_at.desc()).first()

            # 获取工作流名称
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
                can_submit_approval = approval_service.should_require_approval('pqr', workspace_context)

            pqr_summaries.append(PQRSummary(
                id=pqr.id,
                title=pqr.title,
                pqr_number=pqr.pqr_number,
                wps_number=pqr.wps_number,
                test_date=pqr.test_date,
                company=pqr.company,
                welding_process=pqr.welding_process,
                base_material_spec=pqr.base_material_spec,
                qualification_result=pqr.qualification_result,
                status=pqr.status,
                created_at=pqr.created_at,
                updated_at=pqr.updated_at,
                approval_instance_id=approval_instance_id,
                approval_status=approval_status,
                workflow_name=workflow_name,
                can_approve=can_approve,
                can_submit_approval=can_submit_approval,
                submitter_id=submitter_id
            ))

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        return PQRListResponse(
            items=pqr_summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR PQR: 获取PQR列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取PQR列表失败: {str(e)}"
        )


@router.post("/", response_model=PQRResponse)
def create_pqr(
    *,
    db: Session = Depends(deps.get_db),
    pqr_in: PQRCreate,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    创建新的PQR（带工作区上下文）.

    - 个人工作区：创建个人PQR
    - 企业工作区：创建企业PQR
    """
    # Get workspace context
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # Check permission (enterprise members have access by default)
    if current_user.membership_type != "enterprise":
        if not user_service.has_permission(db, current_user.id, "pqr", "create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限"
            )

    try:
        # 检查会员配额 (only for personal workspace)
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            from app.services.membership_service import MembershipService
            membership_service = MembershipService(db)

            if not membership_service.check_quota_available(current_user, "pqr"):
                limits = membership_service.get_membership_limits(current_user.member_tier)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"已达到PQR配额限制 ({limits['pqr']}个)，请升级会员等级"
                )

        # 创建PQR with workspace context
        from app.services.pqr_service import PQRService
        pqr_service_instance = PQRService(db)
        pqr = pqr_service_instance.create(
            db,
            obj_in=pqr_in,
            current_user=current_user,
            workspace_context=workspace_context
        )

        # 更新配额使用情况 (only for personal workspace)
        if workspace_context.workspace_type == WorkspaceType.PERSONAL:
            from app.services.membership_service import MembershipService
            membership_service = MembershipService(db)
            membership_service.update_quota_usage(current_user, "pqr", 1)

        return pqr
    except ValueError as e:
        # 业务逻辑错误（如PQR编号重复）
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 其他错误，记录详细信息
        import traceback
        error_detail = f"创建PQR失败: {str(e)}"
        print(f"[ERROR] {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/{id}", response_model=PQRResponse)
def read_pqr_by_id(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    通过ID获取PQR（带工作区上下文数据隔离）.

    只能获取当前工作区内的PQR。
    """
    # Get workspace context
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # Check permission
    if current_user.membership_type != "enterprise":
        if not user_service.has_permission(db, current_user.id, "pqr", "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限"
            )

    # Get PQR with workspace filtering
    from app.services.pqr_service import PQRService
    pqr_service_instance = PQRService(db)
    pqr = pqr_service_instance.get(
        db,
        id=id,
        current_user=current_user,
        workspace_context=workspace_context
    )

    if not pqr:
        raise HTTPException(status_code=404, detail="PQR未找到或无权访问")

    # 查询关联的审批实例和工作流信息
    from app.models.approval import ApprovalInstance, ApprovalWorkflowDefinition

    approval_instance = db.query(ApprovalInstance).filter(
        ApprovalInstance.document_type == "pqr",
        ApprovalInstance.document_id == pqr.id
    ).order_by(ApprovalInstance.created_at.desc()).first()

    # 创建响应字典
    pqr_dict = {
        **{k: v for k, v in pqr.__dict__.items() if not k.startswith('_')},
        "approval_instance_id": None,
        "approval_status": None,
        "workflow_name": None
    }

    if approval_instance:
        pqr_dict["approval_instance_id"] = approval_instance.id
        pqr_dict["approval_status"] = approval_instance.status

        # 查询工作流定义
        workflow = db.query(ApprovalWorkflowDefinition).filter(
            ApprovalWorkflowDefinition.id == approval_instance.workflow_id
        ).first()

        if workflow:
            pqr_dict["workflow_name"] = workflow.name

    return pqr_dict


@router.put("/{id}", response_model=PQRResponse)
def update_pqr(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    pqr_in: PQRUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    更新PQR（带权限检查和工作区上下文）.

    只能更新当前工作区内有权限的PQR。
    """
    # Get workspace context
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # Check permission
    if current_user.membership_type != "enterprise":
        if not user_service.has_permission(db, current_user.id, "pqr", "update"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限"
            )

    # Get PQR with workspace filtering
    from app.services.pqr_service import PQRService
    pqr_service_instance = PQRService(db)
    pqr = pqr_service_instance.get(
        db,
        id=id,
        current_user=current_user,
        workspace_context=workspace_context
    )

    if not pqr:
        raise HTTPException(status_code=404, detail="PQR未找到")

    # 检查是否为所有者或管理员
    if pqr.user_id != current_user.id and not current_user.is_superuser:
        # For enterprise workspace, check if user is admin
        if workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            employee = db.query(CompanyEmployee).filter(
                CompanyEmployee.user_id == current_user.id,
                CompanyEmployee.company_id == workspace_context.company_id,
                CompanyEmployee.status == "active"
            ).first()

            if not employee or employee.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只能更新自己的PQR或需要管理员权限"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能更新自己的PQR"
            )

    try:
        pqr = pqr_service_instance.update(db, db_obj=pqr, obj_in=pqr_in)
        return pqr
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id}", response_model=PQRResponse)
def delete_pqr(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """
    删除PQR（带权限检查和工作区上下文）.

    只能删除当前工作区内有权限的PQR。
    """
    # Get workspace context
    workspace_context = get_workspace_context(db, current_user, workspace_id)

    # Check permission
    if current_user.membership_type != "enterprise":
        if not user_service.has_permission(db, current_user.id, "pqr", "delete"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限"
            )

    # Get PQR with workspace filtering
    from app.services.pqr_service import PQRService
    pqr_service_instance = PQRService(db)
    pqr = pqr_service_instance.get(
        db,
        id=id,
        current_user=current_user,
        workspace_context=workspace_context
    )

    if not pqr:
        raise HTTPException(status_code=404, detail="PQR未找到")

    # 检查是否为所有者或管理员
    if pqr.user_id != current_user.id and not current_user.is_superuser:
        # For enterprise workspace, check if user is admin
        if workspace_context.workspace_type == WorkspaceType.ENTERPRISE:
            employee = db.query(CompanyEmployee).filter(
                CompanyEmployee.user_id == current_user.id,
                CompanyEmployee.company_id == workspace_context.company_id,
                CompanyEmployee.status == "active"
            ).first()

            if not employee or employee.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只能删除自己的PQR或需要管理员权限"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能删除自己的PQR"
            )

    try:
        pqr = pqr_service_instance.remove(db, id=id)
        
        # 更新配额使用情况
        from app.services.membership_service import MembershipService
        membership_service = MembershipService(db)
        user = db.query(User).filter(User.id == current_user.id).first()
        membership_service.update_quota_usage(user, "pqr", -1)
        
        return pqr
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/specimens/", response_model=PQRTestSpecimenResponse)
def create_pqr_specimen(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    specimen_in: PQRTestSpecimenCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """为PQR创建试样记录."""
    pqr = pqr_service.get(db, id=id)
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR未找到")

    # 设置PQR ID
    specimen_in.pqr_id = id

    try:
        specimen = pqr_service.create_specimen(db, obj_in=specimen_in)
        return specimen
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{id}/specimens/", response_model=List[PQRTestSpecimenResponse])
def read_pqr_specimens(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """获取PQR的试样记录."""
    pqr = pqr_service.get(db, id=id)
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR未找到")

    return pqr_service.get_specimens(db, pqr_id=id)


@router.put("/{id}/qualification/", response_model=PQRResponse)
def update_pqr_qualification(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    qualification_update: PQRQualificationUpdate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """更新PQR评定结果."""
    pqr = pqr_service.get(db, id=id)
    if not pqr:
        raise HTTPException(status_code=404, detail="PQR未找到")

    try:
        pqr = pqr_service.update_qualification(
            db, pqr_id=id, qualification_update=qualification_update
        )
        return pqr
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search", response_model=List[PQRSummary])
def search_pqr(
    *,
    db: Session = Depends(deps.get_db),
    search_params: PQRSearchParams,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """高级PQR搜索."""
    pqr_list = pqr_service.search_pqr(db, search_params=search_params.model_dump())

    # 转换为summary格式
    pqr_summaries = []
    for pqr in pqr_list:
        pqr_summaries.append(PQRSummary(
            id=pqr.id,
            title=pqr.title,
            pqr_number=pqr.pqr_number,
            wps_number=pqr.wps_number,
            test_date=pqr.test_date,
            company=pqr.company,
            welding_process=pqr.welding_process,
            base_material_spec=pqr.base_material_spec,
            qualification_result=pqr.qualification_result,
            created_at=pqr.created_at,
            updated_at=pqr.updated_at
        ))

    return pqr_summaries


@router.get("/statistics/overview", response_model=dict)
def get_pqr_statistics(
    db: Session = Depends(deps.get_db),
    owner_id: int = Query(None, description="所有者ID过滤"),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """获取PQR统计信息."""
    return pqr_service.get_pqr_statistics(db, owner_id=owner_id or current_user.id)


@router.get("/count/qualification", response_model=dict)
def get_pqr_count_by_qualification(
    db: Session = Depends(deps.get_db),
    owner_id: int = Query(None, description="所有者ID过滤"),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """按评定结果获取PQR数量."""
    return pqr_service.get_pqr_count(db, owner_id=owner_id or current_user.id)


@router.get("/statistics/heat-input", response_model=dict)
def get_pqr_heat_input_stats(
    db: Session = Depends(deps.get_db),
    owner_id: int = Query(None, description="所有者ID过滤"),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """获取PQR热输入统计信息."""
    return pqr_service.get_pqr_heat_input_stats(db, owner_id=owner_id or current_user.id)


@router.post("/{id}/duplicate", response_model=PQRResponse)
def duplicate_pqr(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
) -> Any:
    """复制PQR."""
    try:
        # 获取工作区上下文
        workspace_context = get_workspace_context(db, current_user, workspace_id)

        # 导入PQR服务
        from app.services.pqr_service import PQRService
        pqr_service_instance = PQRService(db)

        # 获取原始PQR
        original_pqr = pqr_service_instance.get(
            db,
            id=id,
            current_user=current_user,
            workspace_context=workspace_context
        )
        if not original_pqr:
            raise HTTPException(status_code=404, detail="PQR未找到")

        # 创建副本数据
        from app.schemas.pqr import PQRCreate
        import time

        # 构建新的PQR数据
        pqr_dict = {
            "title": f"{original_pqr.title} (副本)",
            "pqr_number": f"{original_pqr.pqr_number}-COPY-{int(time.time())}",
            "test_date": original_pqr.test_date,
            "qualification_result": "pending",  # 副本默认为待评定
            "template_id": original_pqr.template_id,
            "modules_data": original_pqr.modules_data,
            "wps_number": original_pqr.wps_number,
            "company": original_pqr.company,
            "project_name": original_pqr.project_name,
            "test_location": original_pqr.test_location,
            "welding_operator": original_pqr.welding_operator,
            "welding_process": original_pqr.welding_process,
            "base_material_spec": original_pqr.base_material_spec,
            "filler_material_spec": original_pqr.filler_material_spec,
            "shielding_gas": original_pqr.shielding_gas,
        }

        # 创建新PQR
        pqr_create = PQRCreate(**pqr_dict)
        new_pqr = pqr_service_instance.create(
            db,
            obj_in=pqr_create,
            current_user=current_user,
            workspace_context=workspace_context
        )

        return new_pqr
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: 复制PQR失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"复制PQR失败: {str(e)}")


@router.get("/{id}/export/pdf")
def export_pqr_pdf(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """导出PQR为PDF."""
    try:
        from fastapi.responses import StreamingResponse
        import io

        # 获取PQR
        pqr = pqr_service.get(db, id=id)
        if not pqr:
            raise HTTPException(status_code=404, detail="PQR未找到")

        # TODO: 实现实际的PDF生成逻辑
        # 这里暂时返回一个简单的文本文件作为示例
        content = f"""PQR导出

PQR编号: {pqr.pqr_number}
标题: {pqr.title}
试验日期: {pqr.test_date}
评定结果: {pqr.qualification_result}
焊接工艺: {pqr.welding_process}
母材规格: {pqr.base_material_spec}

注意：这是一个临时实现，实际应该生成PDF文件。
"""

        # 创建字节流
        buffer = io.BytesIO(content.encode('utf-8'))
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={pqr.pqr_number}.pdf"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: 导出PDF失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出PDF失败: {str(e)}")


@router.get("/{id}/export/excel")
def export_pqr_excel(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """导出PQR为Excel."""
    try:
        from fastapi.responses import StreamingResponse
        import io

        # 获取PQR
        pqr = pqr_service.get(db, id=id)
        if not pqr:
            raise HTTPException(status_code=404, detail="PQR未找到")

        # TODO: 实现实际的Excel生成逻辑
        # 这里暂时返回一个简单的CSV文件作为示例
        content = f"""PQR编号,标题,试验日期,评定结果,焊接工艺,母材规格
{pqr.pqr_number},{pqr.title},{pqr.test_date},{pqr.qualification_result},{pqr.welding_process},{pqr.base_material_spec}
"""

        # 创建字节流
        buffer = io.BytesIO(content.encode('utf-8-sig'))  # 使用utf-8-sig以支持Excel中文显示
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={pqr.pqr_number}.xlsx"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: 导出Excel失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出Excel失败: {str(e)}")


@router.post("/export", response_model=dict)
def export_pqr(
    *,
    db: Session = Depends(deps.get_db),
    export_request: PQRExportRequest,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """导出PQR."""
    # 这里应该实现实际的导出逻辑
    # 目前只返回一个模拟的响应
    return {
        "message": f"导出请求已接收，将导出 {len(export_request.pqr_ids)} 个PQR文件",
        "format": export_request.export_format,
        "include_specimens": export_request.include_specimens,
        "include_attachments": export_request.include_attachments
    }
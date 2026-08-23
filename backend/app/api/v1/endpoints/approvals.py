"""
Approval workflow API endpoints.
审批工作流API端点
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_active_user
from app.core.data_access import DataAccessAction, WorkspaceContext, WorkspaceType
from app.core.document_access import require_document_access
from app.models.company import CompanyEmployee
from app.models.ppqr import PPQR
from app.models.pqr import PQR
from app.models.wps import WPS
from app.services.approval_service import ApprovalService
from app.services.workspace_service import WorkspaceService
from app.schemas.approval import (
    SubmitForApprovalRequest,
    ApprovalActionRequest,
    BatchApprovalRequest,
    ApprovalInstanceResponse,
    ApprovalHistoryResponse,
    ApprovalStatistics,
    ApprovalDetailResponse,
    WorkflowDefinitionCreate,
    WorkflowDefinitionResponse,
)

router = APIRouter()


def _approval_snapshot(document: Any) -> Dict[str, Any]:
    return jsonable_encoder(
        {
            column.name: getattr(document, column.name)
            for column in document.__table__.columns
            if column.name not in {"status", "updated_at"}
        }
    )


def get_workspace_context(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
) -> WorkspaceContext:
    """
    Get workspace context from header or user's default workspace.

    Args:
        db: Database session
        current_user: Current user
        x_workspace_id: Workspace ID from header (optional)

    Returns:
        WorkspaceContext object
    """
    workspace_service = WorkspaceService(db)

    # If workspace_id is provided in header, use it
    if x_workspace_id:
        try:
            context = workspace_service.create_workspace_context(
                current_user, x_workspace_id
            )
            return context
        except Exception:
            raise

    # Otherwise, determine default workspace based on user's membership type
    if current_user.membership_type == "enterprise":
        # For enterprise users, find their company
        employee = (
            db.query(CompanyEmployee)
            .filter(
                CompanyEmployee.user_id == current_user.id,
                CompanyEmployee.status == "active",
            )
            .first()
        )

        if employee:
            return WorkspaceContext(
                user_id=current_user.id,
                workspace_type=WorkspaceType.ENTERPRISE,
                company_id=employee.company_id,
                factory_id=employee.factory_id,
            )
    # Default to personal workspace
    return WorkspaceContext(
        user_id=current_user.id, workspace_type=WorkspaceType.PERSONAL
    )


# ==================== 提交审批 ====================


@router.post("/submit")
def submit_for_approval(
    request: SubmitForApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """
    提交文档审批
    支持单个或批量提交
    """
    approval_service = ApprovalService(db)

    model_by_type = {"wps": WPS, "pqr": PQR, "ppqr": PPQR}
    model = model_by_type.get(request.document_type)
    if model is None:
        raise HTTPException(status_code=422, detail="该审批类型需由对应版本模块提交")
    documents = {
        document_id: require_document_access(
            db,
            model,
            document_id,
            current_user,
            f"{request.document_type.upper()}不存在",
            action=DataAccessAction.EDIT,
        )
        for document_id in request.document_ids
    }

    if len(request.document_ids) == 1:
        # 单个提交
        # 根据document_type查询文档信息
        document_number = f"{request.document_type.upper()}-{request.document_ids[0]}"
        document_title = f"Document {request.document_ids[0]}"

        document = documents[request.document_ids[0]]
        document_number = getattr(
            document, f"{request.document_type}_number", document_number
        )
        document_title = document.title

        instance = approval_service.submit_for_approval(
            document_type=request.document_type,
            document_id=request.document_ids[0],
            document_number=document_number,
            document_title=document_title,
            current_user=current_user,
            workspace_context=workspace_context,
            notes=request.notes,
            workflow_id=request.workflow_id,
            version_snapshot=_approval_snapshot(document),
            version_key=str(
                getattr(document, "version", None)
                or getattr(document, "updated_at", None)
                or document.id
            ),
        )

        # 将 ORM 对象转换为 Pydantic schema
        from app.schemas.approval import ApprovalInstanceResponse

        instance_data = ApprovalInstanceResponse.model_validate(instance)

        return {"success": True, "message": "提交审批成功", "data": instance_data}
    else:
        # 批量提交
        instances = approval_service.batch_submit_for_approval(
            document_type=request.document_type,
            document_ids=request.document_ids,
            current_user=current_user,
            workspace_context=workspace_context,
            notes=request.notes,
            version_snapshots={
                document_id: _approval_snapshot(document)
                for document_id, document in documents.items()
            },
        )

        # 将 ORM 对象列表转换为 Pydantic schema 列表
        from app.schemas.approval import ApprovalInstanceResponse

        instances_data = [
            ApprovalInstanceResponse.model_validate(inst) for inst in instances
        ]

        return {
            "success": True,
            "message": f"成功提交 {len(instances)} 个文档审批",
            "data": instances_data,
        }


# ==================== 审批操作 ====================


@router.post("/{instance_id}/approve")
def approve_document(
    instance_id: int,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """批准文档"""
    approval_service = ApprovalService(db)

    instance = approval_service.approve_document(
        instance_id=instance_id,
        current_user=current_user,
        comment=request.comment,
        attachments=request.attachments,
    )

    # 转换为 Pydantic schema
    instance_data = ApprovalInstanceResponse.model_validate(instance)

    return {"success": True, "message": "审批通过", "data": instance_data}


@router.post("/{instance_id}/reject")
def reject_document(
    instance_id: int,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """拒绝文档"""
    approval_service = ApprovalService(db)

    instance = approval_service.reject_document(
        instance_id=instance_id,
        current_user=current_user,
        comment=request.comment,
        attachments=request.attachments,
    )

    # 转换为 Pydantic schema
    instance_data = ApprovalInstanceResponse.model_validate(instance)

    return {"success": True, "message": "审批拒绝", "data": instance_data}


@router.post("/{instance_id}/return")
def return_document(
    instance_id: int,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """退回文档"""
    approval_service = ApprovalService(db)

    instance = approval_service.return_document(
        instance_id=instance_id,
        current_user=current_user,
        comment=request.comment,
        attachments=request.attachments,
    )

    # 转换为 Pydantic schema
    instance_data = ApprovalInstanceResponse.model_validate(instance)

    return {"success": True, "message": "文档已退回", "data": instance_data}


@router.post("/{instance_id}/cancel")
def cancel_approval(
    instance_id: int,
    comment: str = Query("", description="取消原因（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """取消审批（仅提交人可操作）"""
    approval_service = ApprovalService(db)

    instance = approval_service.cancel_approval(
        instance_id=instance_id,
        current_user=current_user,
        comment=comment if comment else None,
    )

    # 转换为 Pydantic schema
    instance_data = ApprovalInstanceResponse.model_validate(instance)

    return {"success": True, "message": "审批已取消", "data": instance_data}


# ==================== 批量操作 ====================


@router.post("/batch/approve")
def batch_approve(
    request: BatchApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """批量批准"""
    approval_service = ApprovalService(db)

    approved, errors = approval_service.batch_approve(
        instance_ids=request.instance_ids,
        current_user=current_user,
        comment=request.comment,
    )

    return {
        "success": True,
        "message": f"成功批准 {len(approved)} 个，失败 {len(errors)} 个",
        "data": {"approved": approved, "errors": errors},
    }


@router.post("/batch/reject")
def batch_reject(
    request: BatchApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """批量拒绝"""
    approval_service = ApprovalService(db)

    rejected, errors = approval_service.batch_reject(
        instance_ids=request.instance_ids,
        current_user=current_user,
        comment=request.comment,
    )

    return {
        "success": True,
        "message": f"成功拒绝 {len(rejected)} 个，失败 {len(errors)} 个",
        "data": {"rejected": rejected, "errors": errors},
    }


# ==================== 查询接口 ====================


@router.get("/pending")
def get_pending_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """获取待我审批的列表"""
    approval_service = ApprovalService(db)

    instances, total = approval_service.get_pending_approvals(
        current_user=current_user,
        workspace_context=workspace_context,
        page=page,
        page_size=page_size,
    )

    # 将SQLAlchemy对象转换为字典列表
    items_data = [
        ApprovalInstanceResponse.model_validate(instance).model_dump()
        for instance in instances
    ]

    return {
        "success": True,
        "data": {
            "items": items_data,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/my-submissions")
def get_my_submissions(
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """获取我提交的审批列表"""
    approval_service = ApprovalService(db)

    instances, total = approval_service.get_my_submissions(
        current_user=current_user,
        workspace_context=workspace_context,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )

    # 将SQLAlchemy对象转换为字典列表
    items_data = [
        ApprovalInstanceResponse.model_validate(instance).model_dump()
        for instance in instances
    ]

    return {
        "success": True,
        "data": {
            "items": items_data,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{instance_id}/history")
def get_approval_history(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取审批历史"""
    approval_service = ApprovalService(db)

    history = approval_service.get_approval_history(instance_id)

    # 将SQLAlchemy对象转换为字典列表
    history_data = []
    for item in history:
        history_data.append(
            {
                "id": item.id,
                "instance_id": item.instance_id,
                "step_number": item.step_number,
                "step_name": item.step_name,
                "action": item.action,
                "operator_id": item.operator_id,
                "operator_name": item.operator_name,
                "operator_role": item.operator_role,
                "comment": item.comment,
                "attachments": item.attachments or [],
                "result": item.result,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "ip_address": item.ip_address,
            }
        )

    return {"success": True, "data": history_data}


@router.get("/statistics")
def get_approval_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """获取审批统计信息"""
    approval_service = ApprovalService(db)

    stats = approval_service.get_approval_statistics(
        current_user=current_user, workspace_context=workspace_context
    )

    return {"success": True, "data": stats}


# ==================== 工作流管理 ====================
# 注意: 必须放在 /{instance_id} 路由之前,避免路由冲突


@router.get("/workflows", response_model=None)
def get_workflows(
    document_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """获取工作流列表"""
    from app.models.approval import ApprovalWorkflowDefinition

    print(f"[获取工作流列表] 用户ID: {current_user.id}")
    print(f"[获取工作流列表] 工作区类型: {workspace_context.workspace_type}")
    print(f"[获取工作流列表] 企业ID: {workspace_context.company_id}")

    query = db.query(ApprovalWorkflowDefinition)

    # 只显示系统工作流和当前企业的工作流
    if workspace_context.workspace_type == "enterprise":
        # 企业工作区：显示系统工作流(company_id IS NULL) 和 当前企业的工作流
        query = query.filter(
            (ApprovalWorkflowDefinition.company_id.is_(None))
            | (ApprovalWorkflowDefinition.company_id == workspace_context.company_id)
        )
    else:
        # 个人工作区只显示系统工作流
        query = query.filter(ApprovalWorkflowDefinition.company_id.is_(None))

    # 按文档类型筛选
    if document_type:
        query = query.filter(ApprovalWorkflowDefinition.document_type == document_type)

    # 按状态筛选
    if is_active is not None:
        query = query.filter(ApprovalWorkflowDefinition.is_active == is_active)

    # 分页
    total = query.count()
    workflows = query.offset((page - 1) * page_size).limit(page_size).all()

    print(f"[获取工作流列表] 查询到 {len(workflows)} 个工作流")

    # 将ORM对象转换为字典,避免序列化问题
    workflow_list = []
    for wf in workflows:
        workflow_dict = {
            "id": wf.id,
            "name": wf.name,
            "code": wf.code,
            "description": wf.description,
            "document_type": wf.document_type,
            "company_id": wf.company_id,
            "factory_id": wf.factory_id,
            "steps": wf.steps,
            "is_active": wf.is_active,
            "is_default": wf.is_default,
            "created_at": wf.created_at.isoformat() if wf.created_at else None,
            "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
            "created_by": wf.created_by,
            "updated_by": wf.updated_by,
        }
        workflow_list.append(workflow_dict)

    return {
        "success": True,
        "data": {
            "items": workflow_list,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/workflows/{workflow_id}", response_model=None)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取工作流详情"""
    from app.models.approval import ApprovalWorkflowDefinition

    workflow = (
        db.query(ApprovalWorkflowDefinition)
        .filter(ApprovalWorkflowDefinition.id == workflow_id)
        .first()
    )

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工作流不存在")

    # 将ORM对象转换为字典
    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "code": workflow.code,
        "description": workflow.description,
        "document_type": workflow.document_type,
        "company_id": workflow.company_id,
        "factory_id": workflow.factory_id,
        "steps": workflow.steps,
        "is_active": workflow.is_active,
        "is_default": workflow.is_default,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        "created_by": workflow.created_by,
        "updated_by": workflow.updated_by,
    }

    return {"success": True, "data": workflow_dict}


@router.post("/workflows", response_model=None)
def create_workflow(
    request: WorkflowDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """创建工作流"""
    from app.models.approval import ApprovalWorkflowDefinition

    # 调试日志
    print(f"[创建工作流] 用户ID: {current_user.id}, 用户邮箱: {current_user.email}")
    print(f"[创建工作流] 用户会员类型: {current_user.membership_type}")
    print(f"[创建工作流] 工作区类型: {workspace_context.workspace_type}")
    print(f"[创建工作流] 企业ID: {workspace_context.company_id}")
    print(f"[创建工作流] 工作流名称: {request.name}")
    print(f"[创建工作流] 工作流代码: {request.code}")

    # 只有企业用户可以创建自定义工作流
    if workspace_context.workspace_type != "enterprise":
        print(
            f"[创建工作流] 权限检查失败: workspace_type={workspace_context.workspace_type}, 期望=enterprise"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"只有企业用户可以创建自定义工作流(当前工作区类型: {workspace_context.workspace_type})",
        )

    # 检查工作流代码是否已存在
    existing = (
        db.query(ApprovalWorkflowDefinition)
        .filter(
            ApprovalWorkflowDefinition.code == request.code,
            ApprovalWorkflowDefinition.company_id == workspace_context.company_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="工作流代码已存在")

    # 创建工作流
    workflow = ApprovalWorkflowDefinition(
        name=request.name,
        code=request.code,
        document_type=request.document_type,
        description=request.description,
        steps=request.steps,
        is_active=request.is_active if request.is_active is not None else True,
        is_default=False,
        company_id=workspace_context.company_id,
        created_by=current_user.id,
    )

    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    print(f"[创建工作流] 工作流创建成功: ID={workflow.id}, 名称={workflow.name}")

    # 将ORM对象转换为字典
    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "code": workflow.code,
        "description": workflow.description,
        "document_type": workflow.document_type,
        "company_id": workflow.company_id,
        "factory_id": workflow.factory_id,
        "steps": workflow.steps,
        "is_active": workflow.is_active,
        "is_default": workflow.is_default,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        "created_by": workflow.created_by,
        "updated_by": workflow.updated_by,
    }

    return {"success": True, "message": "工作流创建成功", "data": workflow_dict}


@router.put("/workflows/{workflow_id}", response_model=None)
def update_workflow(
    workflow_id: int,
    request: WorkflowDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """更新工作流"""
    from app.models.approval import ApprovalWorkflowDefinition

    print(f"[更新工作流] workflow_id={workflow_id}")
    print(f"[更新工作流] 用户ID={current_user.id}, 企业ID={workspace_context.company_id}")

    workflow = (
        db.query(ApprovalWorkflowDefinition)
        .filter(ApprovalWorkflowDefinition.id == workflow_id)
        .first()
    )

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工作流不存在")

    print(
        f"[更新工作流] 工作流: id={workflow.id}, name={workflow.name}, company_id={workflow.company_id}"
    )

    # 不能修改系统工作流
    if workflow.company_id is None:
        print(f"[更新工作流] 不能修改系统工作流")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能修改系统工作流")

    # 只能修改自己企业的工作流
    if workflow.company_id != workspace_context.company_id:
        print(
            f"[更新工作流] 无权修改此工作流: workflow.company_id={workflow.company_id}, workspace.company_id={workspace_context.company_id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此工作流")

    # 更新工作流
    workflow.name = request.name
    workflow.code = request.code
    workflow.document_type = request.document_type
    workflow.description = request.description
    workflow.steps = request.steps
    if request.is_active is not None:
        workflow.is_active = request.is_active
    workflow.updated_by = current_user.id

    db.commit()
    db.refresh(workflow)

    # 将ORM对象转换为字典
    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "code": workflow.code,
        "description": workflow.description,
        "document_type": workflow.document_type,
        "company_id": workflow.company_id,
        "factory_id": workflow.factory_id,
        "steps": workflow.steps,
        "is_active": workflow.is_active,
        "is_default": workflow.is_default,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        "created_by": workflow.created_by,
        "updated_by": workflow.updated_by,
    }

    return {"success": True, "message": "工作流更新成功", "data": workflow_dict}


@router.delete("/workflows/{workflow_id}")
def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """删除工作流(仅限企业自定义工作流)"""
    from app.models.approval import ApprovalWorkflowDefinition

    print(f"[删除工作流] workflow_id={workflow_id}")
    print(f"[删除工作流] 用户ID={current_user.id}, 企业ID={workspace_context.company_id}")

    workflow = (
        db.query(ApprovalWorkflowDefinition)
        .filter(ApprovalWorkflowDefinition.id == workflow_id)
        .first()
    )

    if not workflow:
        print(f"[删除工作流] 工作流不存在")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工作流不存在")

    print(
        f"[删除工作流] 工作流: id={workflow.id}, name={workflow.name}, is_default={workflow.is_default}, company_id={workflow.company_id}"
    )

    # 不能删除系统默认工作流
    if workflow.company_id is None:
        print(f"[删除工作流] 不能删除系统默认工作流")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能删除系统默认工作流")

    # 不能删除默认工作流
    if workflow.is_default:
        print(f"[删除工作流] 不能删除默认工作流")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="不能删除默认工作流,请先设置其他工作流为默认"
        )

    # 只能删除自己企业的工作流
    if workflow.company_id != workspace_context.company_id:
        print(f"[删除工作流] 无权删除此工作流")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此工作流")

    print(f"[删除工作流] 开始删除...")
    db.delete(workflow)
    db.commit()
    print(f"[删除工作流] 删除成功")

    return {"success": True, "message": "工作流删除成功"}


@router.patch("/workflows/{workflow_id}/set-default")
def set_default_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """设置为默认工作流"""
    from app.models.approval import ApprovalWorkflowDefinition

    print(f"[设置默认工作流] workflow_id={workflow_id}")
    print(f"[设置默认工作流] 用户ID={current_user.id}, 企业ID={workspace_context.company_id}")

    workflow = (
        db.query(ApprovalWorkflowDefinition)
        .filter(ApprovalWorkflowDefinition.id == workflow_id)
        .first()
    )

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工作流不存在")

    print(
        f"[设置默认工作流] 工作流: id={workflow.id}, name={workflow.name}, document_type={workflow.document_type}, company_id={workflow.company_id}"
    )

    # 只能修改自己企业的工作流
    if workflow.company_id != workspace_context.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此工作流")

    # 取消同一文档类型、同一企业的其他工作流的默认状态，并禁用它们
    print(f"[设置默认工作流] 禁用同一文档类型的其他工作流")
    db.query(ApprovalWorkflowDefinition).filter(
        ApprovalWorkflowDefinition.company_id == workspace_context.company_id,
        ApprovalWorkflowDefinition.document_type == workflow.document_type,
        ApprovalWorkflowDefinition.id != workflow_id,
    ).update(
        {"is_default": False, "is_active": False}  # 禁用其他工作流
    )

    # 设置当前工作流为默认并启用
    print(f"[设置默认工作流] 设置工作流为默认并启用")
    workflow.is_default = True
    workflow.is_active = True  # 自动启用
    workflow.updated_by = current_user.id

    db.commit()
    db.refresh(workflow)

    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "code": workflow.code,
        "description": workflow.description,
        "document_type": workflow.document_type,
        "company_id": workflow.company_id,
        "factory_id": workflow.factory_id,
        "steps": workflow.steps,
        "is_active": workflow.is_active,
        "is_default": workflow.is_default,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        "created_by": workflow.created_by,
        "updated_by": workflow.updated_by,
    }

    return {"success": True, "message": "已设置为默认工作流", "data": workflow_dict}


@router.patch("/workflows/{workflow_id}/toggle")
def toggle_workflow_status(
    workflow_id: int,
    is_active: bool = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    workspace_context: WorkspaceContext = Depends(get_workspace_context),
) -> Any:
    """切换工作流状态(仅限企业自定义工作流)"""
    from app.models.approval import ApprovalWorkflowDefinition

    print(f"[切换工作流状态] workflow_id={workflow_id}, is_active={is_active}")
    print(f"[切换工作流状态] 用户ID={current_user.id}, 企业ID={workspace_context.company_id}")

    workflow = (
        db.query(ApprovalWorkflowDefinition)
        .filter(ApprovalWorkflowDefinition.id == workflow_id)
        .first()
    )

    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工作流不存在")

    print(
        f"[切换工作流状态] 工作流: id={workflow.id}, name={workflow.name}, is_default={workflow.is_default}, company_id={workflow.company_id}"
    )

    # 不能修改系统默认工作流
    if workflow.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统默认工作流不能修改,请创建企业自定义工作流来覆盖系统默认设置",
        )

    # 只能修改自己企业的工作流
    if workflow.company_id != workspace_context.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此工作流")

    workflow.is_active = is_active
    workflow.updated_by = current_user.id

    db.commit()
    db.refresh(workflow)

    # 将ORM对象转换为字典
    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "code": workflow.code,
        "description": workflow.description,
        "document_type": workflow.document_type,
        "company_id": workflow.company_id,
        "factory_id": workflow.factory_id,
        "steps": workflow.steps,
        "is_active": workflow.is_active,
        "is_default": workflow.is_default,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        "created_by": workflow.created_by,
        "updated_by": workflow.updated_by,
    }

    return {
        "success": True,
        "message": f"工作流已{'启用' if is_active else '停用'}",
        "data": workflow_dict,
    }


# ==================== 审批实例详情 ====================
# 注意: 这个路由必须放在最后,因为 /{instance_id} 会匹配任何路径


@router.get("/{instance_id}")
def get_approval_detail(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取审批详情"""
    from app.models.approval import ApprovalInstance

    approval_service = ApprovalService(db)

    instance = (
        db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
    )

    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审批实例不存在")

    # 获取审批历史
    history = approval_service.get_approval_history(instance_id)

    # 检查权限
    can_approve = approval_service._can_approve(instance, current_user)
    can_cancel = instance.submitter_id == current_user.id

    # 将SQLAlchemy对象转换为字典
    instance_data = ApprovalInstanceResponse.model_validate(instance).model_dump()

    # 将审批历史转换为字典列表
    history_data = []
    for item in history:
        history_data.append(
            {
                "id": item.id,
                "instance_id": item.instance_id,
                "step_number": item.step_number,
                "step_name": item.step_name,
                "action": item.action,
                "operator_id": item.operator_id,
                "operator_name": item.operator_name,
                "operator_role": item.operator_role,
                "comment": item.comment,
                "attachments": item.attachments or [],
                "result": item.result,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "ip_address": item.ip_address,
            }
        )

    return {
        "success": True,
        "data": {
            "instance": instance_data,
            "history": history_data,
            "permissions": {"can_approve": can_approve, "can_cancel": can_cancel},
        },
    }

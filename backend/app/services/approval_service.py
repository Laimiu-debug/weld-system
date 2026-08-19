"""
Approval workflow service for the welding system backend.
审批工作流服务
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.approval import (
    ApprovalWorkflowDefinition,
    ApprovalInstance,
    ApprovalHistory,
    ApprovalNotification,
    ApprovalStatus,
    ApprovalAction,
    DocumentType
)
from app.models.user import User
from app.models.company import CompanyRole, CompanyEmployee
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.schemas.approval import (
    WorkflowDefinitionCreate,
    ApprovalInstanceCreate,
    ApprovalHistoryCreate,
    ApprovalNotificationCreate
)
from app.services.notification_service import NotificationService


class ApprovalService:
    """审批服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    # ==================== 工作流定义管理 ====================
    
    def get_workflow_for_document(
        self,
        document_type: str,
        workspace_context: WorkspaceContext
    ) -> Optional[ApprovalWorkflowDefinition]:
        """
        获取文档类型对应的工作流定义
        优先级：企业自定义 > 系统默认
        """
        # 如果是个人工作区，不需要审批流程
        if workspace_context.is_personal():
            return None
        
        # 企业工作区：查找企业自定义工作流
        if workspace_context.company_id:
            workflow = self.db.query(ApprovalWorkflowDefinition).filter(
                ApprovalWorkflowDefinition.document_type == document_type,
                ApprovalWorkflowDefinition.company_id == workspace_context.company_id,
                ApprovalWorkflowDefinition.is_active == True
            ).order_by(
                ApprovalWorkflowDefinition.is_default.desc(),
                ApprovalWorkflowDefinition.created_at.desc()
            ).first()
            
            if workflow:
                return workflow
        
        # 查找系统默认工作流
        workflow = self.db.query(ApprovalWorkflowDefinition).filter(
            ApprovalWorkflowDefinition.document_type == document_type,
            ApprovalWorkflowDefinition.company_id.is_(None),
            ApprovalWorkflowDefinition.is_active == True,
            ApprovalWorkflowDefinition.is_default == True
        ).first()
        
        return workflow
    
    def create_workflow_definition(
        self,
        workflow_data: WorkflowDefinitionCreate,
        current_user: User
    ) -> ApprovalWorkflowDefinition:
        """创建工作流定义"""
        workflow = ApprovalWorkflowDefinition(
            name=workflow_data.name,
            code=workflow_data.code,
            description=workflow_data.description,
            document_type=workflow_data.document_type,
            company_id=workflow_data.company_id,
            factory_id=workflow_data.factory_id,
            steps=workflow_data.steps,
            is_active=workflow_data.is_active,
            is_default=workflow_data.is_default,
            created_by=current_user.id
        )
        
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        
        return workflow
    
    # ==================== 审批实例管理 ====================
    
    def should_require_approval(
        self,
        document_type: str,
        workspace_context: WorkspaceContext
    ) -> bool:
        """
        判断是否需要审批
        个人工作区：不需要审批
        企业工作区：需要审批
        """
        # 个人工作区不需要审批
        if workspace_context.is_personal():
            return False
        
        # 企业工作区需要审批
        if workspace_context.is_enterprise():
            # 检查是否有对应的工作流
            workflow = self.get_workflow_for_document(document_type, workspace_context)
            return workflow is not None
        
        return False
    
    def submit_for_approval(
        self,
        document_type: str,
        document_id: int,
        document_number: str,
        document_title: str,
        current_user: User,
        workspace_context: WorkspaceContext,
        notes: Optional[str] = None,
        priority: str = "normal",
        workflow_id: Optional[int] = None
    ) -> ApprovalInstance:
        """
        提交文档审批

        Args:
            workflow_id: 指定的工作流ID,如果为None则使用默认工作流
        """
        # 检查是否需要审批
        if not self.should_require_approval(document_type, workspace_context):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该工作区不需要审批流程"
            )

        # 获取工作流定义
        if workflow_id:
            # 使用指定的工作流
            workflow = self.db.query(ApprovalWorkflowDefinition).filter(
                ApprovalWorkflowDefinition.id == workflow_id,
                ApprovalWorkflowDefinition.document_type == document_type,
                ApprovalWorkflowDefinition.is_active == True
            ).first()
            if not workflow:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的工作流不存在或已停用"
                )
            # 验证权限
            if workflow.company_id and workflow.company_id != workspace_context.company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权使用此工作流"
                )
        else:
            # 使用默认工作流
            workflow = self.get_workflow_for_document(document_type, workspace_context)
            if not workflow:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"未找到{document_type}的审批工作流"
                )
        
        # 检查是否已有待审批的实例
        existing_instance = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.document_type == document_type,
            ApprovalInstance.document_id == document_id,
            ApprovalInstance.status.in_([
                ApprovalStatus.PENDING,
                ApprovalStatus.IN_PROGRESS
            ])
        ).first()
        
        if existing_instance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该文档已有待审批的流程"
            )
        
        # 创建审批实例
        instance = ApprovalInstance(
            workflow_id=workflow.id,
            document_type=document_type,
            document_id=document_id,
            document_number=document_number,
            document_title=document_title,
            workspace_type=workspace_context.workspace_type,
            company_id=workspace_context.company_id,
            factory_id=workspace_context.factory_id,
            status=ApprovalStatus.PENDING,
            current_step=1,
            current_step_name=workflow.steps[0]['step_name'] if workflow.steps else None,
            submitter_id=current_user.id,
            submitted_at=datetime.utcnow(),
            priority=priority,
            notes=notes
        )
        
        self.db.add(instance)
        self.db.flush()
        
        # 记录提交历史
        self._add_history(
            instance_id=instance.id,
            step_number=0,
            step_name="提交审批",
            action=ApprovalAction.SUBMIT,
            operator_id=current_user.id,
            operator_name=current_user.username or current_user.email,
            comment=notes or "提交审批申请"
        )
        
        # 发送通知给审批人
        self._notify_approvers(instance, workflow.steps[0] if workflow.steps else None)
        
        self.db.commit()
        self.db.refresh(instance)
        
        return instance
    
    def approve_document(
        self,
        instance_id: int,
        current_user: User,
        comment: str,
        attachments: List[str] = []
    ) -> ApprovalInstance:
        """批准文档"""
        return self._process_approval(
            instance_id=instance_id,
            current_user=current_user,
            action=ApprovalAction.APPROVE,
            comment=comment,
            attachments=attachments
        )
    
    def reject_document(
        self,
        instance_id: int,
        current_user: User,
        comment: str,
        attachments: List[str] = []
    ) -> ApprovalInstance:
        """拒绝文档"""
        return self._process_approval(
            instance_id=instance_id,
            current_user=current_user,
            action=ApprovalAction.REJECT,
            comment=comment,
            attachments=attachments
        )
    
    def return_document(
        self,
        instance_id: int,
        current_user: User,
        comment: str,
        attachments: List[str] = []
    ) -> ApprovalInstance:
        """退回文档"""
        return self._process_approval(
            instance_id=instance_id,
            current_user=current_user,
            action=ApprovalAction.RETURN,
            comment=comment,
            attachments=attachments
        )
    
    def cancel_approval(
        self,
        instance_id: int,
        current_user: User,
        comment: str
    ) -> ApprovalInstance:
        """取消审批（仅提交人可操作）"""
        instance = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.id == instance_id
        ).first()
        
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="审批实例不存在"
            )
        
        # 检查权限：只有提交人可以取消
        if instance.submitter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有提交人可以取消审批"
            )
        
        # 检查状态：只有待审批或审批中的可以取消
        if instance.status not in [ApprovalStatus.PENDING, ApprovalStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前状态不允许取消"
            )
        
        instance.status = ApprovalStatus.CANCELLED
        instance.updated_at = datetime.utcnow()
        
        # 记录历史
        self._add_history(
            instance_id=instance.id,
            step_number=instance.current_step,
            step_name=instance.current_step_name,
            action=ApprovalAction.CANCEL,
            operator_id=current_user.id,
            operator_name=current_user.username or current_user.email,
            comment=comment
        )
        
        self.db.commit()
        self.db.refresh(instance)

        return instance

    # ==================== 批量操作 ====================

    def batch_submit_for_approval(
        self,
        document_type: str,
        document_ids: List[int],
        current_user: User,
        workspace_context: WorkspaceContext,
        notes: Optional[str] = None
    ) -> List[ApprovalInstance]:
        """批量提交审批"""
        instances = []
        errors = []

        for doc_id in document_ids:
            try:
                # 这里需要根据document_type获取文档信息
                # 简化处理，实际应该查询对应的文档表
                instance = self.submit_for_approval(
                    document_type=document_type,
                    document_id=doc_id,
                    document_number=f"{document_type.upper()}-{doc_id}",
                    document_title=f"Document {doc_id}",
                    current_user=current_user,
                    workspace_context=workspace_context,
                    notes=notes
                )
                instances.append(instance)
            except Exception as e:
                errors.append({"document_id": doc_id, "error": str(e)})

        if errors:
            print(f"批量提交部分失败: {errors}")

        return instances

    def batch_approve(
        self,
        instance_ids: List[int],
        current_user: User,
        comment: str
    ) -> Tuple[List[ApprovalInstance], List[Dict]]:
        """批量批准"""
        approved = []
        errors = []

        for instance_id in instance_ids:
            try:
                instance = self.approve_document(
                    instance_id=instance_id,
                    current_user=current_user,
                    comment=comment
                )
                approved.append(instance)
            except Exception as e:
                errors.append({"instance_id": instance_id, "error": str(e)})

        return approved, errors

    def batch_reject(
        self,
        instance_ids: List[int],
        current_user: User,
        comment: str
    ) -> Tuple[List[ApprovalInstance], List[Dict]]:
        """批量拒绝"""
        rejected = []
        errors = []

        for instance_id in instance_ids:
            try:
                instance = self.reject_document(
                    instance_id=instance_id,
                    current_user=current_user,
                    comment=comment
                )
                rejected.append(instance)
            except Exception as e:
                errors.append({"instance_id": instance_id, "error": str(e)})

        return rejected, errors

    # ==================== 查询方法 ====================

    def get_pending_approvals(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ApprovalInstance], int]:
        """获取待我审批的列表"""
        # 获取用户的角色
        employee = self.db.query(CompanyEmployee).filter(
            CompanyEmployee.user_id == current_user.id,
            CompanyEmployee.company_id == workspace_context.company_id,
            CompanyEmployee.status == "active"
        ).first()

        if not employee or not employee.company_role_id:
            return [], 0

        # 查询待审批的实例
        query = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.company_id == workspace_context.company_id,
            ApprovalInstance.status.in_([
                ApprovalStatus.PENDING,
                ApprovalStatus.IN_PROGRESS
            ])
        )

        # TODO: 根据工作流步骤配置过滤出当前用户可以审批的
        # 这里需要检查workflow.steps中当前步骤的approver_ids是否包含当前用户的角色

        total = query.count()
        instances = query.order_by(
            ApprovalInstance.priority.desc(),
            ApprovalInstance.submitted_at.asc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return instances, total

    def get_my_submissions(
        self,
        current_user: User,
        workspace_context: WorkspaceContext,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ApprovalInstance], int]:
        """获取我提交的审批列表"""
        query = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.submitter_id == current_user.id
        )

        if workspace_context.company_id:
            query = query.filter(
                ApprovalInstance.company_id == workspace_context.company_id
            )

        if status_filter:
            query = query.filter(ApprovalInstance.status == status_filter)

        total = query.count()
        instances = query.order_by(
            ApprovalInstance.submitted_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return instances, total

    def get_approval_history(
        self,
        instance_id: int
    ) -> List[ApprovalHistory]:
        """获取审批历史"""
        return self.db.query(ApprovalHistory).filter(
            ApprovalHistory.instance_id == instance_id
        ).order_by(ApprovalHistory.created_at.asc()).all()

    def get_approval_statistics(
        self,
        current_user: User,
        workspace_context: WorkspaceContext
    ) -> Dict[str, int]:
        """获取审批统计信息"""
        stats = {
            "total_pending": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "my_pending": 0,
            "my_submitted": 0,
            "overdue": 0
        }

        if not workspace_context.company_id:
            return stats

        # 企业总体统计
        stats["total_pending"] = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.company_id == workspace_context.company_id,
            ApprovalInstance.status.in_([ApprovalStatus.PENDING, ApprovalStatus.IN_PROGRESS])
        ).count()

        stats["total_approved"] = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.company_id == workspace_context.company_id,
            ApprovalInstance.status == ApprovalStatus.APPROVED
        ).count()

        stats["total_rejected"] = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.company_id == workspace_context.company_id,
            ApprovalInstance.status == ApprovalStatus.REJECTED
        ).count()

        # 我提交的
        stats["my_submitted"] = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.submitter_id == current_user.id,
            ApprovalInstance.status.in_([ApprovalStatus.PENDING, ApprovalStatus.IN_PROGRESS])
        ).count()

        return stats

    # ==================== 私有辅助方法 ====================

    def _process_approval(
        self,
        instance_id: int,
        current_user: User,
        action: ApprovalAction,
        comment: str,
        attachments: List[str] = []
    ) -> ApprovalInstance:
        """处理审批操作的通用方法"""
        instance = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.id == instance_id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="审批实例不存在"
            )

        # 检查状态
        if instance.status not in [ApprovalStatus.PENDING, ApprovalStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前状态不允许审批"
            )

        # 检查权限：是否有审批权限
        if not self._can_approve(instance, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限审批此文档"
            )

        # 获取工作流定义
        workflow = self.db.query(ApprovalWorkflowDefinition).filter(
            ApprovalWorkflowDefinition.id == instance.workflow_id
        ).first()

        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流定义不存在"
            )

        # 记录审批历史
        self._add_history(
            instance_id=instance.id,
            step_number=instance.current_step,
            step_name=instance.current_step_name,
            action=action,
            operator_id=current_user.id,
            operator_name=current_user.username or current_user.email,
            comment=comment,
            attachments=attachments,
            result=action.value
        )

        # 根据操作类型更新状态
        if action == ApprovalAction.APPROVE:
            # 检查是否还有下一步
            if instance.current_step < len(workflow.steps):
                # 进入下一步
                instance.current_step += 1
                instance.current_step_name = workflow.steps[instance.current_step - 1]['step_name']
                instance.status = ApprovalStatus.IN_PROGRESS

                # 通知下一步审批人
                self._notify_approvers(instance, workflow.steps[instance.current_step - 1])
            else:
                # 所有步骤完成
                instance.status = ApprovalStatus.APPROVED
                instance.completed_at = datetime.utcnow()
                instance.final_approver_id = current_user.id

                # 更新文档状态为已批准
                self._update_document_status(instance, "approved")

                # 通知提交人
                self._notify_submitter(instance, "approved")

        elif action == ApprovalAction.REJECT:
            instance.status = ApprovalStatus.REJECTED
            instance.completed_at = datetime.utcnow()

            # 更新文档状态为已拒绝
            self._update_document_status(instance, "rejected")

            # 通知提交人
            self._notify_submitter(instance, "rejected")

        elif action == ApprovalAction.RETURN:
            instance.status = ApprovalStatus.RETURNED

            # 更新文档状态为草稿（退回后需要重新编辑）
            self._update_document_status(instance, "draft")

            # 通知提交人
            self._notify_submitter(instance, "returned")

        instance.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(instance)

        return instance

    def load_approver_permissions(self, user: User) -> Dict[int, Dict[str, Any]]:
        """一次性加载当前用户在各企业的角色权限，避免列表接口按行查询。"""
        rows = (
            self.db.query(CompanyEmployee, CompanyRole)
            .outerjoin(CompanyRole, CompanyRole.id == CompanyEmployee.company_role_id)
            .filter(
                CompanyEmployee.user_id == user.id,
                CompanyEmployee.status == "active",
            )
            .all()
        )
        permissions_by_company: Dict[int, Dict[str, Any]] = {}
        for employee, role in rows:
            permissions_by_company[employee.company_id] = (role.permissions or {}) if role else {}
        return permissions_by_company

    def _can_approve(
        self,
        instance: ApprovalInstance,
        user: User,
        permissions_by_company: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> bool:
        """检查用户是否有权限审批"""
        if user.is_admin:
            return True

        if permissions_by_company is None:
            permissions_by_company = self.load_approver_permissions(user)

        company_id = getattr(instance, "company_id", None)
        if company_id is None:
            return False

        permissions = permissions_by_company.get(company_id) or {}
        module_key = f"{instance.document_type}_management"
        module_perms = permissions.get(module_key, {}) or {}
        return bool(module_perms.get("approve", False))

    def _add_history(
        self,
        instance_id: int,
        step_number: int,
        step_name: str,
        action: ApprovalAction,
        operator_id: int,
        operator_name: str,
        comment: str,
        attachments: List[str] = [],
        result: Optional[str] = None
    ):
        """添加审批历史记录"""
        history = ApprovalHistory(
            instance_id=instance_id,
            step_number=step_number,
            step_name=step_name,
            action=action,
            operator_id=operator_id,
            operator_name=operator_name,
            comment=comment,
            attachments=attachments,
            result=result
        )

        self.db.add(history)
        self.db.flush()

    def _notify_approvers(self, instance: ApprovalInstance, step_config: Dict):
        """通知审批人"""
        if not step_config:
            return

        approver_type = step_config.get('approver_type')
        approver_ids = step_config.get('approver_ids', [])

        # 根据审批人类型获取实际的用户ID列表
        user_ids = []

        if approver_type == 'role':
            # 根据角色ID查找用户
            for role_id in approver_ids:
                employees = self.db.query(CompanyEmployee).filter(
                    CompanyEmployee.company_role_id == role_id,
                    CompanyEmployee.company_id == instance.company_id,
                    CompanyEmployee.status == "active"
                ).all()
                user_ids.extend([emp.user_id for emp in employees])

        elif approver_type == 'user':
            # 直接使用用户ID
            user_ids = approver_ids

        elif approver_type == 'department':
            # 根据部门ID查找用户
            for dept_id in approver_ids:
                employees = self.db.query(CompanyEmployee).filter(
                    CompanyEmployee.department_id == dept_id,
                    CompanyEmployee.company_id == instance.company_id,
                    CompanyEmployee.status == "active"
                ).all()
                user_ids.extend([emp.user_id for emp in employees])

        # 去重
        user_ids = list(set(user_ids))

        if user_ids:
            # 发送通知
            self.notification_service.notify_approval_submitted(
                submitter_id=instance.submitter_id,
                approver_ids=user_ids,
                document_type=instance.document_type,
                document_title=instance.document_title,
                instance_id=instance.id
            )

    def _notify_submitter(self, instance: ApprovalInstance, result: str):
        """通知提交人"""
        self.notification_service.notify_approval_result(
            submitter_id=instance.submitter_id,
            document_type=instance.document_type,
            document_title=instance.document_title,
            result=result,
            comment="",
            instance_id=instance.id
        )

    def _update_document_status(self, instance: ApprovalInstance, new_status: str):
        """更新文档状态"""
        # 根据文档类型更新对应的文档状态
        if instance.document_type == DocumentType.WPS:
            from app.models.wps import WPS
            document = self.db.query(WPS).filter(WPS.id == instance.document_id).first()
            if document:
                document.status = new_status
                document.updated_at = datetime.utcnow()

        elif instance.document_type == DocumentType.PQR:
            from app.models.pqr import PQR
            document = self.db.query(PQR).filter(PQR.id == instance.document_id).first()
            if document:
                document.status = new_status
                document.updated_at = datetime.utcnow()

        elif instance.document_type == DocumentType.PPQR:
            from app.models.ppqr import PPQR
            document = self.db.query(PPQR).filter(PPQR.id == instance.document_id).first()
            if document:
                document.status = new_status
                document.updated_at = datetime.utcnow()


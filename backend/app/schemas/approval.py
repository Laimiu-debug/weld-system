"""
Approval workflow schemas for the welding system backend.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ==================== 工作流定义 Schemas ====================


class ApprovalStepConfig(BaseModel):
    """审批步骤配置"""

    step_number: int = Field(..., description="步骤编号")
    step_name: str = Field(..., description="步骤名称")
    approver_type: str = Field(..., description="审批人类型: role, user, department")
    approver_ids: List[int] = Field(default=[], description="审批人ID列表")
    approval_mode: str = Field(default="any", description="审批模式: any, all, sequential")
    time_limit_hours: Optional[int] = Field(None, description="时限（小时）")
    is_required: bool = Field(default=True, description="是否必需")
    can_skip: bool = Field(default=False, description="是否可跳过")


class WorkflowDefinitionBase(BaseModel):
    """工作流定义基础Schema"""

    name: str = Field(..., description="工作流名称")
    code: str = Field(..., description="工作流代码")
    description: Optional[str] = Field(None, description="描述")
    document_type: str = Field(..., description="文档类型")
    company_id: Optional[int] = Field(None, description="企业ID")
    factory_id: Optional[int] = Field(None, description="工厂ID")
    steps: List[Dict[str, Any]] = Field(default=[], description="审批步骤配置")
    is_active: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否为默认工作流")


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    """创建工作流定义Schema"""

    pass


class WorkflowDefinitionUpdate(BaseModel):
    """更新工作流定义Schema"""

    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class WorkflowDefinitionResponse(WorkflowDefinitionBase):
    """工作流定义响应Schema"""

    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== 审批实例 Schemas ====================


class ApprovalInstanceBase(BaseModel):
    """审批实例基础Schema"""

    workflow_id: int = Field(..., description="工作流定义ID")
    document_type: str = Field(..., description="文档类型")
    document_id: Optional[int] = Field(None, description="旧业务表数字ID")
    document_ref: str = Field(..., description="稳定对象引用，支持UUID")
    version_key: Optional[str] = Field(None, description="审批版本标识")
    version_snapshot: Dict[str, Any] = Field(
        default_factory=dict, description="不可变版本快照"
    )
    snapshot_hash: Optional[str] = Field(None, description="版本快照SHA256")
    document_number: Optional[str] = Field(None, description="文档编号")
    document_title: Optional[str] = Field(None, description="文档标题")
    workspace_type: str = Field(default="enterprise", description="工作区类型")
    company_id: Optional[int] = Field(None, description="企业ID")
    factory_id: Optional[int] = Field(None, description="工厂ID")
    priority: str = Field(default="normal", description="优先级")
    notes: Optional[str] = Field(None, description="备注")


class ApprovalInstanceCreate(ApprovalInstanceBase):
    """创建审批实例Schema"""

    pass


class ApprovalInstanceUpdate(BaseModel):
    """更新审批实例Schema"""

    status: Optional[str] = None
    current_step: Optional[int] = None
    current_step_name: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None


class ApprovalInstanceResponse(ApprovalInstanceBase):
    """审批实例响应Schema"""

    id: int
    status: str
    current_step: int
    current_step_name: Optional[str] = None
    submitter_id: int
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_approver_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 审批历史 Schemas ====================


class ApprovalHistoryBase(BaseModel):
    """审批历史基础Schema"""

    instance_id: int = Field(..., description="审批实例ID")
    step_number: int = Field(..., description="步骤编号")
    step_name: Optional[str] = Field(None, description="步骤名称")
    action: str = Field(..., description="操作类型")
    comment: Optional[str] = Field(None, description="审批意见")
    attachments: List[str] = Field(default=[], description="附件列表")
    result: Optional[str] = Field(None, description="结果")


class ApprovalHistoryCreate(ApprovalHistoryBase):
    """创建审批历史Schema"""

    operator_id: int = Field(..., description="操作人ID")
    operator_name: Optional[str] = Field(None, description="操作人姓名")
    operator_role: Optional[str] = Field(None, description="操作人角色")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")


class ApprovalHistoryResponse(ApprovalHistoryBase):
    """审批历史响应Schema"""

    id: int
    operator_id: int
    operator_name: Optional[str] = None
    operator_role: Optional[str] = None
    created_at: datetime
    ip_address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== 审批操作 Schemas ====================


class SubmitForApprovalRequest(BaseModel):
    """提交审批请求Schema"""

    document_type: str = Field(..., description="文档类型")
    document_ids: List[int] = Field(..., description="文档ID列表（支持批量）")
    workflow_id: Optional[int] = Field(None, description="指定工作流ID（可选）")
    notes: Optional[str] = Field(None, description="备注")


class ApprovalActionRequest(BaseModel):
    """审批操作请求Schema"""

    action: str = Field(..., description="操作类型: approve, reject, return")
    comment: str = Field(..., description="审批意见")
    attachments: List[str] = Field(default=[], description="附件列表")


class BatchApprovalRequest(BaseModel):
    """批量审批请求Schema"""

    instance_ids: List[int] = Field(..., description="审批实例ID列表")
    action: str = Field(..., description="操作类型: approve, reject")
    comment: str = Field(..., description="审批意见")


# ==================== 审批通知 Schemas ====================


class ApprovalNotificationBase(BaseModel):
    """审批通知基础Schema"""

    instance_id: int = Field(..., description="审批实例ID")
    recipient_id: int = Field(..., description="接收人ID")
    notification_type: str = Field(..., description="通知类型")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    send_email: bool = Field(default=True, description="是否发送邮件")
    send_in_app: bool = Field(default=True, description="是否发送应用内通知")


class ApprovalNotificationCreate(ApprovalNotificationBase):
    """创建审批通知Schema"""

    recipient_email: Optional[str] = None


class ApprovalNotificationResponse(ApprovalNotificationBase):
    """审批通知响应Schema"""

    id: int
    is_sent: bool
    sent_at: Optional[datetime] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 查询和统计 Schemas ====================


class ApprovalStatistics(BaseModel):
    """审批统计Schema"""

    total_pending: int = Field(default=0, description="待审批总数")
    total_approved: int = Field(default=0, description="已批准总数")
    total_rejected: int = Field(default=0, description="已拒绝总数")
    my_pending: int = Field(default=0, description="我的待审批")
    my_submitted: int = Field(default=0, description="我提交的")
    overdue: int = Field(default=0, description="超时未审批")


class ApprovalListQuery(BaseModel):
    """审批列表查询Schema"""

    status: Optional[str] = Field(None, description="状态筛选")
    document_type: Optional[str] = Field(None, description="文档类型筛选")
    submitter_id: Optional[int] = Field(None, description="提交人筛选")
    company_id: Optional[int] = Field(None, description="企业筛选")
    factory_id: Optional[int] = Field(None, description="工厂筛选")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class ApprovalDetailResponse(BaseModel):
    """审批详情响应Schema"""

    instance: ApprovalInstanceResponse
    workflow: WorkflowDefinitionResponse
    history: List[ApprovalHistoryResponse]
    can_approve: bool = Field(default=False, description="当前用户是否可以审批")
    can_cancel: bool = Field(default=False, description="当前用户是否可以取消")
    next_approvers: List[Dict[str, Any]] = Field(default=[], description="下一步审批人列表")

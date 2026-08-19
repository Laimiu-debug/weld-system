"""
Approval workflow models for the welding system backend.
文档审批工作流数据模型
"""
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class ApprovalStatus(str, enum.Enum):
    """审批状态"""
    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审批
    IN_PROGRESS = "in_progress"  # 审批中
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消
    RETURNED = "returned"  # 已退回


class ApprovalAction(str, enum.Enum):
    """审批操作"""
    SUBMIT = "submit"  # 提交
    APPROVE = "approve"  # 批准
    REJECT = "reject"  # 拒绝
    RETURN = "return"  # 退回
    CANCEL = "cancel"  # 取消
    COMMENT = "comment"  # 评论


class DocumentType(str, enum.Enum):
    """文档类型"""
    WPS = "wps"  # 焊接工艺规范
    PQR = "pqr"  # 工艺评定记录
    PPQR = "ppqr"  # 预备工艺评定记录
    EQUIPMENT = "equipment"  # 设备
    MATERIAL = "material"  # 材料
    WELDER = "welder"  # 焊工
    PRODUCTION = "production"  # 生产任务
    QUALITY = "quality"  # 质量检验


class ApprovalWorkflowDefinition(Base):
    """审批工作流定义"""
    
    __tablename__ = "approval_workflow_definitions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="工作流名称")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="工作流代码")
    description = Column(Text, comment="描述")
    
    # 适用范围
    document_type = Column(String(50), nullable=False, index=True, comment="文档类型")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID（NULL表示系统默认）")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")
    
    # 工作流配置
    steps = Column(JSONB, nullable=False, default=[], comment="审批步骤配置")
    # 步骤格式: [
    #   {
    #     "step_number": 1,
    #     "step_name": "技术审核",
    #     "approver_type": "role",  # role, user, department
    #     "approver_ids": [1, 2, 3],  # 角色ID或用户ID列表
    #     "approval_mode": "any",  # any(任一), all(全部), sequential(顺序)
    #     "time_limit_hours": 48,  # 时限（小时）
    #     "is_required": true,  # 是否必需
    #     "can_skip": false  # 是否可跳过
    #   }
    # ]
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认工作流")
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    
    # 关系
    instances = relationship("ApprovalInstance", back_populates="workflow_definition")
    
    # 索引
    __table_args__ = (
        Index('ix_workflow_company_type', 'company_id', 'document_type'),
    )


class ApprovalInstance(Base):
    """审批实例"""
    
    __tablename__ = "approval_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 工作流关联
    workflow_id = Column(Integer, ForeignKey("approval_workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True, comment="工作流定义ID")
    
    # 文档关联
    document_type = Column(String(50), nullable=False, index=True, comment="文档类型")
    document_id = Column(Integer, nullable=False, index=True, comment="文档ID")
    document_number = Column(String(100), comment="文档编号")
    document_title = Column(String(200), comment="文档标题")
    
    # 工作区信息
    workspace_type = Column(String(20), nullable=False, default="enterprise", index=True, comment="工作区类型")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")
    
    # 审批状态
    status = Column(String(20), nullable=False, default="draft", index=True, comment="审批状态")
    current_step = Column(Integer, default=0, comment="当前步骤")
    current_step_name = Column(String(100), comment="当前步骤名称")
    
    # 提交信息
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="提交人ID")
    submitted_at = Column(DateTime, comment="提交时间")
    
    # 完成信息
    completed_at = Column(DateTime, comment="完成时间")
    final_approver_id = Column(Integer, ForeignKey("users.id"), comment="最终批准人ID")
    
    # 附加信息
    priority = Column(String(20), default="normal", comment="优先级: low, normal, high, urgent")
    notes = Column(Text, comment="备注")
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    workflow_definition = relationship("ApprovalWorkflowDefinition", back_populates="instances")
    history = relationship("ApprovalHistory", back_populates="instance", order_by="ApprovalHistory.created_at")
    
    # 索引
    __table_args__ = (
        Index('ix_approval_document', 'document_type', 'document_id'),
        Index('ix_approval_company_status', 'company_id', 'status'),
        Index('ix_approval_submitter', 'submitter_id', 'status'),
        Index('ix_approval_status_created', 'status', 'created_at'),
    )


class ApprovalHistory(Base):
    """审批历史记录"""
    
    __tablename__ = "approval_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 审批实例关联
    instance_id = Column(Integer, ForeignKey("approval_instances.id", ondelete="CASCADE"), nullable=False, index=True, comment="审批实例ID")
    
    # 步骤信息
    step_number = Column(Integer, nullable=False, comment="步骤编号")
    step_name = Column(String(100), comment="步骤名称")
    
    # 操作信息
    action = Column(String(20), nullable=False, comment="操作类型")
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="操作人ID")
    operator_name = Column(String(100), comment="操作人姓名")
    operator_role = Column(String(100), comment="操作人角色")
    
    # 审批意见
    comment = Column(Text, comment="审批意见")
    attachments = Column(JSONB, default=[], comment="附件列表")
    
    # 结果
    result = Column(String(20), comment="结果: approved, rejected, returned")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="操作时间")
    
    # 额外信息
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    
    # 关系
    instance = relationship("ApprovalInstance", back_populates="history")
    
    # 索引
    __table_args__ = (
        Index('ix_history_instance_step', 'instance_id', 'step_number'),
        Index('ix_history_operator', 'operator_id', 'created_at'),
    )


class ApprovalNotification(Base):
    """审批通知记录"""
    
    __tablename__ = "approval_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 审批实例关联
    instance_id = Column(Integer, ForeignKey("approval_instances.id", ondelete="CASCADE"), nullable=False, index=True, comment="审批实例ID")
    
    # 接收人信息
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="接收人ID")
    recipient_email = Column(String(255), comment="接收人邮箱")
    
    # 通知内容
    notification_type = Column(String(50), nullable=False, comment="通知类型: submitted, approved, rejected, returned, reminder")
    title = Column(String(200), comment="通知标题")
    content = Column(Text, comment="通知内容")
    
    # 发送状态
    is_sent = Column(Boolean, default=False, comment="是否已发送")
    sent_at = Column(DateTime, comment="发送时间")
    is_read = Column(Boolean, default=False, comment="是否已读")
    read_at = Column(DateTime, comment="阅读时间")
    
    # 发送渠道
    send_email = Column(Boolean, default=True, comment="是否发送邮件")
    send_in_app = Column(Boolean, default=True, comment="是否发送应用内通知")
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 索引
    __table_args__ = (
        Index('ix_notification_recipient', 'recipient_id', 'is_read'),
        Index('ix_notification_instance', 'instance_id', 'created_at'),
    )


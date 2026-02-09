"""
Production models for the welding system backend.
生产管理数据模型
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"  # 待开始
    IN_PROGRESS = "in_progress"  # 进行中
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    FAILED = "failed"  # 失败


class TaskPriority(str, enum.Enum):
    """任务优先级"""
    LOW = "low"  # 低
    NORMAL = "normal"  # 普通
    HIGH = "high"  # 高
    URGENT = "urgent"  # 紧急


class WorkspaceType(str, enum.Enum):
    """工作区类型"""
    PERSONAL = "personal"  # 个人工作区
    ENTERPRISE = "enterprise"  # 企业工作区


class AccessLevel(str, enum.Enum):
    """数据访问级别"""
    PRIVATE = "private"  # 仅创建者可见
    FACTORY = "factory"  # 同工厂成员可见
    COMPANY = "company"  # 全公司成员可见
    PUBLIC = "public"  # 公开


class ProductionTask(Base):
    """生产任务模型"""
    
    __tablename__ = "production_tasks"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # ==================== 数据隔离核心字段 ====================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="创建用户ID")
    workspace_type = Column(String(20), nullable=False, default="personal", index=True, comment="工作区类型")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")
    
    # 数据访问控制
    is_shared = Column(Boolean, default=False, comment="是否在企业内共享")
    access_level = Column(String(20), default="private", comment="访问级别")
    
    # ==================== 基本信息 ====================
    task_number = Column(String(100), nullable=False, unique=True, index=True, comment="任务编号")
    task_name = Column(String(255), nullable=False, comment="任务名称")
    task_type = Column(String(100), comment="任务类型")
    project_name = Column(String(255), comment="项目名称")
    project_code = Column(String(100), comment="项目编号")
    
    # ==================== 关联信息 ====================
    wps_id = Column(Integer, ForeignKey("wps.id"), comment="WPS ID")
    pqr_id = Column(Integer, ForeignKey("pqr.id"), comment="PQR ID")
    customer_name = Column(String(255), comment="客户名称")
    customer_code = Column(String(100), comment="客户编号")
    
    # ==================== 时间信息 ====================
    planned_start_date = Column(Date, comment="计划开始日期")
    planned_end_date = Column(Date, comment="计划结束日期")
    actual_start_date = Column(Date, comment="实际开始日期")
    actual_end_date = Column(Date, comment="实际结束日期")
    estimated_duration_hours = Column(Float, comment="预计工时(h)")
    actual_duration_hours = Column(Float, comment="实际工时(h)")
    
    # ==================== 状态信息 ====================
    status = Column(String(50), default="pending", comment="状态")
    priority = Column(String(50), default="normal", comment="优先级")
    progress_percentage = Column(Float, default=0, comment="进度百分比")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # ==================== 分配信息 ====================
    assigned_welder_id = Column(Integer, ForeignKey("welders.id"), comment="分配焊工ID")
    assigned_equipment_id = Column(Integer, ForeignKey("equipment.id"), comment="分配设备ID")
    team_leader_id = Column(Integer, ForeignKey("users.id"), comment="组长ID")
    team_members = Column(Text, comment="团队成员ID列表(JSON)")
    
    # ==================== 工作内容 ====================
    work_description = Column(Text, comment="工作描述")
    technical_requirements = Column(Text, comment="技术要求")
    quality_requirements = Column(Text, comment="质量要求")
    safety_requirements = Column(Text, comment="安全要求")
    
    # ==================== 数量信息 ====================
    planned_quantity = Column(Float, comment="计划数量")
    completed_quantity = Column(Float, default=0, comment="完成数量")
    unit = Column(String(50), comment="单位")
    weld_length_planned = Column(Float, comment="计划焊接长度(m)")
    weld_length_actual = Column(Float, comment="实际焊接长度(m)")
    
    # ==================== 材料信息 ====================
    base_material = Column(String(255), comment="母材")
    filler_material = Column(String(255), comment="填充材料")
    material_thickness = Column(Float, comment="材料厚度(mm)")
    material_quantity = Column(Float, comment="材料数量")
    
    # ==================== 成本信息 ====================
    estimated_cost = Column(Float, comment="预计成本")
    actual_cost = Column(Float, comment="实际成本")
    labor_cost = Column(Float, comment="人工成本")
    material_cost = Column(Float, comment="材料成本")
    equipment_cost = Column(Float, comment="设备成本")
    currency = Column(String(10), default="CNY", comment="货币")
    
    # ==================== 质量信息 ====================
    quality_inspection_required = Column(Boolean, default=True, comment="是否需要质量检验")
    inspection_status = Column(String(50), comment="检验状态")
    quality_result = Column(String(50), comment="质量结果")
    defect_count = Column(Integer, default=0, comment="缺陷数量")
    rework_count = Column(Integer, default=0, comment="返工次数")
    
    # ==================== 附加信息 ====================
    description = Column(Text, comment="描述")
    notes = Column(Text, comment="备注")
    drawings = Column(Text, comment="图纸(JSON)")
    documents = Column(Text, comment="相关文档(JSON)")
    images = Column(Text, comment="图片(JSON)")
    tags = Column(Text, comment="标签")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # ==================== 关系 ====================
    # owner = relationship("User", foreign_keys=[user_id], back_populates="production_tasks")
    # company = relationship("Company", back_populates="production_tasks")
    # factory = relationship("Factory", back_populates="production_tasks")
    # wps = relationship("WPS", back_populates="production_tasks")
    # assigned_welder = relationship("Welder", back_populates="production_tasks")
    # assigned_equipment = relationship("Equipment", back_populates="production_tasks")
    # records = relationship("ProductionRecord", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ProductionTask(id={self.id}, number={self.task_number}, name={self.task_name})>"


class ProductionRecord(Base):
    """生产记录模型"""
    
    __tablename__ = "production_records"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # ==================== 关联信息 ====================
    task_id = Column(Integer, ForeignKey("production_tasks.id", ondelete="CASCADE"), nullable=False, index=True, comment="任务ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")
    
    # 关联资源
    welder_id = Column(Integer, ForeignKey("welders.id"), comment="焊工ID")
    equipment_id = Column(Integer, ForeignKey("equipment.id"), comment="设备ID")
    wps_id = Column(Integer, ForeignKey("wps.id"), comment="WPS ID")
    
    # ==================== 记录信息 ====================
    record_number = Column(String(100), comment="记录编号")
    record_date = Column(Date, nullable=False, comment="记录日期")
    work_shift = Column(String(50), comment="班次")
    
    # ==================== 时间信息 ====================
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    duration_hours = Column(Float, comment="工时(h)")
    break_time_hours = Column(Float, comment="休息时间(h)")
    effective_work_hours = Column(Float, comment="有效工时(h)")
    
    # ==================== 工作内容 ====================
    work_description = Column(Text, comment="工作描述")
    work_location = Column(String(255), comment="工作地点")
    welding_process = Column(String(100), comment="焊接工艺")
    welding_position = Column(String(50), comment="焊接位置")
    
    # ==================== 数量信息 ====================
    quantity_completed = Column(Float, comment="完成数量")
    unit = Column(String(50), comment="单位")
    weld_length = Column(Float, comment="焊接长度(m)")
    weld_weight = Column(Float, comment="焊接重量(kg)")
    
    # ==================== 材料消耗 ====================
    base_material_used = Column(Float, comment="母材消耗")
    filler_material_used = Column(Float, comment="填充材料消耗")
    gas_consumption = Column(Float, comment="气体消耗")
    power_consumption = Column(Float, comment="耗电量(kWh)")
    
    # ==================== 质量信息 ====================
    quality_status = Column(String(50), comment="质量状态")
    inspection_result = Column(String(50), comment="检验结果")
    defects_found = Column(Integer, default=0, comment="发现缺陷数")
    rework_required = Column(Boolean, default=False, comment="是否需要返工")
    
    # ==================== 环境条件 ====================
    temperature = Column(Float, comment="温度(°C)")
    humidity = Column(Float, comment="湿度(%)")
    weather_conditions = Column(String(100), comment="天气条件")
    
    # ==================== 问题记录 ====================
    issues_occurred = Column(Boolean, default=False, comment="是否发生问题")
    issue_description = Column(Text, comment="问题描述")
    corrective_actions = Column(Text, comment="纠正措施")
    
    # ==================== 附加信息 ====================
    notes = Column(Text, comment="备注")
    images = Column(Text, comment="图片(JSON)")
    attachments = Column(Text, comment="附件(JSON)")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # ==================== 关系 ====================
    # task = relationship("ProductionTask", back_populates="records")
    # welder = relationship("Welder")
    # equipment = relationship("Equipment")
    # wps = relationship("WPS")
    
    def __repr__(self):
        return f"<ProductionRecord(id={self.id}, date={self.record_date})>"


class ProductionPlan(Base):
    """生产计划模型"""
    
    __tablename__ = "production_plans"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # ==================== 数据隔离核心字段 ====================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="创建用户ID")
    workspace_type = Column(String(20), nullable=False, default="personal", index=True, comment="工作区类型")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")
    
    # ==================== 计划信息 ====================
    plan_number = Column(String(100), nullable=False, unique=True, index=True, comment="计划编号")
    plan_name = Column(String(255), nullable=False, comment="计划名称")
    plan_type = Column(String(100), comment="计划类型")
    
    # ==================== 时间信息 ====================
    plan_start_date = Column(Date, nullable=False, comment="计划开始日期")
    plan_end_date = Column(Date, nullable=False, comment="计划结束日期")
    
    # ==================== 状态信息 ====================
    status = Column(String(50), default="draft", comment="状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # ==================== 内容信息 ====================
    description = Column(Text, comment="描述")
    objectives = Column(Text, comment="目标")
    tasks = Column(Text, comment="任务列表(JSON)")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    def __repr__(self):
        return f"<ProductionPlan(id={self.id}, number={self.plan_number})>"


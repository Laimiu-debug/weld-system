"""
Production Management Pydantic schemas for the welding system backend.
生产管理 Pydantic Schema
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ==================== 生产任务基础Schema ====================

class ProductionTaskBase(BaseModel):
    """生产任务基础Schema"""
    task_number: str = Field(..., description="任务编号")
    task_name: str = Field(..., description="任务名称")
    task_type: Optional[str] = Field(None, description="任务类型")
    
    # 关联信息
    wps_id: Optional[int] = Field(None, description="WPS ID")
    pqr_id: Optional[int] = Field(None, description="PQR ID")
    # 注意：project_id 和 customer_id 在模型中不存在，已移除
    
    # 任务详情
    description: Optional[str] = Field(None, description="任务描述")
    technical_requirements: Optional[str] = Field(None, description="技术要求")
    
    # 计划信息
    planned_start_date: Optional[date] = Field(None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(None, description="计划结束日期")
    estimated_duration_hours: Optional[float] = Field(None, description="预计工时(h)")

    # 实际信息
    actual_start_date: Optional[date] = Field(None, description="实际开始日期")
    actual_end_date: Optional[date] = Field(None, description="实际结束日期")
    actual_duration_hours: Optional[float] = Field(None, description="实际工时(h)")
    
    # 人员分配
    assigned_welder_id: Optional[int] = Field(None, description="分配焊工ID")
    assigned_equipment_id: Optional[int] = Field(None, description="分配设备ID")
    team_leader_id: Optional[int] = Field(None, description="组长ID")
    team_members: Optional[str] = Field(None, description="团队成员ID列表(JSON)")

    # 材料信息
    base_material: Optional[str] = Field(None, description="母材")
    filler_material: Optional[str] = Field(None, description="填充材料")
    material_thickness: Optional[float] = Field(None, description="材料厚度(mm)")
    material_quantity: Optional[float] = Field(None, description="材料数量")

    # 成本信息
    estimated_cost: Optional[float] = Field(None, description="预计成本")
    actual_cost: Optional[float] = Field(None, description="实际成本")
    labor_cost: Optional[float] = Field(None, description="人工成本")
    material_cost: Optional[float] = Field(None, description="材料成本")
    equipment_cost: Optional[float] = Field(None, description="设备成本")
    currency: Optional[str] = Field(default="CNY", description="货币")

    # 质量信息
    quality_inspection_required: Optional[bool] = Field(default=True, description="是否需要质量检验")
    inspection_status: Optional[str] = Field(None, description="检验状态")
    quality_result: Optional[str] = Field(None, description="质量结果")
    defect_count: Optional[int] = Field(default=0, description="缺陷数量")
    rework_count: Optional[int] = Field(default=0, description="返工次数")

    # 数量信息
    planned_quantity: Optional[float] = Field(None, description="计划数量")
    completed_quantity: Optional[float] = Field(default=0, description="完成数量")
    unit: Optional[str] = Field(None, description="单位")
    weld_length_planned: Optional[float] = Field(None, description="计划焊接长度(m)")
    weld_length_actual: Optional[float] = Field(None, description="实际焊接长度(m)")

    # 工作内容
    work_description: Optional[str] = Field(None, description="工作描述")
    technical_requirements: Optional[str] = Field(None, description="技术要求")
    quality_requirements: Optional[str] = Field(None, description="质量要求")
    safety_requirements: Optional[str] = Field(None, description="安全要求")
    
    # 状态信息
    status: str = Field(default="pending", description="状态")
    priority: str = Field(default="normal", description="优先级")
    progress_percentage: float = Field(default=0, ge=0, le=100, allow_inf_nan=False, description="进度百分比")

    # 项目信息
    project_name: Optional[str] = Field(None, description="项目名称")
    project_code: Optional[str] = Field(None, description="项目编号")

    # 客户信息
    customer_name: Optional[str] = Field(None, description="客户名称")
    customer_code: Optional[str] = Field(None, description="客户编号")

    # 附加信息
    notes: Optional[str] = Field(None, description="备注")
    drawings: Optional[str] = Field(None, description="图纸(JSON)")
    documents: Optional[str] = Field(None, description="相关文档(JSON)")
    images: Optional[str] = Field(None, description="图片(JSON)")
    tags: Optional[str] = Field(None, description="标签")


# ==================== 创建Schema ====================

class ProductionTaskCreate(ProductionTaskBase):
    """创建生产任务Schema"""
    pass


# ==================== 更新Schema ====================

class ProductionTaskUpdate(BaseModel):
    """更新生产任务Schema"""
    task_number: Optional[str] = None
    task_name: Optional[str] = None
    task_type: Optional[str] = None
    wps_id: Optional[int] = None
    pqr_id: Optional[int] = None
    description: Optional[str] = None
    technical_requirements: Optional[str] = None
    safety_requirements: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    estimated_duration_hours: Optional[float] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_duration_hours: Optional[float] = None
    assigned_welder_id: Optional[int] = None
    assigned_equipment_id: Optional[int] = None
    team_leader_id: Optional[int] = None
    team_members: Optional[str] = None
    base_material: Optional[str] = None
    filler_material: Optional[str] = None
    material_thickness: Optional[float] = None
    material_quantity: Optional[float] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    equipment_cost: Optional[float] = None
    currency: Optional[str] = None
    quality_inspection_required: Optional[bool] = None
    inspection_status: Optional[str] = None
    quality_result: Optional[str] = None
    defect_count: Optional[int] = None
    rework_count: Optional[int] = None
    planned_quantity: Optional[float] = None
    completed_quantity: Optional[float] = None
    unit: Optional[str] = None
    weld_length_planned: Optional[float] = None
    weld_length_actual: Optional[float] = None
    work_description: Optional[str] = None
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    notes: Optional[str] = None
    drawings: Optional[str] = None
    documents: Optional[str] = None
    images: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100, allow_inf_nan=False)


# ==================== 响应Schema ====================

class ProductionTaskResponse(ProductionTaskBase):
    """生产任务响应Schema"""
    id: int
    user_id: int
    workspace_type: str
    company_id: Optional[int] = None
    factory_id: Optional[int] = None
    access_level: str
    is_shared: bool
    
    # 审计字段
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    wps_number: Optional[str] = None
    wps_title: Optional[str] = None
    welder_name: Optional[str] = None
    welder_code: Optional[str] = None
    equipment_name: Optional[str] = None
    equipment_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== 列表响应Schema ====================

class ProductionTaskListResponse(BaseModel):
    """生产任务列表响应Schema"""
    items: List[ProductionTaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== 生产记录Schema ====================

class ProductionRecordBase(BaseModel):
    """生产记录基础Schema（与 production_records 表字段对齐）"""
    record_number: Optional[str] = Field(None, description="记录编号")
    record_date: date = Field(..., description="记录日期")
    work_shift: Optional[str] = Field(None, description="班次")
    welder_id: Optional[int] = Field(None, description="焊工ID")
    equipment_id: Optional[int] = Field(None, description="设备ID")
    wps_id: Optional[int] = Field(None, description="WPS ID")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_hours: Optional[float] = Field(None, description="工时(h)")
    break_time_hours: Optional[float] = Field(None, description="休息时间(h)")
    effective_work_hours: Optional[float] = Field(None, description="有效工时(h)")
    work_description: Optional[str] = Field(None, description="工作描述")
    work_location: Optional[str] = Field(None, description="工作地点")
    welding_process: Optional[str] = Field(None, description="焊接工艺")
    welding_position: Optional[str] = Field(None, description="焊接位置")
    quantity_completed: Optional[float] = Field(None, description="完成数量")
    unit: Optional[str] = Field(None, description="单位")
    weld_length: Optional[float] = Field(None, description="焊接长度(m)")
    weld_weight: Optional[float] = Field(None, description="焊接重量(kg)")
    base_material_used: Optional[float] = Field(None, description="母材消耗")
    filler_material_used: Optional[float] = Field(None, description="填充材料消耗")
    gas_consumption: Optional[float] = Field(None, description="气体消耗")
    power_consumption: Optional[float] = Field(None, description="耗电量(kWh)")
    quality_status: Optional[str] = Field(default="pending", description="质量状态")
    inspection_result: Optional[str] = Field(None, description="检验结果")
    defects_found: Optional[int] = Field(default=0, description="发现缺陷数")
    rework_required: Optional[bool] = Field(default=False, description="是否需要返工")
    temperature: Optional[float] = Field(None, description="温度(°C)")
    humidity: Optional[float] = Field(None, description="湿度(%)")
    weather_conditions: Optional[str] = Field(None, description="天气条件")
    issues_occurred: Optional[bool] = Field(default=False, description="是否发生问题")
    issue_description: Optional[str] = Field(None, description="问题描述")
    corrective_actions: Optional[str] = Field(None, description="纠正措施")
    notes: Optional[str] = Field(None, description="备注")
    images: Optional[str] = Field(None, description="图片(JSON)")
    attachments: Optional[str] = Field(None, description="附件(JSON)")


class ProductionRecordCreate(ProductionRecordBase):
    """创建生产记录Schema"""
    progress_percentage: Optional[float] = Field(None, ge=0, le=100, description="同步更新任务进度")


class ProductionProgressUpdate(BaseModel):
    """更新生产任务进度"""
    progress_percentage: float = Field(..., ge=0, le=100, description="进度百分比")
    status: Optional[str] = Field(None, description="可选同步状态")
    notes: Optional[str] = Field(None, description="进度备注")


class ProductionRecordResponse(ProductionRecordBase):
    """生产记录响应Schema"""
    id: int
    task_id: int
    user_id: int
    company_id: Optional[int] = None
    factory_id: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 统计Schema ====================

class ProductionStatistics(BaseModel):
    """生产统计Schema"""
    total_tasks: int = Field(..., description="任务总数")
    pending_tasks: int = Field(..., description="待处理任务数")
    in_progress_tasks: int = Field(..., description="进行中任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    overdue_tasks: int = Field(..., description="逾期任务数")
    total_weld_length: float = Field(..., description="总焊缝长度(m)")
    total_work_hours: float = Field(..., description="总工时(h)")


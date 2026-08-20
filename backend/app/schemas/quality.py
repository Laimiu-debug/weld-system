"""
Quality Management Pydantic schemas for the welding system backend.
质量管理 Pydantic Schema
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ==================== 质量检验基础Schema ====================

class QualityInspectionBase(BaseModel):
    """质量检验基础Schema - 基于数据库模型"""
    inspection_number: Optional[str] = Field(None, description="检验编号（可空，后端自动生成）")
    inspection_type: Optional[str] = Field(None, description="检验类型")
    inspection_date: Optional[date] = Field(None, description="检验日期")
    # inspection_time字段已移除,因为数据库中只有inspection_date字段
    report_date: Optional[date] = Field(None, description="报告日期")

    # 关联信息
    production_task_id: Optional[int] = Field(None, description="生产任务ID")
    wps_id: Optional[int] = Field(None, description="WPS ID")
    pqr_id: Optional[int] = Field(None, description="PQR ID")

    # 定位层级：项目 → 容器/工令 → 焊缝
    project_name: Optional[str] = Field(None, description="项目名称")
    vessel_no: Optional[str] = Field(None, description="容器号")
    work_order_no: Optional[str] = Field(None, description="工令号")
    weld_joint_number: Optional[str] = Field(None, description="焊缝编号")

    # 检验人员
    inspector_id: Optional[int] = Field(None, description="检验员ID")
    inspector_name: Optional[str] = Field(None, description="检验员姓名")
    inspector_certification: Optional[str] = Field(None, description="检验员资质")
    witness_name: Optional[str] = Field(None, description="见证人")

    # 检验对象
    item_description: Optional[str] = Field(None, description="检验对象描述")
    item_quantity: Optional[float] = Field(None, description="检验数量")
    item_unit: Optional[str] = Field(None, description="单位")
    batch_number: Optional[str] = Field(None, description="批次号")
    serial_number: Optional[str] = Field(None, description="序列号")

    # 检验位置
    inspection_location: Optional[str] = Field(None, description="检验位置")

    # 检验标准
    inspection_standard: Optional[str] = Field(None, description="检验标准")
    inspection_procedure: Optional[str] = Field(None, description="检验程序")

    # 检验结果
    result: Optional[str] = Field(default="pending", description="检验结果")
    acceptance_criteria: Optional[str] = Field(None, description="验收标准")
    actual_measurements: Optional[str] = Field(None, description="实际测量值(JSON)")

    # 缺陷信息
    defects_found: Optional[int] = Field(default=0, description="发现缺陷数")
    defect_details: Optional[str] = Field(None, description="缺陷详情(JSON)")
    defect_locations: Optional[str] = Field(None, description="缺陷位置(JSON)")
    max_defect_severity: Optional[str] = Field(None, description="最大缺陷严重程度")

    # 缺陷详细计数
    crack_count: Optional[int] = Field(default=0, description="裂纹数量")
    porosity_count: Optional[int] = Field(default=0, description="气孔数量")
    inclusion_count: Optional[int] = Field(default=0, description="夹渣数量")
    undercut_count: Optional[int] = Field(default=0, description="咬边数量")
    incomplete_penetration_count: Optional[int] = Field(default=0, description="未焊透数量")
    incomplete_fusion_count: Optional[int] = Field(default=0, description="未熔合数量")
    other_defect_count: Optional[int] = Field(default=0, description="其他缺陷数量")
    other_defect_description: Optional[str] = Field(None, description="其他缺陷描述")

    # 处理措施
    corrective_action_required: Optional[bool] = Field(default=False, description="是否需要纠正措施")
    corrective_actions: Optional[str] = Field(None, description="纠正措施")
    rework_required: Optional[bool] = Field(default=False, description="是否需要返工")
    rework_description: Optional[str] = Field(None, description="返工描述")
    repair_required: Optional[bool] = Field(default=False, description="是否需要修复")
    repair_description: Optional[str] = Field(None, description="修复描述")
    follow_up_required: Optional[bool] = Field(default=False, description="是否需要跟进")
    follow_up_date: Optional[date] = Field(None, description="跟进日期")

    # 复检信息
    reinspection_required: Optional[bool] = Field(default=False, description="是否需要复检")
    reinspection_date: Optional[date] = Field(None, description="复检日期")
    reinspection_result: Optional[str] = Field(None, description="复检结果")
    reinspection_inspector_id: Optional[int] = Field(None, description="复检员ID")
    reinspection_notes: Optional[str] = Field(None, description="复检备注")

    # 环境条件
    ambient_temperature: Optional[float] = Field(None, description="环境温度(°C)")
    temperature: Optional[float] = Field(None, description="温度(°C)")
    humidity: Optional[float] = Field(None, description="湿度(%)")
    weather_conditions: Optional[str] = Field(None, description="天气条件")
    environmental_conditions: Optional[str] = Field(None, description="环境条件")

    # 设备信息
    equipment_used: Optional[str] = Field(None, description="使用设备(JSON)")
    equipment_calibration_date: Optional[date] = Field(None, description="设备校准日期")

    # 附加信息
    description: Optional[str] = Field(None, description="描述")
    notes: Optional[str] = Field(None, description="备注")
    recommendations: Optional[str] = Field(None, description="建议")
    report_file_url: Optional[str] = Field(None, description="报告文件URL")
    photos: Optional[str] = Field(None, description="照片(JSON)")
    images: Optional[str] = Field(None, description="图片(JSON)")
    reports: Optional[str] = Field(None, description="报告(JSON)")
    attachments: Optional[str] = Field(None, description="附件(JSON)")
    tags: Optional[str] = Field(None, description="标签")

    # 审批信息
    reviewed_by: Optional[int] = Field(None, description="审核人ID")
    reviewed_date: Optional[date] = Field(None, description="审核日期")
    approved_by: Optional[int] = Field(None, description="批准人ID")
    approved_date: Optional[date] = Field(None, description="批准日期")

    # 状态信息
    status: Optional[str] = Field(default="draft", description="状态")


# ==================== 创建Schema ====================

class QualityInspectionCreate(QualityInspectionBase):
    """创建质量检验Schema"""
    pass


# ==================== 更新Schema ====================

class QualityInspectionUpdate(BaseModel):
    """更新质量检验Schema"""
    inspection_number: Optional[str] = None
    inspection_type: Optional[str] = None
    inspection_date: Optional[date] = None
    # inspection_time字段已移除,因为数据库中只有inspection_date字段
    report_date: Optional[date] = None
    production_task_id: Optional[int] = None
    wps_id: Optional[int] = None
    pqr_id: Optional[int] = None
    project_name: Optional[str] = None
    vessel_no: Optional[str] = None
    work_order_no: Optional[str] = None
    weld_joint_number: Optional[str] = None
    inspector_id: Optional[int] = None
    inspector_name: Optional[str] = None
    inspector_certification: Optional[str] = None
    witness_name: Optional[str] = None
    item_description: Optional[str] = None
    item_quantity: Optional[float] = None
    item_unit: Optional[str] = None
    batch_number: Optional[str] = None
    serial_number: Optional[str] = None
    inspection_location: Optional[str] = None
    inspection_standard: Optional[str] = None
    inspection_procedure: Optional[str] = None
    result: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    actual_measurements: Optional[str] = None
    defects_found: Optional[int] = None
    defect_details: Optional[str] = None
    defect_locations: Optional[str] = None
    max_defect_severity: Optional[str] = None
    crack_count: Optional[int] = None
    porosity_count: Optional[int] = None
    inclusion_count: Optional[int] = None
    undercut_count: Optional[int] = None
    incomplete_penetration_count: Optional[int] = None
    incomplete_fusion_count: Optional[int] = None
    other_defect_count: Optional[int] = None
    other_defect_description: Optional[str] = None
    corrective_action_required: Optional[bool] = None
    corrective_actions: Optional[str] = None
    rework_required: Optional[bool] = None
    rework_description: Optional[str] = None
    repair_required: Optional[bool] = None
    repair_description: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[date] = None
    reinspection_required: Optional[bool] = None
    reinspection_date: Optional[date] = None
    reinspection_result: Optional[str] = None
    reinspection_inspector_id: Optional[int] = None
    reinspection_notes: Optional[str] = None
    ambient_temperature: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    weather_conditions: Optional[str] = None
    environmental_conditions: Optional[str] = None
    equipment_used: Optional[str] = None
    equipment_calibration_date: Optional[date] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    recommendations: Optional[str] = None
    report_file_url: Optional[str] = None
    photos: Optional[str] = None
    images: Optional[str] = None
    reports: Optional[str] = None
    attachments: Optional[str] = None
    tags: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_date: Optional[date] = None
    approved_by: Optional[int] = None
    approved_date: Optional[date] = None
    status: Optional[str] = None


# ==================== 响应Schema ====================

class QualityInspectionResponse(QualityInspectionBase):
    """质量检验响应Schema"""
    id: int
    owner_id: int  # 实际数据库字段
    company_id: Optional[int] = None
    factory_id: Optional[int] = None

    # 添加is_qualified字段（从模型属性计算）
    is_qualified: bool = Field(default=False, description="是否合格（根据result计算）")

    # 审计字段
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 列表响应Schema ====================

class QualityInspectionListResponse(BaseModel):
    """质量检验列表响应Schema"""
    items: List[QualityInspectionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== 不合格品记录Schema ====================

class NonconformanceRecordBase(BaseModel):
    """不合格品记录基础Schema"""
    ncr_number: Optional[str] = Field(None, description="不合格品编号")
    ncr_title: str = Field(..., description="标题")
    inspection_id: Optional[int] = Field(None, description="检验ID")
    production_task_id: Optional[int] = Field(None, description="生产任务ID")
    wps_id: Optional[int] = Field(None, description="WPS ID")
    occurrence_date: date = Field(..., description="发生日期")
    reported_date: Optional[date] = Field(None, description="报告日期")
    nonconformance_type: Optional[str] = Field(None, description="不合格类型")
    nonconformance_category: Optional[str] = Field(None, description="不合格类别")
    severity: Optional[str] = Field(None, description="严重程度")
    description: str = Field(..., description="描述")
    responsible_person_id: Optional[int] = Field(None, description="责任人ID")
    responsible_department: Optional[str] = Field(None, description="责任部门")
    root_cause: Optional[str] = Field(None, description="根本原因")
    contributing_factors: Optional[str] = Field(None, description="促成因素")
    disposition: Optional[str] = Field(None, description="处置方式")
    corrective_actions: Optional[str] = Field(None, description="纠正措施")
    preventive_actions: Optional[str] = Field(None, description="预防措施")
    action_plan: Optional[str] = Field(None, description="行动计划(JSON)")
    resolution_status: Optional[str] = Field(default="open", description="解决状态")
    resolution_date: Optional[date] = Field(None, description="解决日期")
    resolution_description: Optional[str] = Field(None, description="解决描述")
    verification_result: Optional[str] = Field(None, description="验证结果")
    estimated_cost: Optional[float] = Field(None, description="预计成本")
    actual_cost: Optional[float] = Field(None, description="实际成本")
    currency: Optional[str] = Field(default="CNY", description="货币")
    notes: Optional[str] = Field(None, description="备注")
    images: Optional[str] = Field(None, description="图片(JSON)")
    attachments: Optional[str] = Field(None, description="附件(JSON)")


class NonconformanceRecordCreate(NonconformanceRecordBase):
    """创建不合格品记录"""
    pass


class NonconformanceRecordUpdate(BaseModel):
    """更新不合格品记录"""
    ncr_title: Optional[str] = None
    inspection_id: Optional[int] = None
    production_task_id: Optional[int] = None
    wps_id: Optional[int] = None
    occurrence_date: Optional[date] = None
    reported_date: Optional[date] = None
    nonconformance_type: Optional[str] = None
    nonconformance_category: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    responsible_person_id: Optional[int] = None
    responsible_department: Optional[str] = None
    root_cause: Optional[str] = None
    contributing_factors: Optional[str] = None
    disposition: Optional[str] = None
    corrective_actions: Optional[str] = None
    preventive_actions: Optional[str] = None
    action_plan: Optional[str] = None
    resolution_status: Optional[str] = None
    resolution_date: Optional[date] = None
    resolution_description: Optional[str] = None
    verification_result: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    images: Optional[str] = None
    attachments: Optional[str] = None


class NonconformanceRecordResponse(NonconformanceRecordBase):
    """不合格品记录响应"""
    id: int
    owner_id: int
    workspace_type: str
    company_id: Optional[int] = None
    factory_id: Optional[int] = None
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
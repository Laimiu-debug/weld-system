"""
WPS schemas for the welding system backend.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field
from app.core.html_security import SanitizedDocumentHTML


# 基础信息 schemas
class WPSBase(BaseModel):
    """Base WPS schema."""
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    wps_number: str = Field(..., min_length=1, max_length=50, description="WPS编号")
    revision: str = Field(default="A", max_length=10, description="版本号")
    status: str = Field(default="draft", max_length=20, description="状态")

    # 新增核心字段
    template_id: Optional[str] = Field(None, max_length=100, description="使用的模板ID")
    process_specification: Optional[str] = Field(None, max_length=50, description="工艺规范")
    product_name: Optional[str] = Field(None, max_length=200, description="产品名称")
    manufacturer: Optional[str] = Field(None, max_length=200, description="制造商")
    customer: Optional[str] = Field(None, max_length=200, description="用户/客户")
    location: Optional[str] = Field(None, max_length=200, description="地点")
    order_number: Optional[str] = Field(None, max_length=100, description="订单编号")
    part_number: Optional[str] = Field(None, max_length=100, description="部件编号")
    drawing_number: Optional[str] = Field(None, max_length=100, description="图纸编号")
    wpqr_number: Optional[str] = Field(None, max_length=100, description="WPQR编号/标准")
    welder_qualification: Optional[str] = Field(None, max_length=200, description="焊工资质要求")
    pdf_link: Optional[str] = Field(None, max_length=500, description="WPS PDF文件链接")

    company: Optional[str] = Field(None, max_length=100, description="公司名称")
    project_name: Optional[str] = Field(None, max_length=100, description="项目名称")

    # 焊接工艺参数
    welding_process: Optional[str] = Field(None, max_length=50, description="焊接工艺代码")
    process_type: Optional[str] = Field(None, max_length=20, description="工艺类型")

    # 母材信息
    base_material_group: Optional[str] = Field(None, max_length=50, description="母材组号")
    base_material_spec: Optional[str] = Field(None, max_length=50, description="母材规格")
    base_material_thickness_range: Optional[str] = Field(None, max_length=50, description="母材厚度范围")

    # 填充金属信息
    filler_material_spec: Optional[str] = Field(None, max_length=50, description="填充金属规格")
    filler_material_classification: Optional[str] = Field(None, max_length=50, description="填充金属分类")
    filler_material_diameter: Optional[float] = Field(None, gt=0, description="填充金属直径")

    # 保护气体信息
    shielding_gas: Optional[str] = Field(None, max_length=50, description="保护气体")
    gas_flow_rate: Optional[float] = Field(None, gt=0, description="气体流量")
    gas_composition: Optional[str] = Field(None, max_length=50, description="气体成分")

    # 电流参数
    current_type: Optional[str] = Field(None, max_length=10, description="电流类型")
    current_polarity: Optional[str] = Field(None, max_length=10, description="电极极性")
    current_range: Optional[str] = Field(None, max_length=50, description="电流范围")

    # 电压和送丝速度
    voltage_range: Optional[str] = Field(None, max_length=50, description="电压范围")
    wire_feed_speed: Optional[str] = Field(None, max_length=50, description="送丝速度")

    # 焊接速度
    welding_speed: Optional[str] = Field(None, max_length=50, description="焊接速度")
    travel_speed: Optional[str] = Field(None, max_length=50, description="行走速度")

    # 热输入
    heat_input_min: Optional[float] = Field(None, ge=0, description="最小热输入")
    heat_input_max: Optional[float] = Field(None, ge=0, description="最大热输入")

    # 焊道信息
    weld_passes: Optional[int] = Field(None, ge=1, description="焊道数量")
    weld_layer: Optional[int] = Field(None, ge=1, description="焊层数量")

    # 坡口设计
    joint_design: Optional[str] = Field(None, max_length=50, description="接头设计")
    groove_type: Optional[str] = Field(None, max_length=50, description="坡口类型")
    groove_angle: Optional[str] = Field(None, max_length=50, description="坡口角度")
    root_gap: Optional[str] = Field(None, max_length=50, description="根部间隙")
    root_face: Optional[str] = Field(None, max_length=50, description="根部钝边")

    # 预热和层间温度
    preheat_temp_min: Optional[float] = Field(None, ge=-273.15, description="最低预热温度")
    preheat_temp_max: Optional[float] = Field(None, ge=-273.15, description="最高预热温度")
    interpass_temp_max: Optional[float] = Field(None, ge=-273.15, description="最高层间温度")

    # 焊后热处理
    pwht_required: Optional[bool] = Field(False, description="是否需要焊后热处理")
    pwht_temperature: Optional[float] = Field(None, ge=-273.15, description="焊后热处理温度")
    pwht_time: Optional[float] = Field(None, gt=0, description="焊后热处理时间")

    # 检验和测试
    ndt_required: Optional[bool] = Field(True, description="是否需要无损检测")
    ndt_methods: Optional[str] = Field(None, description="无损检测方法")
    mechanical_testing: Optional[str] = Field(None, description="力学性能测试")

    # 重要性和特殊要求
    critical_application: Optional[bool] = Field(False, description="是否为关键应用")
    special_requirements: Optional[str] = Field(None, description="特殊要求说明")

    # 附加信息
    notes: Optional[str] = Field(None, description="备注")
    supporting_documents: Optional[str] = Field(None, description="支持文件链接")
    attachments: Optional[str] = Field(None, description="附件文件路径")

    # JSONB动态字段（用于存储模板驱动的数据）
    # 新增：完全灵活的模块数据存储
    # 结构: { "module_instance_id": { "field_key": value, ... }, ... }
    modules_data: Optional[Dict[str, Any]] = Field(None, description="所有模块数据（JSON格式），支持无限自定义")

    # 文档编辑模式字段
    document_html: SanitizedDocumentHTML = Field(None, description="文档HTML内容（用于文档编辑模式）")

    # 保留以下字段用于向后兼容（逐步废弃）
    header_info: Optional[Dict[str, Any]] = Field(None, description="表头数据（JSON格式）- 已废弃，使用 modules_data")
    summary_info: Optional[Dict[str, Any]] = Field(None, description="概要信息（JSON格式）- 已废弃，使用 modules_data")
    diagram_info: Optional[Dict[str, Any]] = Field(None, description="示意图信息（JSON格式）- 已废弃，使用 modules_data")
    weld_layers: Optional[List[Dict[str, Any]]] = Field(None, description="焊层信息数组（JSON格式）- 已废弃，使用 modules_data")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="附加信息（JSON格式）- 已废弃，使用 modules_data")


class WPSCreate(WPSBase):
    """WPS creation schema."""
    pass


class WPSUpdate(BaseModel):
    """WPS update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="标题")
    revision: Optional[str] = Field(None, max_length=10, description="版本号")
    status: Optional[str] = Field(None, max_length=20, description="状态")
    company: Optional[str] = Field(None, max_length=100, description="公司名称")
    project_name: Optional[str] = Field(None, max_length=100, description="项目名称")

    # 焊接工艺参数
    welding_process: Optional[str] = Field(None, max_length=50, description="焊接工艺")
    process_type: Optional[str] = Field(None, max_length=20, description="工艺类型")
    process_specification: Optional[str] = Field(None, max_length=50, description="工艺规范")

    # 母材信息
    base_material_group: Optional[str] = Field(None, max_length=50, description="母材组号")
    base_material_spec: Optional[str] = Field(None, max_length=50, description="母材规格")
    base_material_thickness_range: Optional[str] = Field(None, max_length=50, description="母材厚度范围")

    # 填充金属信息
    filler_material_spec: Optional[str] = Field(None, max_length=50, description="填充金属规格")
    filler_material_classification: Optional[str] = Field(None, max_length=50, description="填充金属分类")
    filler_material_diameter: Optional[float] = Field(None, gt=0, description="填充金属直径")

    # 保护气体信息
    shielding_gas: Optional[str] = Field(None, max_length=50, description="保护气体")
    gas_flow_rate: Optional[float] = Field(None, gt=0, description="气体流量")
    gas_composition: Optional[str] = Field(None, max_length=50, description="气体成分")

    # 电流参数
    current_type: Optional[str] = Field(None, max_length=10, description="电流类型")
    current_polarity: Optional[str] = Field(None, max_length=10, description="电极极性")
    current_range: Optional[str] = Field(None, max_length=50, description="电流范围")

    # 电压和送丝速度
    voltage_range: Optional[str] = Field(None, max_length=50, description="电压范围")
    wire_feed_speed: Optional[str] = Field(None, max_length=50, description="送丝速度")

    # 焊接速度
    welding_speed: Optional[str] = Field(None, max_length=50, description="焊接速度")
    travel_speed: Optional[str] = Field(None, max_length=50, description="行走速度")

    # 热输入
    heat_input_min: Optional[float] = Field(None, ge=0, description="最小热输入")
    heat_input_max: Optional[float] = Field(None, ge=0, description="最大热输入")

    # 焊道信息
    weld_passes: Optional[int] = Field(None, ge=1, description="焊道数量")
    weld_layer: Optional[int] = Field(None, ge=1, description="焊层数量")

    # 坡口设计
    joint_design: Optional[str] = Field(None, max_length=50, description="接头设计")
    groove_type: Optional[str] = Field(None, max_length=50, description="坡口类型")
    groove_angle: Optional[str] = Field(None, max_length=50, description="坡口角度")
    root_gap: Optional[str] = Field(None, max_length=50, description="根部间隙")
    root_face: Optional[str] = Field(None, max_length=50, description="根部钝边")

    # 预热和层间温度
    preheat_temp_min: Optional[float] = Field(None, ge=-273.15, description="最低预热温度")
    preheat_temp_max: Optional[float] = Field(None, ge=-273.15, description="最高预热温度")
    interpass_temp_max: Optional[float] = Field(None, ge=-273.15, description="最高层间温度")

    # 焊后热处理
    pwht_required: Optional[bool] = Field(None, description="是否需要焊后热处理")
    pwht_temperature: Optional[float] = Field(None, ge=-273.15, description="焊后热处理温度")
    pwht_time: Optional[float] = Field(None, gt=0, description="焊后热处理时间")

    # 检验和测试
    ndt_required: Optional[bool] = Field(None, description="是否需要无损检测")
    ndt_methods: Optional[str] = Field(None, description="无损检测方法")
    mechanical_testing: Optional[str] = Field(None, description="力学性能测试")

    # 重要性和特殊要求
    critical_application: Optional[bool] = Field(None, description="是否为关键应用")
    special_requirements: Optional[str] = Field(None, description="特殊要求说明")

    # 附加信息
    notes: Optional[str] = Field(None, description="备注")
    supporting_documents: Optional[str] = Field(None, description="支持文件链接")
    attachments: Optional[str] = Field(None, description="附件文件路径")

    # 文档编辑模式
    document_html: SanitizedDocumentHTML = Field(None, description="文档HTML内容（用于文档编辑模式）")

    # 审核和批准
    reviewed_by: Optional[int] = Field(None, description="审核人ID")
    approved_by: Optional[int] = Field(None, description="批准人ID")


class WPSResponse(WPSBase):
    """WPS response schema."""
    id: int
    owner_id: int
    reviewed_by: Optional[int] = None
    reviewed_date: Optional[datetime] = None
    approved_by: Optional[int] = None
    approved_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    # 审批相关字段
    approval_instance_id: Optional[int] = None
    approval_status: Optional[str] = None
    workflow_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WPSSummary(BaseModel):
    """WPS summary for list views."""
    id: int
    title: str
    wps_number: str
    revision: str
    status: str
    company: Optional[str] = None
    project_name: Optional[str] = None
    welding_process: Optional[str] = None
    base_material_spec: Optional[str] = None
    filler_material_classification: Optional[str] = None
    template_id: Optional[str] = None
    modules_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    # 审批相关字段
    approval_instance_id: Optional[int] = None
    approval_status: Optional[str] = None
    workflow_name: Optional[str] = None
    can_approve: Optional[bool] = None
    can_submit_approval: Optional[bool] = None
    submitter_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# WPS版本管理 schemas
class WPSRevisionBase(BaseModel):
    """Base WPS revision schema."""
    revision_number: str = Field(..., max_length=10, description="版本号")
    change_summary: str = Field(..., min_length=1, description="变更摘要")
    change_reason: str = Field(..., min_length=1, description="变更原因")
    changes_made: str = Field(..., min_length=1, description="具体变更内容")
    old_document_path: Optional[str] = Field(None, description="旧文档路径")
    new_document_path: Optional[str] = Field(None, description="新文档路径")


class WPSRevisionCreate(WPSRevisionBase):
    """WPS revision creation schema."""
    pass


class WPSRevisionResponse(WPSRevisionBase):
    """WPS revision response schema."""
    id: int
    wps_id: int
    changed_by: int
    change_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WPSExportRequest(BaseModel):
    """WPS export request schema."""
    wps_ids: List[int] = Field(..., description="要导出的WPS ID列表")
    export_format: str = Field(default="pdf", description="导出格式: pdf, docx, excel")
    include_revisions: bool = Field(default=False, description="是否包含版本历史")
    include_attachments: bool = Field(default=False, description="是否包含附件")


class WPSSearchParams(BaseModel):
    """WPS search parameters schema."""
    search_term: Optional[str] = Field(None, description="搜索关键词")
    status: Optional[str] = Field(None, description="状态过滤")
    welding_process: Optional[str] = Field(None, description="焊接工艺过滤")
    base_material_group: Optional[str] = Field(None, description="母材组号过滤")
    company: Optional[str] = Field(None, description="公司过滤")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    owner_id: Optional[int] = Field(None, description="所有者ID过滤")
    skip: int = Field(default=0, ge=0, description="跳过记录数")
    limit: int = Field(default=100, ge=1, le=1000, description="返回记录数")
    sort_by: Optional[str] = Field(default="created_at", description="排序字段")
    sort_order: Optional[str] = Field(default="desc", description="排序方向")


class WPSStatusUpdate(BaseModel):
    """WPS status update schema."""
    status: str = Field(..., description="新状态")
    reason: Optional[str] = Field(None, description="状态变更原因")
    reviewed_by: Optional[int] = Field(None, description="审核人ID")
    approved_by: Optional[int] = Field(None, description="批准人ID")

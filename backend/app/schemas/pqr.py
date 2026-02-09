"""
PQR schemas for the welding system backend.
"""
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# 基础信息 schemas
class PQRBase(BaseModel):
    """Base PQR schema."""
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    pqr_number: str = Field(..., min_length=1, max_length=50, description="PQR编号")
    wps_number: Optional[str] = Field(None, max_length=50, description="对应的WPS编号")
    test_date: Optional[datetime] = Field(None, description="试验日期")
    company: Optional[str] = Field(None, max_length=100, description="公司名称")
    project_name: Optional[str] = Field(None, max_length=100, description="项目名称")
    test_location: Optional[str] = Field(None, max_length=100, description="试验地点")
    welding_operator: Optional[str] = Field(None, max_length=100, description="焊工姓名和编号")

    # 焊接工艺参数
    welding_process: Optional[str] = Field(None, max_length=50, description="焊接工艺")
    process_type: Optional[str] = Field(None, max_length=20, description="工艺类型")
    process_specification: Optional[str] = Field(None, max_length=50, description="工艺规范")

    # 母材信息
    base_material_group: Optional[str] = Field(None, max_length=50, description="母材组号")
    base_material_spec: Optional[str] = Field(None, max_length=50, description="母材规格")
    base_material_thickness: Optional[float] = Field(None, gt=0, description="母材实际厚度")
    base_material_heat_number: Optional[str] = Field(None, max_length=50, description="母材炉号")

    # 填充金属信息
    filler_material_spec: Optional[str] = Field(None, max_length=50, description="填充金属规格")
    filler_material_classification: Optional[str] = Field(None, max_length=50, description="填充金属分类")
    filler_material_diameter: Optional[float] = Field(None, gt=0, description="填充金属直径")
    filler_material_heat_number: Optional[str] = Field(None, max_length=50, description="填充金属炉号")

    # 保护气体信息
    shielding_gas: Optional[str] = Field(None, max_length=50, description="保护气体")
    gas_flow_rate: Optional[float] = Field(None, gt=0, description="实际气体流量")
    gas_composition: Optional[str] = Field(None, max_length=50, description="气体成分")

    # 电流参数（实际值）
    current_type: Optional[str] = Field(None, max_length=10, description="电流类型")
    current_polarity: Optional[str] = Field(None, max_length=10, description="电极极性")
    current_actual: Optional[float] = Field(None, gt=0, description="实际电流")
    voltage_actual: Optional[float] = Field(None, gt=0, description="实际电压")

    # 速度参数（实际值）
    wire_feed_speed_actual: Optional[float] = Field(None, ge=0, description="实际送丝速度")
    welding_speed_actual: Optional[float] = Field(None, ge=0, description="实际焊接速度")
    travel_speed_actual: Optional[float] = Field(None, ge=0, description="实际行走速度")

    # 热输入计算
    heat_input_calculated: Optional[float] = Field(None, ge=0, description="计算热输入")
    heat_input_range_min: Optional[float] = Field(None, ge=0, description="热输入范围最小值")
    heat_input_range_max: Optional[float] = Field(None, ge=0, description="热输入范围最大值")

    # 焊道和焊层信息
    weld_passes_actual: Optional[int] = Field(None, ge=1, description="实际焊道数量")
    weld_layer_actual: Optional[int] = Field(None, ge=1, description="实际焊层数量")

    # 坡口设计信息
    joint_design: Optional[str] = Field(None, max_length=50, description="接头设计")
    groove_type: Optional[str] = Field(None, max_length=50, description="坡口类型")
    groove_angle_actual: Optional[float] = Field(None, ge=0, le=180, description="实际坡口角度")
    root_gap_actual: Optional[float] = Field(None, ge=0, description="实际根部间隙")
    root_face_actual: Optional[float] = Field(None, ge=0, description="实际根部钝边")

    # 预热和层间温度（实际值）
    preheat_temp_actual: Optional[float] = Field(None, ge=-273.15, description="实际预热温度")
    interpass_temp_max_actual: Optional[float] = Field(None, ge=-273.15, description="实际最高层间温度")
    ambient_temperature: Optional[float] = Field(None, ge=-273.15, description="环境温度")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="湿度")

    # 焊后热处理（实际值）
    pwht_performed: Optional[bool] = Field(False, description="是否进行了焊后热处理")
    pwht_temperature_actual: Optional[float] = Field(None, ge=-273.15, description="实际焊后热处理温度")
    pwht_time_actual: Optional[float] = Field(None, gt=0, description="实际焊后热处理时间")
    pwht_method: Optional[str] = Field(None, max_length=50, description="热处理方法")

    # 无损检测结果
    visual_inspection_result: Optional[str] = Field(None, max_length=20, description="目视检测结果")
    rt_result: Optional[str] = Field(None, max_length=20, description="射线检测结果")
    ut_result: Optional[str] = Field(None, max_length=20, description="超声检测结果")
    mt_result: Optional[str] = Field(None, max_length=20, description="磁粉检测结果")
    pt_result: Optional[str] = Field(None, max_length=20, description="渗透检测结果")
    ndt_report_number: Optional[str] = Field(None, max_length=50, description="无损检测报告编号")

    # 力学性能测试结果
    tensile_test_result: Optional[str] = Field(None, max_length=20, description="拉伸测试结果")
    tensile_strength_actual: Optional[float] = Field(None, ge=0, description="实际抗拉强度")
    tensile_yield_strength: Optional[float] = Field(None, ge=0, description="屈服强度")
    tensile_elongation: Optional[float] = Field(None, ge=0, le=100, description="延伸率")

    # 弯曲测试结果
    root_bend_result: Optional[str] = Field(None, max_length=20, description="根部弯曲结果")
    face_bend_result: Optional[str] = Field(None, max_length=20, description="表面弯曲结果")
    side_bend_result: Optional[str] = Field(None, max_length=20, description="侧面弯曲结果")
    bend_angle: Optional[float] = Field(None, ge=0, le=180, description="弯曲角度")
    bend_radius: Optional[float] = Field(None, gt=0, description="弯曲半径")

    # 冲击测试结果
    charpy_test_performed: Optional[bool] = Field(False, description="是否进行了冲击测试")
    charpy_test_temp: Optional[float] = Field(None, description="冲击试验温度")
    charpy_energy_avg: Optional[float] = Field(None, ge=0, description="平均冲击功")
    charpy_energy_min: Optional[float] = Field(None, ge=0, description="最小冲击功")
    charpy_lateral_expansion: Optional[float] = Field(None, ge=0, description="侧向膨胀")

    # 硬度测试结果
    hardness_test_performed: Optional[bool] = Field(False, description="是否进行了硬度测试")
    hardness_values: Optional[str] = Field(None, description="硬度值列表")

    # 金相检验结果
    metallography_performed: Optional[bool] = Field(False, description="是否进行了金相检验")
    metallography_results: Optional[str] = Field(None, description="金相检验结果")

    # 腐蚀测试结果
    corrosion_test_performed: Optional[bool] = Field(False, description="是否进行了腐蚀测试")
    corrosion_test_results: Optional[str] = Field(None, description="腐蚀测试结果")

    # 有效范围
    thickness_range_qualified: Optional[str] = Field(None, max_length=50, description="合格的厚度范围")
    diameter_range_qualified: Optional[str] = Field(None, max_length=50, description="合格的直径范围")
    position_qualified: Optional[str] = Field(None, max_length=100, description="合格的焊接位置")
    filler_material_range: Optional[str] = Field(None, max_length=100, description="合格的填充材料范围")

    # 附加信息
    test_notes: Optional[str] = Field(None, description="试验备注")
    deviation_notes: Optional[str] = Field(None, description="偏离说明")
    recommendations: Optional[str] = Field(None, description="建议")
    test_reports: Optional[str] = Field(None, description="试验报告文件路径")
    attachments: Optional[str] = Field(None, description="附件文件路径")


class PQRCreate(PQRBase):
    """PQR creation schema."""
    qualification_result: Optional[str] = Field(None, max_length=20, description="评定结果")
    qualification_date: Optional[datetime] = Field(None, description="评定日期")
    qualified_by: Optional[int] = Field(None, description="评定人ID")

    # 模块化数据支持
    template_id: Optional[str] = Field(None, description="模板ID")
    modules_data: Optional[dict] = Field(None, description="模块化数据")


class PQRUpdate(BaseModel):
    """PQR update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="标题")
    pqr_number: Optional[str] = Field(None, min_length=1, max_length=50, description="PQR编号")
    wps_number: Optional[str] = Field(None, max_length=50, description="对应的WPS编号")
    test_date: Optional[datetime] = Field(None, description="试验日期")
    company: Optional[str] = Field(None, max_length=100, description="公司名称")
    project_name: Optional[str] = Field(None, max_length=100, description="项目名称")
    test_location: Optional[str] = Field(None, max_length=100, description="试验地点")
    welding_operator: Optional[str] = Field(None, max_length=100, description="焊工姓名和编号")

    # 焊接工艺参数
    welding_process: Optional[str] = Field(None, max_length=50, description="焊接工艺")
    process_type: Optional[str] = Field(None, max_length=20, description="工艺类型")
    process_specification: Optional[str] = Field(None, max_length=50, description="工艺规范")

    # 母材信息
    base_material_group: Optional[str] = Field(None, max_length=50, description="母材组号")
    base_material_spec: Optional[str] = Field(None, max_length=50, description="母材规格")
    base_material_thickness: Optional[float] = Field(None, gt=0, description="母材实际厚度")
    base_material_heat_number: Optional[str] = Field(None, max_length=50, description="母材炉号")

    # 填充金属信息
    filler_material_spec: Optional[str] = Field(None, max_length=50, description="填充金属规格")
    filler_material_classification: Optional[str] = Field(None, max_length=50, description="填充金属分类")
    filler_material_diameter: Optional[float] = Field(None, gt=0, description="填充金属直径")
    filler_material_heat_number: Optional[str] = Field(None, max_length=50, description="填充金属炉号")

    # 保护气体信息
    shielding_gas: Optional[str] = Field(None, max_length=50, description="保护气体")
    gas_flow_rate: Optional[float] = Field(None, gt=0, description="实际气体流量")
    gas_composition: Optional[str] = Field(None, max_length=50, description="气体成分")

    # 电流参数（实际值）
    current_type: Optional[str] = Field(None, max_length=10, description="电流类型")
    current_polarity: Optional[str] = Field(None, max_length=10, description="电极极性")
    current_actual: Optional[float] = Field(None, gt=0, description="实际电流")
    voltage_actual: Optional[float] = Field(None, gt=0, description="实际电压")

    # 速度参数（实际值）
    wire_feed_speed_actual: Optional[float] = Field(None, ge=0, description="实际送丝速度")
    welding_speed_actual: Optional[float] = Field(None, ge=0, description="实际焊接速度")
    travel_speed_actual: Optional[float] = Field(None, ge=0, description="实际行走速度")

    # 热输入计算
    heat_input_calculated: Optional[float] = Field(None, ge=0, description="计算热输入")
    heat_input_range_min: Optional[float] = Field(None, ge=0, description="热输入范围最小值")
    heat_input_range_max: Optional[float] = Field(None, ge=0, description="热输入范围最大值")

    # 焊道和焊层信息
    weld_passes_actual: Optional[int] = Field(None, ge=1, description="实际焊道数量")
    weld_layer_actual: Optional[int] = Field(None, ge=1, description="实际焊层数量")

    # 坡口设计信息
    joint_design: Optional[str] = Field(None, max_length=50, description="接头设计")
    groove_type: Optional[str] = Field(None, max_length=50, description="坡口类型")
    groove_angle_actual: Optional[float] = Field(None, ge=0, le=180, description="实际坡口角度")
    root_gap_actual: Optional[float] = Field(None, ge=0, description="实际根部间隙")
    root_face_actual: Optional[float] = Field(None, ge=0, description="实际根部钝边")

    # 预热和层间温度（实际值）
    preheat_temp_actual: Optional[float] = Field(None, ge=-273.15, description="实际预热温度")
    interpass_temp_max_actual: Optional[float] = Field(None, ge=-273.15, description="实际最高层间温度")
    ambient_temperature: Optional[float] = Field(None, ge=-273.15, description="环境温度")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="湿度")

    # 焊后热处理（实际值）
    pwht_performed: Optional[bool] = Field(None, description="是否进行了焊后热处理")
    pwht_temperature_actual: Optional[float] = Field(None, ge=-273.15, description="实际焊后热处理温度")
    pwht_time_actual: Optional[float] = Field(None, gt=0, description="实际焊后热处理时间")
    pwht_method: Optional[str] = Field(None, max_length=50, description="热处理方法")

    # 无损检测结果
    visual_inspection_result: Optional[str] = Field(None, max_length=20, description="目视检测结果")
    rt_result: Optional[str] = Field(None, max_length=20, description="射线检测结果")
    ut_result: Optional[str] = Field(None, max_length=20, description="超声检测结果")
    mt_result: Optional[str] = Field(None, max_length=20, description="磁粉检测结果")
    pt_result: Optional[str] = Field(None, max_length=20, description="渗透检测结果")
    ndt_report_number: Optional[str] = Field(None, max_length=50, description="无损检测报告编号")

    # 力学性能测试结果
    tensile_test_result: Optional[str] = Field(None, max_length=20, description="拉伸测试结果")
    tensile_strength_actual: Optional[float] = Field(None, ge=0, description="实际抗拉强度")
    tensile_yield_strength: Optional[float] = Field(None, ge=0, description="屈服强度")
    tensile_elongation: Optional[float] = Field(None, ge=0, le=100, description="延伸率")

    # 弯曲测试结果
    root_bend_result: Optional[str] = Field(None, max_length=20, description="根部弯曲结果")
    face_bend_result: Optional[str] = Field(None, max_length=20, description="表面弯曲结果")
    side_bend_result: Optional[str] = Field(None, max_length=20, description="侧面弯曲结果")
    bend_angle: Optional[float] = Field(None, ge=0, le=180, description="弯曲角度")
    bend_radius: Optional[float] = Field(None, gt=0, description="弯曲半径")

    # 冲击测试结果
    charpy_test_performed: Optional[bool] = Field(None, description="是否进行了冲击测试")
    charpy_test_temp: Optional[float] = Field(None, description="冲击试验温度")
    charpy_energy_avg: Optional[float] = Field(None, ge=0, description="平均冲击功")
    charpy_energy_min: Optional[float] = Field(None, ge=0, description="最小冲击功")
    charpy_lateral_expansion: Optional[float] = Field(None, ge=0, description="侧向膨胀")

    # 硬度测试结果
    hardness_test_performed: Optional[bool] = Field(None, description="是否进行了硬度测试")
    hardness_values: Optional[str] = Field(None, description="硬度值列表")

    # 金相检验结果
    metallography_performed: Optional[bool] = Field(None, description="是否进行了金相检验")
    metallography_results: Optional[str] = Field(None, description="金相检验结果")

    # 腐蚀测试结果
    corrosion_test_performed: Optional[bool] = Field(None, description="是否进行了腐蚀测试")
    corrosion_test_results: Optional[str] = Field(None, description="腐蚀测试结果")

    # 总体评定结果
    qualification_result: Optional[str] = Field(None, max_length=20, description="评定结果")
    qualification_date: Optional[datetime] = Field(None, description="评定日期")
    qualified_by: Optional[int] = Field(None, description="评定人ID")

    # 有效范围
    thickness_range_qualified: Optional[str] = Field(None, max_length=50, description="合格的厚度范围")
    diameter_range_qualified: Optional[str] = Field(None, max_length=50, description="合格的直径范围")
    position_qualified: Optional[str] = Field(None, max_length=100, description="合格的焊接位置")
    filler_material_range: Optional[str] = Field(None, max_length=100, description="合格的填充材料范围")

    # 附加信息
    test_notes: Optional[str] = Field(None, description="试验备注")
    deviation_notes: Optional[str] = Field(None, description="偏离说明")
    recommendations: Optional[str] = Field(None, description="建议")
    test_reports: Optional[str] = Field(None, description="试验报告文件路径")
    attachments: Optional[str] = Field(None, description="附件文件路径")

    # 模块化数据支持
    template_id: Optional[str] = Field(None, description="模板ID")
    modules_data: Optional[dict] = Field(None, description="模块化数据")

    # 文档编辑模式
    document_html: Optional[str] = Field(None, description="文档HTML内容（用于文档编辑模式）")
    status: Optional[str] = Field(None, description="状态")


class PQRResponse(PQRBase):
    """PQR response schema."""
    id: int
    owner_id: int
    qualification_result: Optional[str] = Field(default="pending", description="评定结果")
    qualification_date: Optional[datetime] = None
    qualified_by: Optional[int] = None
    status: Optional[str] = Field(default="draft", description="状态")
    template_id: Optional[str] = Field(None, description="模板ID")
    modules_data: Optional[dict] = Field(None, description="模块化数据")
    created_at: datetime
    updated_at: datetime
    is_active: bool
    # 审批相关字段
    approval_instance_id: Optional[int] = None
    approval_status: Optional[str] = None
    workflow_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PQRSummary(BaseModel):
    """PQR summary for list views."""
    id: int
    title: str
    pqr_number: str
    wps_number: Optional[str] = None
    test_date: Optional[datetime] = None
    company: Optional[str] = None
    welding_process: Optional[str] = None
    base_material_spec: Optional[str] = None
    qualification_result: Optional[str] = None
    status: Optional[str] = Field(default="draft", description="状态")
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


class PQRListResponse(BaseModel):
    """PQR list response with pagination."""
    items: List[PQRSummary] = Field(..., description="PQR列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")


# PQR试样信息 schemas
class PQRTestSpecimenBase(BaseModel):
    """Base PQR test specimen schema."""
    specimen_type: str = Field(..., max_length=50, description="试样类型")
    specimen_number: Optional[str] = Field(None, max_length=20, description="试样编号")
    specimen_location: Optional[str] = Field(None, max_length=50, description="取样位置")
    specimen_dimensions: Optional[str] = Field(None, description="试样尺寸")
    test_result: Optional[str] = Field(None, max_length=20, description="测试结果")
    test_value: Optional[float] = Field(None, description="测试值")
    test_unit: Optional[str] = Field(None, max_length=20, description="测试单位")
    test_temperature: Optional[float] = Field(None, description="试验温度")
    test_speed: Optional[float] = Field(None, description="试验速度")
    failure_mode: Optional[str] = Field(None, max_length=50, description="失效模式")
    failure_location: Optional[str] = Field(None, max_length=50, description="失效位置")
    specimen_notes: Optional[str] = Field(None, description="试样备注")


class PQRTestSpecimenCreate(PQRTestSpecimenBase):
    """PQR test specimen creation schema."""
    pqr_id: int = Field(..., description="PQR ID")


class PQRTestSpecimenResponse(PQRTestSpecimenBase):
    """PQR test specimen response schema."""
    id: int
    pqr_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PQRExportRequest(BaseModel):
    """PQR export request schema."""
    pqr_ids: List[int] = Field(..., description="要导出的PQR ID列表")
    export_format: str = Field(default="pdf", description="导出格式: pdf, docx, excel")
    include_specimens: bool = Field(default=False, description="是否包含试样信息")
    include_attachments: bool = Field(default=False, description="是否包含附件")


class PQRSearchParams(BaseModel):
    """PQR search parameters schema."""
    search_term: Optional[str] = Field(None, description="搜索关键词")
    qualification_result: Optional[str] = Field(None, description="评定结果过滤")
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


class PQRQualificationUpdate(BaseModel):
    """PQR qualification update schema."""
    qualification_result: str = Field(..., max_length=20, description="评定结果")
    qualification_date: datetime = Field(..., description="评定日期")
    qualified_by: int = Field(..., description="评定人ID")
    thickness_range_qualified: Optional[str] = Field(None, max_length=50, description="合格的厚度范围")
    diameter_range_qualified: Optional[str] = Field(None, max_length=50, description="合格的直径范围")
    position_qualified: Optional[str] = Field(None, max_length=100, description="合格的焊接位置")
    filler_material_range: Optional[str] = Field(None, max_length=100, description="合格的填充材料范围")
    recommendations: Optional[str] = Field(None, description="建议")
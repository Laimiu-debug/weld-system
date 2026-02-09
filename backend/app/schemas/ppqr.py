"""
pPQR schemas for the welding system backend.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field


# 基础信息 schemas
class PPQRBase(BaseModel):
    """Base pPQR schema."""
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    ppqr_number: str = Field(..., min_length=1, max_length=50, description="pPQR编号")
    revision: str = Field(default="A", max_length=10, description="版本号")
    status: str = Field(default="draft", max_length=20, description="状态: draft, testing, completed, converted")
    
    # 模板和模块数据
    template_id: Optional[str] = Field(None, max_length=100, description="使用的模板ID")
    module_data: Optional[Dict[str, Any]] = Field(None, description="模块数据(JSON)")
    
    # 基本信息
    test_date: Optional[date] = Field(None, description="试验日期")
    test_purpose: Optional[str] = Field(None, description="试验目的")
    reference_standard: Optional[str] = Field(None, max_length=100, description="参考标准")
    welding_process: Optional[str] = Field(None, max_length=50, description="焊接工艺")
    welder_name: Optional[str] = Field(None, max_length=100, description="焊工姓名")
    project_name: Optional[str] = Field(None, max_length=100, description="项目名称")
    
    # 试验方案
    test_variables: Optional[str] = Field(None, description="试验变量")
    number_of_specimens: Optional[int] = Field(None, ge=0, description="试样数量")
    test_matrix: Optional[str] = Field(None, description="试验矩阵")
    expected_outcome: Optional[str] = Field(None, description="预期结果")
    risk_assessment: Optional[str] = Field(None, description="风险评估")
    
    # 材料信息
    base_material_spec: Optional[str] = Field(None, max_length=100, description="母材规格")
    base_material_grade: Optional[str] = Field(None, max_length=50, description="母材牌号")
    thickness: Optional[float] = Field(None, ge=0, description="厚度")
    filler_metal_spec: Optional[str] = Field(None, max_length=100, description="填充金属规格")
    filler_metal_classification: Optional[str] = Field(None, max_length=100, description="填充金属分类")
    diameter: Optional[float] = Field(None, ge=0, description="直径")
    shielding_gas: Optional[str] = Field(None, max_length=100, description="保护气体")
    batch_number: Optional[str] = Field(None, max_length=50, description="批号")
    
    # 参数对比分析
    best_group: Optional[str] = Field(None, max_length=50, description="最佳参数组")
    best_group_reason: Optional[str] = Field(None, description="最佳参数组原因")
    heat_input_analysis: Optional[str] = Field(None, description="热输入分析")
    quality_comparison: Optional[str] = Field(None, description="质量对比")
    efficiency_analysis: Optional[str] = Field(None, description="效率分析")
    recommended_parameters: Optional[str] = Field(None, description="推荐参数")
    
    # 试验评价
    test_conclusion: Optional[str] = Field(None, max_length=50, description="试验结论")
    objectives_achieved: Optional[str] = Field(None, description="目标达成情况")
    lessons_learned: Optional[str] = Field(None, description="经验教训")
    next_steps: Optional[str] = Field(None, description="下一步计划")
    convert_to_pqr: Optional[str] = Field(None, max_length=20, description="是否转换为PQR: yes/no/pending")
    target_pqr_number: Optional[str] = Field(None, max_length=50, description="目标PQR编号")
    evaluated_by: Optional[str] = Field(None, max_length=100, description="评估人")
    evaluation_date: Optional[date] = Field(None, description="评估日期")
    
    # 备注
    notes: Optional[str] = Field(None, description="备注")
    remarks: Optional[str] = Field(None, description="说明")


class PPQRCreate(PPQRBase):
    """pPQR creation schema."""
    pass


class PPQRUpdate(BaseModel):
    """pPQR update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="标题")
    ppqr_number: Optional[str] = Field(None, min_length=1, max_length=50, description="pPQR编号")
    revision: Optional[str] = Field(None, max_length=10, description="版本号")
    status: Optional[str] = Field(None, max_length=20, description="状态")
    template_id: Optional[str] = Field(None, max_length=100, description="使用的模板ID")
    module_data: Optional[Dict[str, Any]] = Field(None, description="模块数据(JSON)")
    test_date: Optional[date] = Field(None, description="试验日期")
    test_purpose: Optional[str] = Field(None, description="试验目的")
    reference_standard: Optional[str] = Field(None, max_length=100, description="参考标准")
    welding_process: Optional[str] = Field(None, max_length=50, description="焊接工艺")
    welder_name: Optional[str] = Field(None, max_length=100, description="焊工姓名")
    project_name: Optional[str] = Field(None, max_length=100, description="项目名称")
    test_variables: Optional[str] = Field(None, description="试验变量")
    number_of_specimens: Optional[int] = Field(None, ge=0, description="试样数量")
    test_matrix: Optional[str] = Field(None, description="试验矩阵")
    expected_outcome: Optional[str] = Field(None, description="预期结果")
    risk_assessment: Optional[str] = Field(None, description="风险评估")
    base_material_spec: Optional[str] = Field(None, max_length=100, description="母材规格")
    base_material_grade: Optional[str] = Field(None, max_length=50, description="母材牌号")
    thickness: Optional[float] = Field(None, ge=0, description="厚度")
    filler_metal_spec: Optional[str] = Field(None, max_length=100, description="填充金属规格")
    filler_metal_classification: Optional[str] = Field(None, max_length=100, description="填充金属分类")
    diameter: Optional[float] = Field(None, ge=0, description="直径")
    shielding_gas: Optional[str] = Field(None, max_length=100, description="保护气体")
    batch_number: Optional[str] = Field(None, max_length=50, description="批号")
    best_group: Optional[str] = Field(None, max_length=50, description="最佳参数组")
    best_group_reason: Optional[str] = Field(None, description="最佳参数组原因")
    heat_input_analysis: Optional[str] = Field(None, description="热输入分析")
    quality_comparison: Optional[str] = Field(None, description="质量对比")
    efficiency_analysis: Optional[str] = Field(None, description="效率分析")
    recommended_parameters: Optional[str] = Field(None, description="推荐参数")
    test_conclusion: Optional[str] = Field(None, max_length=50, description="试验结论")
    objectives_achieved: Optional[str] = Field(None, description="目标达成情况")
    lessons_learned: Optional[str] = Field(None, description="经验教训")
    next_steps: Optional[str] = Field(None, description="下一步计划")
    convert_to_pqr: Optional[str] = Field(None, max_length=20, description="是否转换为PQR")
    target_pqr_number: Optional[str] = Field(None, max_length=50, description="目标PQR编号")
    evaluated_by: Optional[str] = Field(None, max_length=100, description="评估人")
    evaluation_date: Optional[date] = Field(None, description="评估日期")
    notes: Optional[str] = Field(None, description="备注")
    remarks: Optional[str] = Field(None, description="说明")
    reviewed_by: Optional[int] = Field(None, description="审核人ID")
    approved_by: Optional[int] = Field(None, description="批准人ID")

    # 文档编辑模式
    document_html: Optional[str] = Field(None, description="文档HTML内容（用于文档编辑模式）")


class PPQRResponse(PPQRBase):
    """pPQR response schema."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    reviewed_by: Optional[int] = None
    reviewed_date: Optional[datetime] = None
    approved_by: Optional[int] = None
    approved_date: Optional[datetime] = None
    is_active: bool = True
    # 审批相关字段
    approval_instance_id: Optional[int] = None
    approval_status: Optional[str] = None
    workflow_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PPQRSummary(BaseModel):
    """pPQR summary for list views."""
    id: int
    title: str
    ppqr_number: str
    revision: str
    status: str
    test_date: Optional[date] = None
    test_conclusion: Optional[str] = None
    convert_to_pqr: Optional[str] = None
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


class PPQRListResponse(BaseModel):
    """pPQR list response with pagination."""
    items: List[PPQRSummary] = Field(..., description="pPQR列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")

    model_config = ConfigDict(from_attributes=True)


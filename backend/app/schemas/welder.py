"""
Welder Pydantic schemas for the welding system backend.
焊工管理 Pydantic Schema
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ==================== 基础Schema ====================

class WelderBase(BaseModel):
    """焊工基础Schema"""
    welder_code: str = Field(..., description="焊工编号")
    full_name: str = Field(..., description="姓名")
    english_name: Optional[str] = Field(None, description="英文名")
    gender: Optional[str] = Field(None, description="性别")
    date_of_birth: Optional[date] = Field(None, description="出生日期")
    
    # 身份信息
    id_type: Optional[str] = Field(None, description="证件类型")
    id_number: Optional[str] = Field(None, description="证件号码")
    nationality: str = Field(default="中国", description="国籍")
    
    # 联系信息
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="地址")
    emergency_contact: Optional[str] = Field(None, description="紧急联系人")
    emergency_phone: Optional[str] = Field(None, description="紧急联系电话")
    
    # 雇佣信息
    hire_date: Optional[date] = Field(None, description="入职日期")
    department: Optional[str] = Field(None, description="部门")
    position: Optional[str] = Field(None, description="职位")
    
    # 技能等级
    skill_level: Optional[str] = Field(None, description="技能等级")
    specialization: Optional[str] = Field(None, description="专业方向")
    qualified_processes: Optional[str] = Field(None, description="合格的焊接工艺(JSON)")
    qualified_positions: Optional[str] = Field(None, description="合格的焊接位置(JSON)")
    qualified_materials: Optional[str] = Field(None, description="合格的材料(JSON)")
    
    # 主要证书信息
    primary_certification_number: Optional[str] = Field(None, description="主要证书编号")
    primary_certification_level: Optional[str] = Field(None, description="主要证书等级")
    primary_certification_date: Optional[date] = Field(None, description="主要证书颁发日期")
    primary_expiry_date: Optional[date] = Field(None, description="主要证书过期日期")
    primary_issuing_authority: Optional[str] = Field(None, description="主要证书颁发机构")
    
    # 状态信息
    status: str = Field(default="active", description="状态")
    certification_status: str = Field(default="valid", description="证书状态")
    
    # 绩效统计
    total_tasks_completed: int = Field(default=0, description="完成任务数")
    total_weld_length: float = Field(default=0, description="累计焊接长度(m)")
    total_work_hours: float = Field(default=0, description="累计工时(h)")
    quality_score: Optional[float] = Field(None, description="质量评分")
    efficiency_score: Optional[float] = Field(None, description="效率评分")
    safety_score: Optional[float] = Field(None, description="安全评分")
    
    # 培训信息
    last_training_date: Optional[date] = Field(None, description="最后培训日期")
    next_training_date: Optional[date] = Field(None, description="下次培训日期")
    training_hours: float = Field(default=0, description="培训时长(h)")
    
    # 健康信息
    last_health_check_date: Optional[date] = Field(None, description="最后体检日期")
    next_health_check_date: Optional[date] = Field(None, description="下次体检日期")
    health_status: Optional[str] = Field(None, description="健康状态")
    medical_restrictions: Optional[str] = Field(None, description="医疗限制")
    
    # 附加信息
    photo_url: Optional[str] = Field(None, description="照片URL")
    description: Optional[str] = Field(None, description="描述")
    notes: Optional[str] = Field(None, description="备注")
    documents: Optional[str] = Field(None, description="相关文档(JSON)")
    tags: Optional[str] = Field(None, description="标签")


# ==================== 创建Schema ====================

class WelderCreate(WelderBase):
    """创建焊工Schema"""
    pass


# ==================== 更新Schema ====================

class WelderUpdate(BaseModel):
    """更新焊工Schema"""
    welder_code: Optional[str] = None
    full_name: Optional[str] = None
    english_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    nationality: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    hire_date: Optional[date] = None
    department: Optional[str] = None
    position: Optional[str] = None
    skill_level: Optional[str] = None
    specialization: Optional[str] = None
    qualified_processes: Optional[str] = None
    qualified_positions: Optional[str] = None
    qualified_materials: Optional[str] = None
    primary_certification_number: Optional[str] = None
    primary_certification_level: Optional[str] = None
    primary_certification_date: Optional[date] = None
    primary_expiry_date: Optional[date] = None
    primary_issuing_authority: Optional[str] = None
    status: Optional[str] = None
    certification_status: Optional[str] = None
    total_tasks_completed: Optional[int] = None
    total_weld_length: Optional[float] = None
    total_work_hours: Optional[float] = None
    quality_score: Optional[float] = None
    efficiency_score: Optional[float] = None
    safety_score: Optional[float] = None
    last_training_date: Optional[date] = None
    next_training_date: Optional[date] = None
    training_hours: Optional[float] = None
    last_health_check_date: Optional[date] = None
    next_health_check_date: Optional[date] = None
    health_status: Optional[str] = None
    medical_restrictions: Optional[str] = None
    photo_url: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    documents: Optional[str] = None
    tags: Optional[str] = None


# ==================== 响应Schema ====================

class WelderResponse(WelderBase):
    """焊工响应Schema"""
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
    
    model_config = ConfigDict(from_attributes=True)


# ==================== 列表响应Schema ====================

class WelderListResponse(BaseModel):
    """焊工列表响应Schema"""
    items: List[WelderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== 证书Schema ====================

class WelderCertificationBase(BaseModel):
    """焊工证书基础Schema"""
    # 证书基本信息
    certification_number: str = Field(..., description="证书编号")
    certification_type: str = Field(..., description="证书类型")
    certification_level: Optional[str] = Field(None, description="证书等级")
    certification_standard: Optional[str] = Field(None, description="认证标准")
    certification_system: Optional[str] = Field(None, description="认证体系")
    project_name: Optional[str] = Field(None, description="项目名称")

    # 颁发信息
    issuing_authority: Optional[str] = Field(None, description="颁发机构")
    issuing_country: Optional[str] = Field(None, description="颁发国家")
    issue_date: Optional[date] = Field(None, description="颁发日期")
    expiry_date: Optional[date] = Field(None, description="过期日期")

    # 合格项目 - JSON格式存储表格数据
    # 格式：[{"item": "GTAW-FeIV-6G-3/159-FefS-02/10/12", "description": "氩弧焊-碳钢-全位置", "notes": ""}, ...]
    qualified_items: Optional[str] = Field(None, description="合格项目列表（JSON格式）")

    # 合格范围 - JSON格式存储表格数据
    # 格式：[{"name": "母材", "value": "Q345R", "notes": ""}, {"name": "焊接位置", "value": "1G,2G,3G,4G,5G,6G", "notes": ""}, ...]
    qualified_range: Optional[str] = Field(None, description="合格范围列表（JSON格式）")

    # 考试信息
    exam_date: Optional[date] = Field(None, description="考试日期")
    exam_location: Optional[str] = Field(None, description="考试地点")
    exam_score: Optional[float] = Field(None, description="考试成绩")
    practical_test_result: Optional[str] = Field(None, description="实操测试结果")
    theory_test_result: Optional[str] = Field(None, description="理论测试结果")

    # 复审信息
    renewal_date: Optional[date] = Field(None, description="最近复审日期")
    renewal_count: Optional[int] = Field(default=0, description="复审次数")
    next_renewal_date: Optional[date] = Field(None, description="下次复审日期")
    renewal_result: Optional[str] = Field(None, description="复审结果")
    renewal_notes: Optional[str] = Field(None, description="复审备注")

    # 状态和附件
    status: str = Field(default="valid", description="状态")
    is_primary: bool = Field(default=False, description="是否主要证书")
    certificate_file_url: Optional[str] = Field(None, description="证书文件URL")
    attachments: Optional[str] = Field(None, description="附件(JSON)")
    notes: Optional[str] = Field(None, description="备注")


class WelderCertificationCreate(WelderCertificationBase):
    """创建焊工证书Schema"""
    pass


class WelderCertificationUpdate(BaseModel):
    """更新焊工证书Schema"""
    certification_number: Optional[str] = Field(None, description="证书编号")
    certification_type: Optional[str] = Field(None, description="证书类型")
    certification_level: Optional[str] = Field(None, description="证书等级")
    certification_standard: Optional[str] = Field(None, description="认证标准")
    certification_system: Optional[str] = Field(None, description="认证体系")
    project_name: Optional[str] = Field(None, description="项目名称")

    issuing_authority: Optional[str] = Field(None, description="颁发机构")
    issuing_country: Optional[str] = Field(None, description="颁发国家")
    issue_date: Optional[date] = Field(None, description="颁发日期")
    expiry_date: Optional[date] = Field(None, description="过期日期")

    qualified_process: Optional[str] = Field(None, description="合格工艺")
    qualified_material_group: Optional[str] = Field(None, description="合格材料组")
    qualified_filler_material: Optional[str] = Field(None, description="合格填充材料")
    qualified_thickness_range: Optional[str] = Field(None, description="合格厚度范围")
    qualified_diameter_range: Optional[str] = Field(None, description="合格直径范围")
    qualified_position: Optional[str] = Field(None, description="合格位置")

    exam_date: Optional[date] = Field(None, description="考试日期")
    exam_location: Optional[str] = Field(None, description="考试地点")
    exam_score: Optional[float] = Field(None, description="考试成绩")
    practical_test_result: Optional[str] = Field(None, description="实操测试结果")
    theory_test_result: Optional[str] = Field(None, description="理论测试结果")

    renewal_date: Optional[date] = Field(None, description="最近复审日期")
    renewal_count: Optional[int] = Field(None, description="复审次数")
    next_renewal_date: Optional[date] = Field(None, description="下次复审日期")
    renewal_result: Optional[str] = Field(None, description="复审结果")
    renewal_notes: Optional[str] = Field(None, description="复审备注")

    status: Optional[str] = Field(None, description="状态")
    is_primary: Optional[bool] = Field(None, description="是否主要证书")
    certificate_file_url: Optional[str] = Field(None, description="证书文件URL")
    attachments: Optional[str] = Field(None, description="附件(JSON)")
    notes: Optional[str] = Field(None, description="备注")


class WelderCertificationResponse(WelderCertificationBase):
    """焊工证书响应Schema"""
    id: int
    welder_id: int
    user_id: int
    company_id: Optional[int] = None
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ==================== 统计Schema ====================

class WelderStatistics(BaseModel):
    """焊工统计Schema"""
    total_welders: int = Field(..., description="焊工总数")
    active_welders: int = Field(..., description="在职焊工数")
    inactive_welders: int = Field(..., description="离职焊工数")
    certifications_expiring_soon: int = Field(..., description="即将过期证书数")
    certifications_expired: int = Field(..., description="已过期证书数")


# ==================== 工作经历 Schema ====================

class WelderWorkRecordBase(BaseModel):
    """焊工工作记录基础Schema"""
    work_date: date = Field(..., description="工作日期")
    work_shift: Optional[str] = Field(None, description="班次")
    work_hours: Optional[float] = Field(None, description="工时(h)")

    # 焊接信息
    welding_process: Optional[str] = Field(None, description="焊接工艺")
    welding_position: Optional[str] = Field(None, description="焊接位置")
    base_material: Optional[str] = Field(None, description="母材")
    filler_material: Optional[str] = Field(None, description="填充材料")
    weld_length: Optional[float] = Field(None, description="焊接长度(m)")
    weld_weight: Optional[float] = Field(None, description="焊接重量(kg)")

    # 质量信息
    quality_result: Optional[str] = Field(None, description="质量结果")
    defect_count: Optional[int] = Field(default=0, description="缺陷数量")
    rework_count: Optional[int] = Field(default=0, description="返工次数")

    # 关联业务
    production_task_id: Optional[int] = Field(None, description="生产任务ID")
    wps_id: Optional[int] = Field(None, description="WPS ID")

    # 附加信息
    notes: Optional[str] = Field(None, description="备注")


class WelderWorkRecordCreate(WelderWorkRecordBase):
    """创建焊工工作记录Schema"""
    pass


class WelderWorkRecordUpdate(BaseModel):
    """更新焊工工作记录Schema"""
    work_date: Optional[date] = None
    work_shift: Optional[str] = None
    work_hours: Optional[float] = None
    welding_process: Optional[str] = None
    welding_position: Optional[str] = None
    base_material: Optional[str] = None
    filler_material: Optional[str] = None
    weld_length: Optional[float] = None
    weld_weight: Optional[float] = None
    quality_result: Optional[str] = None
    defect_count: Optional[int] = None
    rework_count: Optional[int] = None
    production_task_id: Optional[int] = None
    wps_id: Optional[int] = None
    notes: Optional[str] = None


class WelderWorkRecordResponse(WelderWorkRecordBase):
    """焊工工作记录响应Schema"""
    id: int
    welder_id: int
    user_id: int
    company_id: Optional[int] = None
    factory_id: Optional[int] = None
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 培训记录 Schema ====================

class WelderTrainingBase(BaseModel):
    """焊工培训记录基础Schema"""
    training_code: Optional[str] = Field(None, description="培训编号")
    training_name: str = Field(..., description="培训名称")
    training_type: Optional[str] = Field(None, description="培训类型")
    training_category: Optional[str] = Field(None, description="培训类别")

    # 时间信息
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    duration_hours: Optional[float] = Field(None, description="培训时长(h)")

    # 培训机构
    training_organization: Optional[str] = Field(None, description="培训机构")
    trainer_name: Optional[str] = Field(None, description="培训师")
    training_location: Optional[str] = Field(None, description="培训地点")

    # 培训内容
    training_content: Optional[str] = Field(None, description="培训内容")
    training_objectives: Optional[str] = Field(None, description="培训目标")
    training_materials: Optional[str] = Field(None, description="培训材料(JSON)")

    # 考核信息
    assessment_method: Optional[str] = Field(None, description="考核方式")
    assessment_score: Optional[float] = Field(None, description="考核成绩")
    assessment_result: Optional[str] = Field(None, description="考核结果")
    pass_status: Optional[bool] = Field(None, description="是否通过")

    # 证书信息
    certificate_issued: Optional[bool] = Field(default=False, description="是否颁发证书")
    certificate_number: Optional[str] = Field(None, description="证书编号")
    certificate_file_url: Optional[str] = Field(None, description="证书文件URL")

    # 附加信息
    notes: Optional[str] = Field(None, description="备注")
    attachments: Optional[str] = Field(None, description="附件(JSON)")


class WelderTrainingCreate(WelderTrainingBase):
    """创建焊工培训记录Schema"""
    pass


class WelderTrainingUpdate(BaseModel):
    """更新焊工培训记录Schema"""
    training_code: Optional[str] = None
    training_name: Optional[str] = None
    training_type: Optional[str] = None
    training_category: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_hours: Optional[float] = None
    training_organization: Optional[str] = None
    trainer_name: Optional[str] = None
    training_location: Optional[str] = None
    training_content: Optional[str] = None
    training_objectives: Optional[str] = None
    training_materials: Optional[str] = None
    assessment_method: Optional[str] = None
    assessment_score: Optional[float] = None
    assessment_result: Optional[str] = None
    pass_status: Optional[bool] = None
    certificate_issued: Optional[bool] = None
    certificate_number: Optional[str] = None
    certificate_file_url: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[str] = None


class WelderTrainingResponse(WelderTrainingBase):
    """焊工培训记录响应Schema"""
    id: int
    welder_id: int
    user_id: int
    company_id: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 考核记录 Schema ====================

class WelderAssessmentBase(BaseModel):
    """焊工考核记录基础Schema"""
    assessment_code: Optional[str] = Field(None, description="考核编号")
    assessment_name: str = Field(..., description="考核名称")
    assessment_type: Optional[str] = Field(None, description="考核类型")
    assessment_category: Optional[str] = Field(None, description="考核类别")

    # 时间信息
    assessment_date: date = Field(..., description="考核日期")
    duration_minutes: Optional[int] = Field(None, description="考核时长(分钟)")

    # 考核内容
    assessment_content: Optional[str] = Field(None, description="考核内容")
    assessment_standards: Optional[str] = Field(None, description="考核标准")
    assessment_items: Optional[str] = Field(None, description="考核项目(JSON)")

    # 考核人员
    assessor_name: Optional[str] = Field(None, description="考核人")
    assessor_organization: Optional[str] = Field(None, description="考核机构")
    assessment_location: Optional[str] = Field(None, description="考核地点")

    # 考核成绩
    theory_score: Optional[float] = Field(None, description="理论成绩")
    practical_score: Optional[float] = Field(None, description="实操成绩")
    total_score: Optional[float] = Field(None, description="总成绩")
    pass_score: Optional[float] = Field(None, description="及格分数")

    # 考核结果
    assessment_result: Optional[str] = Field(None, description="考核结果")
    pass_status: Optional[bool] = Field(None, description="是否通过")
    grade_level: Optional[str] = Field(None, description="评定等级")

    # 证书信息
    certificate_issued: Optional[bool] = Field(default=False, description="是否颁发证书")
    certificate_number: Optional[str] = Field(None, description="证书编号")
    certificate_file_url: Optional[str] = Field(None, description="证书文件URL")

    # 附加信息
    notes: Optional[str] = Field(None, description="备注")
    attachments: Optional[str] = Field(None, description="附件(JSON)")


class WelderAssessmentCreate(WelderAssessmentBase):
    """创建焊工考核记录Schema"""
    pass


class WelderAssessmentUpdate(BaseModel):
    """更新焊工考核记录Schema"""
    assessment_code: Optional[str] = None
    assessment_name: Optional[str] = None
    assessment_type: Optional[str] = None
    assessment_category: Optional[str] = None
    assessment_date: Optional[date] = None
    duration_minutes: Optional[int] = None
    assessment_content: Optional[str] = None
    assessment_standards: Optional[str] = None
    assessment_items: Optional[str] = None
    assessor_name: Optional[str] = None
    assessor_organization: Optional[str] = None
    assessment_location: Optional[str] = None
    theory_score: Optional[float] = None
    practical_score: Optional[float] = None
    total_score: Optional[float] = None
    pass_score: Optional[float] = None
    assessment_result: Optional[str] = None
    pass_status: Optional[bool] = None
    grade_level: Optional[str] = None
    certificate_issued: Optional[bool] = None
    certificate_number: Optional[str] = None
    certificate_file_url: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[str] = None


class WelderAssessmentResponse(WelderAssessmentBase):
    """焊工考核记录响应Schema"""
    id: int
    welder_id: int
    user_id: int
    company_id: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 工作履历 Schema ====================

class WelderWorkHistoryBase(BaseModel):
    """焊工工作履历基础Schema"""
    company_name: str = Field(..., description="公司名称")
    position: str = Field(..., description="职位")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    department: Optional[str] = Field(None, description="部门")
    location: Optional[str] = Field(None, description="工作地点")
    job_description: Optional[str] = Field(None, description="工作内容")
    achievements: Optional[str] = Field(None, description="主要成就")
    leaving_reason: Optional[str] = Field(None, description="离职原因")


class WelderWorkHistoryCreate(WelderWorkHistoryBase):
    """创建焊工工作履历Schema"""
    pass


class WelderWorkHistoryUpdate(BaseModel):
    """更新焊工工作履历Schema"""
    company_name: Optional[str] = None
    position: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    department: Optional[str] = None
    location: Optional[str] = None
    job_description: Optional[str] = None
    achievements: Optional[str] = None
    leaving_reason: Optional[str] = None


class WelderWorkHistoryResponse(WelderWorkHistoryBase):
    """焊工工作履历响应Schema"""
    id: int
    welder_id: int
    user_id: int
    company_id: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

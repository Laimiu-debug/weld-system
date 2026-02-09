"""
Welder models for the welding system backend.
焊工管理数据模型
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class WelderStatus(str, enum.Enum):
    """焊工状态"""
    ACTIVE = "active"  # 在职
    INACTIVE = "inactive"  # 离职
    SUSPENDED = "suspended"  # 停职
    TRAINING = "training"  # 培训中


class CertificationStatus(str, enum.Enum):
    """证书状态"""
    VALID = "valid"  # 有效
    EXPIRED = "expired"  # 已过期
    EXPIRING_SOON = "expiring_soon"  # 即将过期
    SUSPENDED = "suspended"  # 暂停
    REVOKED = "revoked"  # 吊销


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


class Welder(Base):
    """焊工管理模型"""
    
    __tablename__ = "welders"
    
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
    welder_code = Column(String(100), nullable=False, index=True, comment="焊工编号")
    full_name = Column(String(255), nullable=False, comment="姓名")
    english_name = Column(String(255), comment="英文名")
    gender = Column(String(10), comment="性别")
    date_of_birth = Column(Date, comment="出生日期")
    
    # ==================== 身份信息 ====================
    id_type = Column(String(50), comment="证件类型")
    id_number = Column(String(100), comment="证件号码")
    nationality = Column(String(50), default="中国", comment="国籍")
    
    # ==================== 联系信息 ====================
    phone = Column(String(50), comment="电话")
    email = Column(String(255), comment="邮箱")
    emergency_contact = Column(String(100), comment="紧急联系人")
    emergency_phone = Column(String(50), comment="紧急联系电话")
    address = Column(Text, comment="地址")
    
    # ==================== 工作信息 ====================
    employee_number = Column(String(100), comment="员工编号")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="职位")
    hire_date = Column(Date, comment="入职日期")
    work_experience_years = Column(Integer, comment="工作年限")
    
    # ==================== 技能等级 ====================
    skill_level = Column(String(50), comment="技能等级")
    specialization = Column(String(255), comment="专业方向")
    qualified_processes = Column(Text, comment="合格的焊接工艺(JSON)")
    qualified_positions = Column(Text, comment="合格的焊接位置(JSON)")
    qualified_materials = Column(Text, comment="合格的材料(JSON)")
    
    # ==================== 主要证书信息 ====================
    primary_certification_number = Column(String(100), comment="主要证书编号")
    primary_certification_level = Column(String(50), comment="主要证书等级")
    primary_certification_date = Column(Date, comment="主要证书颁发日期")
    primary_expiry_date = Column(Date, comment="主要证书过期日期")
    primary_issuing_authority = Column(String(255), comment="主要证书颁发机构")
    
    # ==================== 状态信息 ====================
    status = Column(String(50), default="active", comment="状态")
    certification_status = Column(String(50), default="valid", comment="证书状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # ==================== 绩效统计 ====================
    total_tasks_completed = Column(Integer, default=0, comment="完成任务数")
    total_weld_length = Column(Float, default=0, comment="累计焊接长度(m)")
    total_work_hours = Column(Float, default=0, comment="累计工时(h)")
    quality_score = Column(Float, comment="质量评分")
    efficiency_score = Column(Float, comment="效率评分")
    safety_score = Column(Float, comment="安全评分")
    
    # ==================== 培训信息 ====================
    last_training_date = Column(Date, comment="最后培训日期")
    next_training_date = Column(Date, comment="下次培训日期")
    training_hours = Column(Float, default=0, comment="培训时长(h)")
    
    # ==================== 健康信息 ====================
    last_health_check_date = Column(Date, comment="最后体检日期")
    next_health_check_date = Column(Date, comment="下次体检日期")
    health_status = Column(String(50), comment="健康状态")
    medical_restrictions = Column(Text, comment="医疗限制")
    
    # ==================== 附加信息 ====================
    photo_url = Column(String(500), comment="照片URL")
    description = Column(Text, comment="描述")
    notes = Column(Text, comment="备注")
    documents = Column(Text, comment="相关文档(JSON)")
    tags = Column(Text, comment="标签")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # ==================== 关系 ====================
    # owner = relationship("User", foreign_keys=[user_id], back_populates="welders")
    # company = relationship("Company", back_populates="welders")
    # factory = relationship("Factory", back_populates="welders")
    # certifications = relationship("WelderCertification", back_populates="welder", cascade="all, delete-orphan")
    # training_records = relationship("WelderTraining", back_populates="welder", cascade="all, delete-orphan")
    # work_records = relationship("WelderWorkRecord", back_populates="welder", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Welder(id={self.id}, code={self.welder_code}, name={self.full_name})>"


class WelderCertification(Base):
    """焊工证书模型"""
    
    __tablename__ = "welder_certifications"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # ==================== 关联信息 ====================
    welder_id = Column(Integer, ForeignKey("welders.id", ondelete="CASCADE"), nullable=False, index=True, comment="焊工ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    
    # ==================== 证书信息 ====================
    certification_number = Column(String(100), nullable=False, unique=True, index=True, comment="证书编号")
    certification_type = Column(String(100), nullable=False, comment="证书类型")
    certification_level = Column(String(50), comment="证书等级")
    certification_standard = Column(String(100), comment="认证标准")
    certification_system = Column(String(50), comment="认证体系")
    project_name = Column(String(200), comment="项目名称")
    
    # ==================== 颁发信息 ====================
    issuing_authority = Column(String(255), comment="颁发机构")
    issuing_country = Column(String(50), comment="颁发国家")
    issue_date = Column(Date, comment="颁发日期")
    expiry_date = Column(Date, comment="过期日期")
    
    # ==================== 合格范围 ====================
    # 旧字段（保留用于兼容）
    qualified_process = Column(String(100), comment="合格工艺")
    qualified_material_group = Column(String(100), comment="合格材料组")
    qualified_thickness_range = Column(String(100), comment="合格厚度范围")
    qualified_diameter_range = Column(String(100), comment="合格直径范围")
    qualified_position = Column(String(100), comment="合格位置")
    qualified_filler_material = Column(String(100), comment="合格填充材料")

    # 新字段（JSON格式）
    qualified_items = Column(Text, comment="合格项目列表（JSON格式）")
    qualified_range = Column(Text, comment="合格范围列表（JSON格式）")
    
    # ==================== 考试信息 ====================
    exam_date = Column(Date, comment="考试日期")
    exam_location = Column(String(255), comment="考试地点")
    exam_score = Column(Float, comment="考试成绩")
    practical_test_result = Column(String(50), comment="实操测试结果")
    theory_test_result = Column(String(50), comment="理论测试结果")
    
    # ==================== 状态信息 ====================
    status = Column(String(50), default="valid", comment="状态")
    is_primary = Column(Boolean, default=False, comment="是否主要证书")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # ==================== 续期信息 ====================
    renewal_date = Column(Date, comment="续期日期")
    renewal_count = Column(Integer, default=0, comment="续期次数")
    next_renewal_date = Column(Date, comment="下次续期日期")
    renewal_result = Column(String(50), comment="复审结果")
    renewal_notes = Column(Text, comment="复审备注")
    
    # ==================== 附加信息 ====================
    certificate_file_url = Column(String(500), comment="证书文件URL")
    notes = Column(Text, comment="备注")
    attachments = Column(Text, comment="附件(JSON)")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # ==================== 关系 ====================
    # welder = relationship("Welder", back_populates="certifications")
    # user = relationship("User", foreign_keys=[user_id])
    # company = relationship("Company")
    
    def __repr__(self):
        return f"<WelderCertification(id={self.id}, number={self.certification_number})>"


class WelderTraining(Base):
    """焊工培训记录模型"""

    __tablename__ = "welder_training_records"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # ==================== 数据隔离核心字段 ====================
    workspace_type = Column(String(20), nullable=False, default="personal", index=True, comment="工作区类型")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")

    # ==================== 关联信息 ====================
    welder_id = Column(Integer, ForeignKey("welders.id", ondelete="CASCADE"), nullable=False, index=True, comment="焊工ID")
    
    # ==================== 培训信息 ====================
    training_code = Column(String(100), comment="培训编号")
    training_name = Column(String(255), nullable=False, comment="培训名称")
    training_type = Column(String(100), comment="培训类型")
    training_category = Column(String(100), comment="培训类别")
    
    # ==================== 时间信息 ====================
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    duration_hours = Column(Float, comment="培训时长(h)")
    
    # ==================== 培训机构 ====================
    training_organization = Column(String(255), comment="培训机构")
    trainer_name = Column(String(100), comment="培训师")
    training_location = Column(String(255), comment="培训地点")
    
    # ==================== 培训内容 ====================
    training_content = Column(Text, comment="培训内容")
    training_objectives = Column(Text, comment="培训目标")
    training_materials = Column(Text, comment="培训材料(JSON)")
    
    # ==================== 考核信息 ====================
    assessment_method = Column(String(100), comment="考核方式")
    assessment_score = Column(Float, comment="考核成绩")
    assessment_result = Column(String(50), comment="考核结果")
    pass_status = Column(Boolean, comment="是否通过")
    
    # ==================== 证书信息 ====================
    certificate_issued = Column(Boolean, default=False, comment="是否颁发证书")
    certificate_number = Column(String(100), comment="证书编号")
    certificate_file_url = Column(String(500), comment="证书文件URL")
    
    # ==================== 附加信息 ====================
    notes = Column(Text, comment="备注")
    attachments = Column(Text, comment="附件(JSON)")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # ==================== 关系 ====================
    # welder = relationship("Welder", back_populates="training_records")
    # user = relationship("User", foreign_keys=[user_id])
    # company = relationship("Company")
    
    def __repr__(self):
        return f"<WelderTraining(id={self.id}, name={self.training_name})>"


class WelderWorkRecord(Base):
    """焊工工作记录模型"""

    __tablename__ = "welder_work_records"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # ==================== 数据隔离核心字段 ====================
    workspace_type = Column(String(20), nullable=False, default="personal", index=True, comment="工作区类型")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")

    # ==================== 关联信息 ====================
    welder_id = Column(Integer, ForeignKey("welders.id", ondelete="CASCADE"), nullable=False, index=True, comment="焊工ID")
    
    # 关联业务
    production_task_id = Column(Integer, comment="生产任务ID")
    wps_id = Column(Integer, comment="WPS ID")
    
    # ==================== 工作信息 ====================
    work_date = Column(Date, nullable=False, comment="工作日期")
    work_shift = Column(String(50), comment="班次")
    work_hours = Column(Float, comment="工时(h)")
    
    # ==================== 焊接信息 ====================
    welding_process = Column(String(100), comment="焊接工艺")
    welding_position = Column(String(50), comment="焊接位置")
    base_material = Column(String(100), comment="母材")
    filler_material = Column(String(100), comment="填充材料")
    weld_length = Column(Float, comment="焊接长度(m)")
    weld_weight = Column(Float, comment="焊接重量(kg)")
    
    # ==================== 质量信息 ====================
    quality_result = Column(String(50), comment="质量结果")
    defect_count = Column(Integer, default=0, comment="缺陷数量")
    rework_count = Column(Integer, default=0, comment="返工次数")
    
    # ==================== 附加信息 ====================
    notes = Column(Text, comment="备注")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    
    # ==================== 关系 ====================
    # welder = relationship("Welder", back_populates="work_records")

    def __repr__(self):
        return f"<WelderWorkRecord(id={self.id}, date={self.work_date})>"


class WelderAssessment(Base):
    """焊工考核记录模型"""

    __tablename__ = "welder_assessment_records"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # ==================== 数据隔离核心字段 ====================
    workspace_type = Column(String(20), nullable=False, default="personal", index=True, comment="工作区类型")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")

    # ==================== 关联信息 ====================
    welder_id = Column(Integer, ForeignKey("welders.id", ondelete="CASCADE"), nullable=False, index=True, comment="焊工ID")

    # ==================== 考核信息 ====================
    assessment_code = Column(String(100), comment="考核编号")
    assessment_name = Column(String(255), nullable=False, comment="考核名称")
    assessment_type = Column(String(100), comment="考核类型")  # 理论考核、实操考核、综合考核
    assessment_category = Column(String(100), comment="考核类别")  # 入职考核、定期考核、晋级考核

    # ==================== 时间信息 ====================
    assessment_date = Column(Date, nullable=False, comment="考核日期")
    duration_minutes = Column(Integer, comment="考核时长(分钟)")

    # ==================== 考核内容 ====================
    assessment_content = Column(Text, comment="考核内容")
    assessment_standards = Column(Text, comment="考核标准")
    assessment_items = Column(Text, comment="考核项目(JSON)")

    # ==================== 考核人员 ====================
    assessor_name = Column(String(100), comment="考核人")
    assessor_organization = Column(String(255), comment="考核机构")
    assessment_location = Column(String(255), comment="考核地点")

    # ==================== 考核成绩 ====================
    theory_score = Column(Float, comment="理论成绩")
    practical_score = Column(Float, comment="实操成绩")
    total_score = Column(Float, comment="总成绩")
    pass_score = Column(Float, comment="及格分数")

    # ==================== 考核结果 ====================
    assessment_result = Column(String(50), comment="考核结果")  # 优秀、良好、合格、不合格
    pass_status = Column(Boolean, comment="是否通过")
    grade_level = Column(String(50), comment="评定等级")

    # ==================== 证书信息 ====================
    certificate_issued = Column(Boolean, default=False, comment="是否颁发证书")
    certificate_number = Column(String(100), comment="证书编号")
    certificate_file_url = Column(String(500), comment="证书文件URL")

    # ==================== 附加信息 ====================
    notes = Column(Text, comment="备注")
    attachments = Column(Text, comment="附件(JSON)")

    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    def __repr__(self):
        return f"<WelderAssessment(id={self.id}, name={self.assessment_name})>"


class WelderWorkHistory(Base):
    """焊工工作履历模型"""

    __tablename__ = "welder_work_histories"

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # ==================== 数据隔离核心字段 ====================
    workspace_type = Column(String(20), nullable=False, default="personal", index=True, comment="工作区类型")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")

    # ==================== 关联信息 ====================
    welder_id = Column(Integer, ForeignKey("welders.id", ondelete="CASCADE"), nullable=False, index=True, comment="焊工ID")

    # ==================== 工作履历信息 ====================
    company_name = Column(String(255), nullable=False, comment="公司名称")
    position = Column(String(100), nullable=False, comment="职位")
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, nullable=True, comment="结束日期")
    department = Column(String(100), comment="部门")
    location = Column(String(255), comment="工作地点")
    job_description = Column(Text, comment="工作内容")
    achievements = Column(Text, comment="主要成就")
    leaving_reason = Column(String(255), comment="离职原因")

    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")

    def __repr__(self):
        return f"<WelderWorkHistory(id={self.id}, company={self.company_name}, position={self.position})>"

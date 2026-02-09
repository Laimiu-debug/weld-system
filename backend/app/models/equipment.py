"""
Equipment models for the welding system backend.
设备管理数据模型
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class EquipmentType(str, enum.Enum):
    """设备类型"""
    WELDING_MACHINE = "welding_machine"  # 焊接设备
    CUTTING_MACHINE = "cutting_machine"  # 切割设备
    GRINDING_MACHINE = "grinding_machine"  # 打磨设备
    TESTING_EQUIPMENT = "testing_equipment"  # 检测设备
    AUXILIARY_EQUIPMENT = "auxiliary_equipment"  # 辅助设备
    OTHER = "other"  # 其他


class EquipmentStatus(str, enum.Enum):
    """设备状态"""
    OPERATIONAL = "operational"  # 运行中
    IDLE = "idle"  # 空闲
    MAINTENANCE = "maintenance"  # 维护中
    REPAIR = "repair"  # 维修中
    BROKEN = "broken"  # 故障
    RETIRED = "retired"  # 报废


class MaintenanceType(str, enum.Enum):
    """维护类型"""
    ROUTINE = "routine"  # 例行维护
    PREVENTIVE = "preventive"  # 预防性维护
    CORRECTIVE = "corrective"  # 纠正性维护
    EMERGENCY = "emergency"  # 紧急维护


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


class Equipment(Base):
    """设备管理模型"""
    
    __tablename__ = "equipment"
    
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
    equipment_code = Column(String(100), nullable=False, index=True, comment="设备编号")
    equipment_name = Column(String(255), nullable=False, comment="设备名称")
    equipment_type = Column(String(50), nullable=False, comment="设备类型")
    category = Column(String(100), comment="设备类别")
    
    # ==================== 制造商信息 ====================
    manufacturer = Column(String(255), comment="制造商")
    brand = Column(String(100), comment="品牌")
    model = Column(String(100), comment="型号")
    serial_number = Column(String(100), unique=True, comment="序列号")
    
    # ==================== 技术参数 ====================
    specifications = Column(Text, comment="技术规格(JSON)")
    rated_power = Column(Float, comment="额定功率(kW)")
    rated_voltage = Column(Float, comment="额定电压(V)")
    rated_current = Column(Float, comment="额定电流(A)")
    max_capacity = Column(Float, comment="最大容量")
    working_range = Column(String(255), comment="工作范围")
    
    # ==================== 采购信息 ====================
    purchase_date = Column(Date, comment="采购日期")
    purchase_price = Column(Float, comment="采购价格")
    currency = Column(String(10), default="CNY", comment="货币")
    supplier = Column(String(255), comment="供应商")
    warranty_period = Column(Integer, comment="保修期(月)")
    warranty_expiry_date = Column(Date, comment="保修到期日期")
    
    # ==================== 位置信息 ====================
    location = Column(String(255), comment="位置")
    workshop = Column(String(100), comment="车间")
    area = Column(String(100), comment="区域")
    
    # ==================== 状态信息 ====================
    status = Column(String(50), default="operational", comment="状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_critical = Column(Boolean, default=False, comment="是否关键设备")
    
    # ==================== 使用信息 ====================
    installation_date = Column(Date, comment="安装日期")
    commissioning_date = Column(Date, comment="投产日期")
    total_operating_hours = Column(Float, default=0, comment="累计运行时长(h)")
    total_maintenance_hours = Column(Float, default=0, comment="累计维护时长(h)")
    last_used_date = Column(Date, comment="最后使用日期")
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    # ==================== 维护信息 ====================
    last_maintenance_date = Column(Date, comment="最后维护日期")
    next_maintenance_date = Column(Date, comment="下次维护日期")
    maintenance_interval_days = Column(Integer, comment="维护间隔(天)")
    maintenance_count = Column(Integer, default=0, comment="维护次数")
    
    # ==================== 检验信息 ====================
    last_inspection_date = Column(Date, comment="最后检验日期")
    next_inspection_date = Column(Date, comment="下次检验日期")
    inspection_interval_days = Column(Integer, comment="检验间隔(天)")
    calibration_date = Column(Date, comment="校准日期")
    calibration_due_date = Column(Date, comment="校准到期日期")
    
    # ==================== 责任人信息 ====================
    responsible_person_id = Column(Integer, ForeignKey("users.id"), comment="责任人ID")
    operator_ids = Column(Text, comment="操作员ID列表(JSON)")
    
    # ==================== 性能指标 ====================
    availability_rate = Column(Float, comment="可用率(%)")
    utilization_rate = Column(Float, comment="利用率(%)")
    failure_rate = Column(Float, comment="故障率")
    mtbf = Column(Float, comment="平均故障间隔时间(h)")
    mttr = Column(Float, comment="平均修复时间(h)")
    
    # ==================== 附加信息 ====================
    description = Column(Text, comment="描述")
    notes = Column(Text, comment="备注")
    manual_url = Column(String(500), comment="使用手册URL")
    images = Column(Text, comment="图片(JSON)")
    documents = Column(Text, comment="相关文档(JSON)")
    tags = Column(Text, comment="标签")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # ==================== 关系 ====================
    # owner = relationship("User", foreign_keys=[user_id], back_populates="equipment")
    # company = relationship("Company", back_populates="equipment")
    # factory = relationship("Factory", back_populates="equipment")
    # maintenance_records = relationship("EquipmentMaintenance", back_populates="equipment", cascade="all, delete-orphan")
    # usage_records = relationship("EquipmentUsage", back_populates="equipment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Equipment(id={self.id}, code={self.equipment_code}, name={self.equipment_name})>"


class EquipmentMaintenance(Base):
    """设备维护记录模型"""
    
    __tablename__ = "equipment_maintenance_records"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # ==================== 关联信息 ====================
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True, comment="设备ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")
    
    # ==================== 维护信息 ====================
    maintenance_code = Column(String(100), comment="维护编号")
    maintenance_type = Column(String(50), nullable=False, comment="维护类型")
    maintenance_category = Column(String(100), comment="维护类别")
    
    # ==================== 时间信息 ====================
    scheduled_date = Column(Date, comment="计划日期")
    start_date = Column(DateTime, nullable=False, comment="开始时间")
    end_date = Column(DateTime, comment="结束时间")
    duration_hours = Column(Float, comment="持续时长(h)")
    
    # ==================== 执行信息 ====================
    technician_id = Column(Integer, ForeignKey("users.id"), comment="技术员ID")
    technician_name = Column(String(100), comment="技术员姓名")
    team_members = Column(Text, comment="团队成员(JSON)")
    
    # ==================== 维护内容 ====================
    maintenance_items = Column(Text, comment="维护项目(JSON)")
    work_description = Column(Text, comment="工作描述")
    parts_replaced = Column(Text, comment="更换部件(JSON)")
    materials_used = Column(Text, comment="使用材料(JSON)")
    
    # ==================== 结果信息 ====================
    status = Column(String(50), default="completed", comment="状态")
    result = Column(String(50), comment="结果")
    issues_found = Column(Text, comment="发现的问题")
    recommendations = Column(Text, comment="建议")
    
    # ==================== 成本信息 ====================
    labor_cost = Column(Float, comment="人工成本")
    parts_cost = Column(Float, comment="配件成本")
    total_cost = Column(Float, comment="总成本")
    currency = Column(String(10), default="CNY", comment="货币")
    
    # ==================== 附加信息 ====================
    notes = Column(Text, comment="备注")
    attachments = Column(Text, comment="附件(JSON)")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # ==================== 关系 ====================
    # equipment = relationship("Equipment", back_populates="maintenance_records")
    # user = relationship("User", foreign_keys=[user_id])
    # technician = relationship("User", foreign_keys=[technician_id])
    # company = relationship("Company")
    # factory = relationship("Factory")
    
    def __repr__(self):
        return f"<EquipmentMaintenance(id={self.id}, type={self.maintenance_type})>"


class EquipmentUsage(Base):
    """设备使用记录模型"""
    
    __tablename__ = "equipment_usage_records"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # ==================== 关联信息 ====================
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True, comment="设备ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")
    
    # 关联业务
    production_task_id = Column(Integer, comment="生产任务ID")
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作员ID")
    
    # ==================== 使用信息 ====================
    usage_date = Column(Date, nullable=False, comment="使用日期")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    duration_hours = Column(Float, comment="使用时长(h)")
    
    # ==================== 工作信息 ====================
    work_type = Column(String(100), comment="工作类型")
    work_description = Column(Text, comment="工作描述")
    output_quantity = Column(Float, comment="产出数量")
    output_unit = Column(String(50), comment="产出单位")
    
    # ==================== 性能信息 ====================
    power_consumption = Column(Float, comment="耗电量(kWh)")
    efficiency = Column(Float, comment="效率(%)")
    quality_rating = Column(Float, comment="质量评分")
    
    # ==================== 问题记录 ====================
    issues_occurred = Column(Boolean, default=False, comment="是否发生问题")
    issue_description = Column(Text, comment="问题描述")
    downtime_hours = Column(Float, comment="停机时长(h)")
    
    # ==================== 附加信息 ====================
    notes = Column(Text, comment="备注")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    
    # ==================== 关系 ====================
    # equipment = relationship("Equipment", back_populates="usage_records")
    # operator = relationship("User", foreign_keys=[operator_id])
    
    def __repr__(self):
        return f"<EquipmentUsage(id={self.id}, date={self.usage_date})>"


"""
Welding Material models for the welding system backend.
焊材管理数据模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class MaterialType(str, enum.Enum):
    """焊材类型"""
    ELECTRODE = "electrode"  # 焊条
    WIRE = "wire"  # 焊丝
    FLUX = "flux"  # 焊剂
    GAS = "gas"  # 保护气体
    POWDER = "powder"  # 焊粉
    OTHER = "other"  # 其他


class MaterialStatus(str, enum.Enum):
    """焊材状态"""
    IN_STOCK = "in_stock"  # 在库
    LOW_STOCK = "low_stock"  # 低库存
    OUT_OF_STOCK = "out_of_stock"  # 缺货
    RESERVED = "reserved"  # 已预留
    EXPIRED = "expired"  # 已过期


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


class TransactionType(str, enum.Enum):
    """出入库类型"""
    IN = "in"  # 入库
    OUT = "out"  # 出库
    ADJUST = "adjust"  # 调整
    RETURN = "return"  # 退库
    TRANSFER = "transfer"  # 调拨
    CONSUME = "consume"  # 消耗（生产使用）


class WeldingMaterial(Base):
    """焊材管理模型"""
    
    __tablename__ = "welding_materials"
    
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
    material_code = Column(String(100), nullable=False, index=True, comment="焊材编号")
    material_name = Column(String(255), nullable=False, comment="焊材名称")
    material_type = Column(String(50), nullable=False, comment="焊材类型")
    specification = Column(String(255), comment="规格型号")
    classification = Column(String(100), comment="分类标准")
    
    # ==================== 制造商信息 ====================
    manufacturer = Column(String(255), comment="制造商")
    brand = Column(String(100), comment="品牌")
    supplier = Column(String(255), comment="供应商")
    supplier_contact = Column(String(100), comment="供应商联系方式")
    
    # ==================== 技术参数 ====================
    diameter = Column(Float, comment="直径/规格(mm)")
    length = Column(Float, comment="长度(mm)")
    weight_per_unit = Column(Float, comment="单位重量(kg)")
    chemical_composition = Column(Text, comment="化学成分")
    mechanical_properties = Column(Text, comment="力学性能")
    welding_position = Column(String(100), comment="适用焊接位置")
    current_type = Column(String(50), comment="电流类型")
    
    # ==================== 库存信息 ====================
    current_stock = Column(Float, default=0, comment="当前库存数量")
    unit = Column(String(50), default="kg", comment="单位")
    min_stock_level = Column(Float, comment="最低库存水平")
    max_stock_level = Column(Float, comment="最高库存水平")
    reorder_point = Column(Float, comment="再订货点")
    reorder_quantity = Column(Float, comment="再订货量")
    
    # ==================== 存储信息 ====================
    storage_location = Column(String(255), comment="存储位置")
    warehouse = Column(String(100), comment="仓库")
    shelf_number = Column(String(50), comment="货架号")
    bin_location = Column(String(50), comment="货位")
    
    # ==================== 价格信息 ====================
    unit_price = Column(Float, comment="单价")
    currency = Column(String(10), default="CNY", comment="货币单位")
    total_value = Column(Float, comment="库存总价值")
    last_purchase_price = Column(Float, comment="最近采购价")
    last_purchase_date = Column(DateTime, comment="最近采购日期")
    
    # ==================== 质量信息 ====================
    batch_number = Column(String(100), comment="批次号")
    production_date = Column(DateTime, comment="生产日期")
    expiry_date = Column(DateTime, comment="过期日期")
    quality_certificate = Column(String(255), comment="质量证书编号")
    inspection_report = Column(String(255), comment="检验报告")
    
    # ==================== 使用信息 ====================
    usage_count = Column(Integer, default=0, comment="使用次数")
    total_consumed = Column(Float, default=0, comment="累计消耗量")
    last_used_date = Column(DateTime, comment="最后使用日期")
    average_consumption_rate = Column(Float, comment="平均消耗率")
    
    # ==================== 状态信息 ====================
    status = Column(String(50), default="in_stock", comment="状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_critical = Column(Boolean, default=False, comment="是否关键物料")
    
    # ==================== 附加信息 ====================
    description = Column(Text, comment="描述")
    notes = Column(Text, comment="备注")
    technical_documents = Column(Text, comment="技术文档链接")
    images = Column(Text, comment="图片链接")
    tags = Column(Text, comment="标签")
    
    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    
    # ==================== 关系 ====================
    # owner = relationship("User", foreign_keys=[user_id], back_populates="materials")
    # company = relationship("Company", back_populates="materials")
    # factory = relationship("Factory", back_populates="materials")
    # transactions = relationship("MaterialTransaction", back_populates="material", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WeldingMaterial(id={self.id}, code={self.material_code}, name={self.material_name})>"


class MaterialCategory(Base):
    """焊材分类模型"""
    
    __tablename__ = "material_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 分类信息
    name = Column(String(100), nullable=False, unique=True, comment="分类名称")
    code = Column(String(50), unique=True, comment="分类代码")
    parent_id = Column(Integer, ForeignKey("material_categories.id"), nullable=True, comment="父分类ID")
    level = Column(Integer, default=1, comment="层级")
    
    # 描述信息
    description = Column(Text, comment="描述")
    icon = Column(String(100), comment="图标")
    sort_order = Column(Integer, default=0, comment="排序")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    # parent = relationship("MaterialCategory", remote_side=[id], back_populates="children")
    # children = relationship("MaterialCategory", back_populates="parent")
    
    def __repr__(self):
        return f"<MaterialCategory(id={self.id}, name={self.name})>"


class MaterialTransaction(Base):
    """焊材出入库记录模型"""

    __tablename__ = "material_transactions"
    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # ==================== 数据隔离核心字段 ====================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="操作用户ID")
    workspace_type = Column(String(20), default="personal", index=True, comment="工作区类型")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")

    # ==================== 关联信息 ====================
    material_id = Column(Integer, ForeignKey("welding_materials.id", ondelete="CASCADE"), nullable=False, index=True, comment="焊材ID")

    # ==================== 交易信息 ====================
    transaction_type = Column(String(50), nullable=False, index=True, comment="交易类型：in/out/adjust/return/transfer/consume")
    transaction_number = Column(String(100), index=True, comment="交易单号")
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False, comment="交易日期")

    # ==================== 数量信息 ====================
    quantity = Column(Float, nullable=False, comment="数量（正数表示增加，负数表示减少）")
    unit = Column(String(50), default="kg", comment="单位")
    stock_before = Column(Float, nullable=False, comment="交易前库存")
    stock_after = Column(Float, nullable=False, comment="交易后库存")

    # ==================== 价格信息 ====================
    unit_price = Column(Float, comment="单价")
    total_price = Column(Float, comment="总金额")  # 注意：数据库中是total_price不是total_amount
    currency = Column(String(10), default="CNY", comment="货币")

    # ==================== 来源/去向信息 ====================
    source = Column(String(255), comment="来源（供应商/仓库/部门等）")
    destination = Column(String(255), comment="去向（仓库/部门/项目等）")

    # ==================== 关联单据 ====================
    reference_type = Column(String(50), comment="关联单据类型（采购单/生产任务/调拨单等）")
    reference_id = Column(Integer, comment="关联单据ID")
    reference_number = Column(String(100), comment="关联单据号")

    # ==================== 批次信息 ====================
    batch_number = Column(String(100), comment="批次号")
    production_date = Column(DateTime, comment="生产日期")
    expiry_date = Column(DateTime, comment="过期日期")

    # ==================== 质检信息 ====================
    quality_status = Column(String(20), comment="质检状态：pending/passed/failed")
    quality_inspector = Column(String(100), comment="质检员")
    quality_report = Column(Text, comment="质检报告")

    # ==================== 存储信息 ====================
    warehouse = Column(String(100), comment="仓库")
    storage_location = Column(String(255), comment="存储位置")
    shelf_number = Column(String(50), comment="货架号")
    bin_location = Column(String(50), comment="货位")

    # ==================== 其他信息 ====================
    operator = Column(String(100), comment="操作员")
    approver = Column(String(100), comment="审批人")
    approval_status = Column(String(20), comment="审批状态：pending/approved/rejected")
    approval_date = Column(DateTime, comment="审批日期")

    notes = Column(Text, comment="备注")
    attachments = Column(Text, comment="附件（JSON格式）")

    # ==================== 状态 ====================
    is_active = Column(Boolean, default=True, comment="是否有效")
    is_cancelled = Column(Boolean, default=False, comment="是否已取消")
    cancelled_at = Column(DateTime, comment="取消时间")
    cancelled_by = Column(Integer, ForeignKey("users.id"), comment="取消人")
    cancel_reason = Column(Text, comment="取消原因")

    # ==================== 审计字段 ====================
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 关系
    material = relationship("WeldingMaterial", backref="transactions")

    def __repr__(self):
        return f"<MaterialTransaction(id={self.id}, type={self.transaction_type}, material_id={self.material_id})>"


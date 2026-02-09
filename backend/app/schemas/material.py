"""
Welding Material Pydantic schemas for the welding system backend.
焊材管理 Pydantic Schema
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ==================== 基础Schema ====================

class MaterialBase(BaseModel):
    """焊材基础Schema"""
    material_code: str = Field(..., description="焊材编号")
    material_name: str = Field(..., description="焊材名称")
    material_type: str = Field(..., description="焊材类型")
    specification: Optional[str] = Field(None, description="规格型号")
    classification: Optional[str] = Field(None, description="分类标准")
    
    # 制造商信息
    manufacturer: Optional[str] = Field(None, description="制造商")
    brand: Optional[str] = Field(None, description="品牌")
    supplier: Optional[str] = Field(None, description="供应商")
    supplier_contact: Optional[str] = Field(None, description="供应商联系方式")
    
    # 技术参数
    diameter: Optional[float] = Field(None, description="直径/规格(mm)")
    length: Optional[float] = Field(None, description="长度(mm)")
    weight_per_unit: Optional[float] = Field(None, description="单位重量(kg)")
    chemical_composition: Optional[str] = Field(None, description="化学成分")
    mechanical_properties: Optional[str] = Field(None, description="力学性能")
    welding_position: Optional[str] = Field(None, description="适用焊接位置")
    current_type: Optional[str] = Field(None, description="电流类型")
    
    # 库存信息
    current_stock: float = Field(default=0, description="当前库存数量")
    unit: str = Field(default="kg", description="单位")
    min_stock_level: Optional[float] = Field(None, description="最低库存水平")
    max_stock_level: Optional[float] = Field(None, description="最高库存水平")
    reorder_point: Optional[float] = Field(None, description="再订货点")
    reorder_quantity: Optional[float] = Field(None, description="再订货量")
    
    # 存储信息
    storage_location: Optional[str] = Field(None, description="存储位置")
    warehouse: Optional[str] = Field(None, description="仓库")
    shelf_number: Optional[str] = Field(None, description="货架号")
    bin_location: Optional[str] = Field(None, description="货位")

    # 成本信息
    unit_price: Optional[float] = Field(None, description="单价")
    currency: str = Field(default="CNY", description="货币")
    total_value: Optional[float] = Field(None, description="总价值")
    last_purchase_price: Optional[float] = Field(None, description="最后采购价")
    last_purchase_date: Optional[datetime] = Field(None, description="最后采购日期")

    # 批次信息
    batch_number: Optional[str] = Field(None, description="批次号")
    production_date: Optional[datetime] = Field(None, description="生产日期")
    expiry_date: Optional[datetime] = Field(None, description="过期日期")

    # 质量信息
    quality_certificate: Optional[str] = Field(None, description="质量证书")
    inspection_report: Optional[str] = Field(None, description="检验报告")

    # 使用统计
    usage_count: Optional[int] = Field(None, description="使用次数")
    total_consumed: Optional[float] = Field(None, description="总消耗量")
    last_used_date: Optional[datetime] = Field(None, description="最后使用日期")
    average_consumption_rate: Optional[float] = Field(None, description="平均消耗率")

    # 状态
    status: Optional[str] = Field(None, description="状态")
    is_critical: Optional[bool] = Field(None, description="是否关键物料")
    
    # 附加信息
    description: Optional[str] = Field(None, description="描述")
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[str] = Field(None, description="标签")


# ==================== 创建Schema ====================

class MaterialCreate(MaterialBase):
    """创建焊材Schema"""
    pass


# ==================== 更新Schema ====================

class MaterialUpdate(BaseModel):
    """更新焊材Schema"""
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    material_type: Optional[str] = None
    specification: Optional[str] = None
    classification: Optional[str] = None
    manufacturer: Optional[str] = None
    brand: Optional[str] = None
    supplier: Optional[str] = None
    supplier_contact: Optional[str] = None
    diameter: Optional[float] = None
    length: Optional[float] = None
    weight_per_unit: Optional[float] = None
    chemical_composition: Optional[str] = None
    mechanical_properties: Optional[str] = None
    welding_position: Optional[str] = None
    current_type: Optional[str] = None
    current_stock: Optional[float] = None
    unit: Optional[str] = None
    min_stock_level: Optional[float] = None
    max_stock_level: Optional[float] = None
    reorder_point: Optional[float] = None
    reorder_quantity: Optional[float] = None
    storage_location: Optional[str] = None
    warehouse: Optional[str] = None
    shelf_number: Optional[str] = None
    bin_location: Optional[str] = None
    unit_price: Optional[float] = None
    currency: Optional[str] = None
    total_value: Optional[float] = None
    last_purchase_price: Optional[float] = None
    last_purchase_date: Optional[datetime] = None
    batch_number: Optional[str] = None
    production_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    quality_certificate: Optional[str] = None
    inspection_report: Optional[str] = None
    usage_count: Optional[int] = None
    total_consumed: Optional[float] = None
    last_used_date: Optional[datetime] = None
    average_consumption_rate: Optional[float] = None
    status: Optional[str] = None
    is_critical: Optional[bool] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


# ==================== 响应Schema ====================

class MaterialResponse(MaterialBase):
    """焊材响应Schema"""
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

class MaterialListResponse(BaseModel):
    """焊材列表响应Schema"""
    items: List[MaterialResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== 库存变更Schema ====================

class MaterialStockChange(BaseModel):
    """库存变更Schema"""
    quantity: float = Field(..., description="变更数量（正数为入库，负数为出库）")
    transaction_type: str = Field(..., description="交易类型：in/out/adjust")
    batch_number: Optional[str] = Field(None, description="批次号")
    supplier_id: Optional[int] = Field(None, description="供应商ID")
    document_number: Optional[str] = Field(None, description="单据号")
    production_date: Optional[date] = Field(None, description="生产日期")
    expiry_date: Optional[date] = Field(None, description="过期日期")
    notes: Optional[str] = Field(None, description="备注")


# ==================== 库存统计Schema ====================

class MaterialStockStatistics(BaseModel):
    """库存统计Schema"""
    total_materials: int = Field(..., description="焊材总数")
    total_stock_value: float = Field(..., description="库存总价值")
    low_stock_count: int = Field(..., description="低库存数量")
    out_of_stock_count: int = Field(..., description="缺货数量")
    expiring_soon_count: int = Field(..., description="即将过期数量")


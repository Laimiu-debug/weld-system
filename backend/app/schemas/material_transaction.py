"""
Material Transaction schemas for the welding system backend.
焊材出入库记录Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MaterialTransactionBase(BaseModel):
    """出入库记录基础Schema"""
    material_id: int = Field(..., description="焊材ID")
    transaction_type: str = Field(..., description="交易类型：in/out/adjust/return/transfer/consume")
    quantity: float = Field(..., description="数量（正数表示增加，负数表示减少）")
    unit: Optional[str] = Field("kg", description="单位")
    
    # 价格信息
    unit_price: Optional[float] = Field(None, description="单价")
    total_amount: Optional[float] = Field(None, description="总金额")
    currency: Optional[str] = Field("CNY", description="货币")
    
    # 来源/去向
    source: Optional[str] = Field(None, description="来源（供应商/仓库/部门等）")
    destination: Optional[str] = Field(None, description="去向（仓库/部门/项目等）")
    
    # 关联单据
    reference_type: Optional[str] = Field(None, description="关联单据类型")
    reference_id: Optional[int] = Field(None, description="关联单据ID")
    reference_number: Optional[str] = Field(None, description="关联单据号")
    
    # 批次信息
    batch_number: Optional[str] = Field(None, description="批次号")
    production_date: Optional[datetime] = Field(None, description="生产日期")
    expiry_date: Optional[datetime] = Field(None, description="过期日期")
    
    # 质检信息
    quality_status: Optional[str] = Field(None, description="质检状态")
    quality_inspector: Optional[str] = Field(None, description="质检员")
    quality_report: Optional[str] = Field(None, description="质检报告")
    
    # 存储信息
    warehouse: Optional[str] = Field(None, description="仓库")
    storage_location: Optional[str] = Field(None, description="存储位置")
    shelf_number: Optional[str] = Field(None, description="货架号")
    bin_location: Optional[str] = Field(None, description="货位")
    
    # 其他信息
    operator: Optional[str] = Field(None, description="操作员")
    notes: Optional[str] = Field(None, description="备注")
    attachments: Optional[str] = Field(None, description="附件（JSON格式）")


class MaterialTransactionCreate(MaterialTransactionBase):
    """创建出入库记录Schema"""
    transaction_date: Optional[datetime] = Field(None, description="交易日期")


class MaterialTransactionUpdate(BaseModel):
    """更新出入库记录Schema"""
    notes: Optional[str] = Field(None, description="备注")
    attachments: Optional[str] = Field(None, description="附件")
    quality_status: Optional[str] = Field(None, description="质检状态")
    quality_inspector: Optional[str] = Field(None, description="质检员")
    quality_report: Optional[str] = Field(None, description="质检报告")


class MaterialTransactionResponse(MaterialTransactionBase):
    """出入库记录响应Schema"""
    id: int
    user_id: int
    workspace_type: str
    company_id: Optional[int]
    factory_id: Optional[int]
    
    transaction_number: str
    transaction_date: datetime
    
    stock_before: float
    stock_after: float
    
    approval_status: Optional[str]
    approver: Optional[str]
    approval_date: Optional[datetime]
    
    is_active: bool
    is_cancelled: bool
    cancelled_at: Optional[datetime]
    cancelled_by: Optional[int]
    cancel_reason: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: Optional[int]
    
    class Config:
        from_attributes = True


class MaterialTransactionListResponse(BaseModel):
    """出入库记录列表响应Schema"""
    items: list[MaterialTransactionResponse]
    total: int
    skip: int
    limit: int


class MaterialStockInRequest(BaseModel):
    """入库请求Schema"""
    material_id: int = Field(..., description="焊材ID")
    quantity: float = Field(..., gt=0, description="入库数量（必须大于0）")
    unit_price: Optional[float] = Field(None, description="单价")
    source: Optional[str] = Field(None, description="来源（供应商等）")
    batch_number: Optional[str] = Field(None, description="批次号")
    production_date: Optional[datetime] = Field(None, description="生产日期")
    expiry_date: Optional[datetime] = Field(None, description="过期日期")
    warehouse: Optional[str] = Field(None, description="仓库")
    storage_location: Optional[str] = Field(None, description="存储位置")
    notes: Optional[str] = Field(None, description="备注")


class MaterialStockOutRequest(BaseModel):
    """出库请求Schema"""
    material_id: int = Field(..., description="焊材ID")
    quantity: float = Field(..., gt=0, description="出库数量（必须大于0）")
    destination: Optional[str] = Field(None, description="去向（部门/项目等）")
    reference_type: Optional[str] = Field(None, description="关联单据类型（如：生产任务）")
    reference_id: Optional[int] = Field(None, description="关联单据ID")
    reference_number: Optional[str] = Field(None, description="关联单据号")
    notes: Optional[str] = Field(None, description="备注")


class MaterialStockAdjustRequest(BaseModel):
    """库存调整请求Schema"""
    material_id: int = Field(..., description="焊材ID")
    quantity: float = Field(..., description="调整数量（正数增加，负数减少）")
    reason: str = Field(..., description="调整原因")
    notes: Optional[str] = Field(None, description="备注")


class MaterialStockTransferRequest(BaseModel):
    """库存调拨请求Schema"""
    material_id: int = Field(..., description="焊材ID")
    quantity: float = Field(..., gt=0, description="调拨数量（必须大于0）")
    source_warehouse: Optional[str] = Field(None, description="源仓库")
    destination_warehouse: Optional[str] = Field(None, description="目标仓库")
    source_location: Optional[str] = Field(None, description="源位置")
    destination_location: Optional[str] = Field(None, description="目标位置")
    notes: Optional[str] = Field(None, description="备注")


class MaterialStockSummary(BaseModel):
    """库存汇总Schema"""
    material_id: int
    material_code: str
    material_name: str
    material_type: str
    current_stock: float
    unit: str
    total_in: float = Field(0, description="总入库量")
    total_out: float = Field(0, description="总出库量")
    total_value: float = Field(0, description="库存总值")
    last_transaction_date: Optional[datetime] = Field(None, description="最后交易日期")
    
    class Config:
        from_attributes = True


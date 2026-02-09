"""
WPS Template schemas for the welding system backend.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ==================== 模块实例相关 ====================
# 注：已移除 FieldDefinition, TabDefinition, TopInfoDefinition
# 这些类在新的模块化系统中不再需要

class ModuleInstance(BaseModel):
    """模块实例定义"""
    instanceId: str = Field(..., description="实例唯一ID")
    moduleId: str = Field(..., description="模块定义ID")
    order: int = Field(..., description="排序")
    customName: Optional[str] = Field(None, description="自定义名称（如'第1层'、'第2层'）")
    rowIndex: Optional[int] = Field(None, description="所在行索引")
    columnIndex: Optional[int] = Field(None, description="所在列索引")


# ==================== WPS模板 Schemas ====================

class WPSTemplateBase(BaseModel):
    """WPS模板基础Schema"""
    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    module_type: str = Field(default="wps", description="模块类型: wps/pqr/ppqr")
    welding_process: Optional[str] = Field(None, description="焊接工艺代码: 111, 114, 121, 135, 141, 15, 311")
    welding_process_name: Optional[str] = Field(None, description="焊接工艺名称")
    standard: Optional[str] = Field(None, description="焊接标准")
    # 注：已移除 field_schema, ui_layout, validation_rules, default_values
    # 现在仅使用 module_instances 基于模块的模板方式
    module_instances: List[ModuleInstance] = Field(..., description="模块实例列表（基于模块的模板）")


class WPSTemplateCreate(WPSTemplateBase):
    """创建WPS模板"""
    workspace_type: str = Field(default="personal", description="工作区类型: personal/enterprise")
    is_shared: bool = Field(default=False, description="是否共享")
    access_level: str = Field(default="private", description="访问级别: private/factory/company/public")


class WPSTemplateUpdate(BaseModel):
    """更新WPS模板"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    # 注：已移除 field_schema, ui_layout, validation_rules, default_values
    module_instances: Optional[List[ModuleInstance]] = Field(None, description="模块实例列表")
    is_shared: Optional[bool] = Field(None)
    access_level: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


class WPSTemplateResponse(WPSTemplateBase):
    """WPS模板响应"""
    id: str
    user_id: Optional[int] = None
    workspace_type: str
    company_id: Optional[int] = None
    template_source: str
    is_shared: bool
    access_level: str
    version: str
    is_active: bool
    is_system: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WPSTemplateSummary(BaseModel):
    """WPS模板摘要（列表用）"""
    id: str
    name: str
    description: Optional[str] = None
    module_type: str = Field(default="wps", description="模块类型: wps/pqr/ppqr")
    welding_process: Optional[str] = None
    welding_process_name: Optional[str] = None
    standard: Optional[str] = None
    template_source: str
    is_system: bool
    is_shared: bool
    usage_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WPSTemplateListResponse(BaseModel):
    """WPS模板列表响应"""
    total: int
    items: List[WPSTemplateSummary]


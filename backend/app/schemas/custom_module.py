"""
自定义模块 Pydantic schemas
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from app.domain.semantic_fields import get_semantic_field


class TableCellDefinition(BaseModel):
    """表格单元格定义"""
    label: str
    type: str  # text, number, select, date, textarea
    unit: Optional[str] = None
    options: Optional[List[str]] = None
    default: Optional[Any] = None
    required: Optional[bool] = False
    readonly: Optional[bool] = False
    placeholder: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    rowspan: Optional[int] = 1
    colspan: Optional[int] = 1


class TableRowDefinition(BaseModel):
    """表格行定义"""
    cells: List[TableCellDefinition]
    isHeader: Optional[bool] = False


class TableDefinition(BaseModel):
    """表格定义"""
    rows: List[TableRowDefinition]
    bordered: Optional[bool] = True
    size: Optional[str] = 'small'


class FieldDefinition(BaseModel):
    """字段定义"""
    label: str
    type: str  # text, number, select, date, textarea, file, table
    unit: Optional[str] = None
    options: Optional[list[str]] = None
    default: Optional[Any] = None
    required: Optional[bool] = False
    readonly: Optional[bool] = False
    placeholder: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    multiple: Optional[bool] = False
    tableDefinition: Optional[TableDefinition] = None
    field_id: Optional[str] = Field(
        default=None,
        description="稳定字段ID；显示键名或标签变化时保持不变",
    )
    description: Optional[str] = Field(None, max_length=500)
    aliases: List[str] = Field(default_factory=list)
    examples: List[Any] = Field(default_factory=list)
    ai_extract_mode: str = Field(
        default="auto",
        pattern="^(auto|manual|derived|disabled)$",
    )
    canonical_field_key: Optional[str] = None
    confidence_threshold: float = Field(default=0.8, ge=0, le=1)
    use_in_rules: bool = False

    @field_validator("canonical_field_key")
    @classmethod
    def validate_canonical_field_key(cls, value: Optional[str]) -> Optional[str]:
        if value and get_semantic_field(value) is None:
            raise ValueError("未知的系统语义字段")
        return value

    @field_validator("field_id")
    @classmethod
    def validate_field_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        try:
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("field_id 必须是有效 UUID") from exc


class CustomModuleBase(BaseModel):
    """自定义模块基础schema - 支持WPS/PQR/pPQR三种记录类型"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    icon: str = Field(default='BlockOutlined', max_length=50)

    # 模块类型：wps, pqr, ppqr, common
    module_type: str = Field(
        default='wps',
        pattern='^(wps|pqr|ppqr|common)$',
        description="模块适用的记录类型：wps=WPS模块, pqr=PQR模块, ppqr=pPQR模块, common=通用模块"
    )

    # 模块分类：通用分类系统
    category: str = Field(
        default='basic',
        pattern='^(basic|parameters|materials|tests|results|equipment|attachments|notes)$',
        description="模块分类：basic=基本信息, parameters=参数信息, materials=材料信息, tests=测试/试验, results=结果/评价, equipment=设备信息, attachments=附件, notes=备注"
    )

    repeatable: bool = False
    fields: Dict[str, FieldDefinition]
    is_shared: bool = False
    access_level: str = Field(default='private', pattern='^(private|shared|public)$')


class CustomModuleCreate(CustomModuleBase):
    """创建自定义模块schema"""
    id: Optional[str] = None  # 如果不提供，后端自动生成


class CustomModuleUpdate(BaseModel):
    """更新自定义模块schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    module_type: Optional[str] = Field(None, pattern='^(wps|pqr|ppqr|common)$')
    category: Optional[str] = Field(None, pattern='^(basic|parameters|materials|tests|results|equipment|attachments|notes)$')
    repeatable: Optional[bool] = None
    fields: Optional[Dict[str, FieldDefinition]] = None
    is_shared: Optional[bool] = None
    access_level: Optional[str] = Field(None, pattern='^(private|shared|public)$')


class CustomModuleResponse(CustomModuleBase):
    """自定义模块响应schema"""
    id: str
    module_type: str  # 确保包含module_type
    user_id: Optional[int] = None
    workspace_type: str
    company_id: Optional[int] = None
    factory_id: Optional[int] = None
    usage_count: int
    schema_version: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomModuleSummary(BaseModel):
    """自定义模块摘要schema（用于列表）"""
    id: str
    name: str
    description: Optional[str] = None
    icon: str
    module_type: str  # 模块类型
    category: str
    repeatable: bool
    field_count: int  # 字段数量
    usage_count: int
    is_shared: bool
    access_level: str
    created_at: datetime

    model_config = {"from_attributes": True}

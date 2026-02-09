"""
WPS Template models for the welding system backend.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class WPSTemplate(Base):
    """WPS模板 model - 支持系统模板和用户自定义模板."""
    
    __tablename__ = "wps_templates"
    
    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")

    # 模块类型
    module_type = Column(String(20), nullable=False, default="wps", index=True, comment="模块类型: wps/pqr/ppqr")

    # 适用范围
    welding_process = Column(String(50), nullable=True, index=True, comment="焊接工艺代码: 111, 114, 121, 135, 141, 15, 311")
    welding_process_name = Column(String(100), comment="焊接工艺名称")
    standard = Column(String(50), index=True, comment="焊接标准: AWS D1.1, ASME IX, EN ISO 15609-1, GB/T")

    # 模板配置（JSONB）
    # 注：已移除 field_schema, ui_layout, validation_rules, default_values
    # 现在仅使用 module_instances 基于模块的模板方式
    module_instances = Column(JSONB, nullable=False, comment="模块实例列表（基于模块的模板）")
    
    # ==================== 数据隔离字段 ====================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True, comment="创建用户ID（系统模板为NULL）")
    workspace_type = Column(String(20), nullable=False, default="system", index=True, comment="工作区类型: system/personal/enterprise")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")
    is_shared = Column(Boolean, default=False, comment="是否在企业内共享")
    access_level = Column(String(20), default="private", comment="访问级别: private/factory/company/public")
    template_source = Column(String(20), nullable=False, default="system", index=True, comment="模板来源: system/user/enterprise")
    
    # 元数据
    version = Column(String(20), default="1.0", comment="模板版本")
    is_active = Column(Boolean, default=True, index=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否为系统内置模板")
    
    # 统计信息
    usage_count = Column(Integer, default=0, comment="模板使用次数")
    
    # 审计
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")


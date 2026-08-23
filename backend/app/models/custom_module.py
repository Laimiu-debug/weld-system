"""
自定义模块模型
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class CustomModule(Base):
    """自定义字段模块模型 - 支持WPS/PQR/pPQR三种记录类型"""
    __tablename__ = "custom_modules"

    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    icon = Column(String(50), default='BlockOutlined')

    # 模块类型：标识此模块适用于哪种记录类型
    # wps: WPS模块, pqr: PQR模块, ppqr: pPQR模块, common: 通用模块（可用于所有类型）
    module_type = Column(String(20), nullable=False, default='wps', index=True)

    # 模块分类：通用分类系统
    # basic: 基本信息, parameters: 参数信息, materials: 材料信息, tests: 测试/试验
    # results: 结果/评价, equipment: 设备信息, attachments: 附件, notes: 备注
    category = Column(String(20), default='basic')
    repeatable = Column(Boolean, default=False)
    
    # 字段定义（JSONB格式）
    fields = Column(JSONB, nullable=False, default={})
    schema_version = Column(Integer, nullable=False, default=1)
    
    # 数据隔离字段
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    workspace_type = Column(String(20), default='personal')
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'))
    factory_id = Column(Integer, ForeignKey('factories.id', ondelete='SET NULL'))
    
    # 访问控制
    is_shared = Column(Boolean, default=False)
    access_level = Column(String(20), default='private')
    
    # 统计信息
    usage_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 约束
    __table_args__ = (
        CheckConstraint(
            "workspace_type IN ('personal', 'enterprise', 'system')",
            name='check_workspace_type'
        ),
        CheckConstraint(
            "access_level IN ('private', 'shared', 'public')",
            name='check_access_level'
        ),
        CheckConstraint(
            "module_type IN ('wps', 'pqr', 'ppqr', 'common')",
            name='check_module_type'
        ),
        CheckConstraint(
            "category IN ('basic', 'parameters', 'materials', 'tests', 'results', 'equipment', 'attachments', 'notes')",
            name='check_category'
        ),
    )

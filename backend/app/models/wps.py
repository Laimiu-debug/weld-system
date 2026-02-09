"""
WPS (Welding Procedure Specification) models for the welding system backend.
"""
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class WPS(Base):
    """WPS (Welding Procedure Specification) model."""

    __tablename__ = "wps"

    id = Column(Integer, primary_key=True, index=True)

    # ==================== 数据隔离核心字段 ====================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="创建用户ID")
    workspace_type = Column(String(20), nullable=False, default="personal", index=True, comment="工作区类型: personal/enterprise")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")

    # 数据访问控制
    is_shared = Column(Boolean, default=False, comment="是否在企业内共享")
    access_level = Column(String(20), default="private", comment="访问级别: private/factory/company/public")

    # 基本信息
    wps_number = Column(String(50), index=True, nullable=False, comment="WPS编号")
    title = Column(String(200), nullable=False, comment="标题")
    revision = Column(String(10), default="A", comment="版本号")
    status = Column(String(20), default="draft", comment="状态: draft, approved, obsolete")

    # 关联信息（保留owner_id用于向后兼容）
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="所有者ID（已废弃，使用user_id）")
    company = Column(String(100), comment="公司名称")
    project_name = Column(String(100), comment="项目名称")

    # 焊接工艺参数
    welding_process = Column(String(50), comment="焊接工艺: SMAW, GTAW, GMAW, FCAW, etc.")
    process_type = Column(String(20), comment="工艺类型: manual, semi-automatic, automatic, robotic")
    process_specification = Column(String(50), comment="工艺规范: AWS D1.1, ASME Section IX, ISO 15614, etc.")

    # 母材信息
    base_material_group = Column(String(50), comment="母材组号: P-No.1, P-No.2, etc.")
    base_material_spec = Column(String(50), comment="母材规格: ASTM A36, ASTM A516, etc.")
    base_material_thickness_range = Column(String(50), comment="母材厚度范围: 1.6-12.7mm")

    # 填充金属信息
    filler_material_spec = Column(String(50), comment="填充金属规格: AWS A5.1, AWS A5.18, etc.")
    filler_material_classification = Column(String(50), comment="填充金属分类: E7018, ER70S-6, etc.")
    filler_material_diameter = Column(Float, comment="填充金属直径: 2.4, 3.2, 4.0mm")

    # 保护气体信息
    shielding_gas = Column(String(50), comment="保护气体: Ar, CO2, Ar+CO2, etc.")
    gas_flow_rate = Column(Float, comment="气体流量: L/min")
    gas_composition = Column(String(50), comment="气体成分: 100%Ar, 75%Ar+25%CO2, etc.")

    # 电流参数
    current_type = Column(String(10), comment="电流类型: AC, DCEN, DCEP")
    current_polarity = Column(String(10), comment="电极极性: electrode positive/negative")
    current_range = Column(String(50), comment="电流范围: 90-130A")

    # 电压和送丝速度
    voltage_range = Column(String(50), comment="电压范围: 20-28V")
    wire_feed_speed = Column(String(50), comment="送丝速度: 200-400mm/min")

    # 焊接速度
    welding_speed = Column(String(50), comment="焊接速度: 100-250mm/min")
    travel_speed = Column(String(50), comment="行走速度: mm/min")

    # 热输入
    heat_input_min = Column(Float, comment="最小热输入: kJ/mm")
    heat_input_max = Column(Float, comment="最大热输入: kJ/mm")

    # 焊道信息
    weld_passes = Column(Integer, comment="焊道数量")
    weld_layer = Column(Integer, comment="焊层数量")

    # 坡口设计
    joint_design = Column(String(50), comment="接头设计: butt, T-joint, corner, lap")
    groove_type = Column(String(50), comment="坡口类型: V-groove, U-groove, J-groove")
    groove_angle = Column(String(50), comment="坡口角度: 60°")
    root_gap = Column(String(50), comment="根部间隙: 2-3mm")
    root_face = Column(String(50), comment="根部钝边: 1-2mm")

    # 预热和层间温度
    preheat_temp_min = Column(Float, comment="最低预热温度: °C")
    preheat_temp_max = Column(Float, comment="最高预热温度: °C")
    interpass_temp_max = Column(Float, comment="最高层间温度: °C")

    # 焊后热处理
    pwht_required = Column(Boolean, default=False, comment="是否需要焊后热处理")
    pwht_temperature = Column(Float, comment="焊后热处理温度: °C")
    pwht_time = Column(Float, comment="焊后热处理时间: hours")

    # 检验和测试
    ndt_required = Column(Boolean, default=True, comment="是否需要无损检测")
    ndt_methods = Column(Text, comment="无损检测方法: RT, UT, MT, PT")
    mechanical_testing = Column(Text, comment="力学性能测试: tensile, bend, charpy")

    # 重要性和特殊要求
    critical_application = Column(Boolean, default=False, comment="是否为关键应用")
    special_requirements = Column(Text, comment="特殊要求说明")

    # 附加信息
    notes = Column(Text, comment="备注")
    supporting_documents = Column(Text, comment="支持文件链接")
    attachments = Column(Text, comment="附件文件路径")

    # 审核和批准
    reviewed_by = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    reviewed_date = Column(DateTime, comment="审核日期")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="批准人ID")
    approved_date = Column(DateTime, comment="批准日期")

    # ==================== JSONB动态字段（模板驱动） ====================
    # 修改为外键 + SET NULL：当模板被删除时，已创建的WPS文档应该保持可编辑
    # template_id 设为 NULL 表示模板已被删除，但文档数据仍然完整保存在 modules_data 中
    template_id = Column(String(100), ForeignKey('wps_templates.id', ondelete='SET NULL'), nullable=True, index=True, comment="使用的模板ID（可为空，模板删除后自动设为NULL）")

    # 新增：完全灵活的模块数据存储
    # 结构: { "module_instance_id": { "field_key": value, ... }, ... }
    modules_data = Column(JSONB, default={}, comment="所有模块数据（JSON格式），支持无限自定义")

    # 文档编辑模式：存储富文本HTML内容
    document_html = Column(Text, nullable=True, comment="文档HTML内容（用于文档编辑模式）")

    # 保留以下字段用于向后兼容（逐步废弃）
    header_info = Column(JSONB, default={}, comment="表头数据（JSON格式）- 已废弃，使用 modules_data")
    summary_info = Column(JSONB, default={}, comment="概要信息（JSON格式）- 已废弃，使用 modules_data")
    diagram_info = Column(JSONB, default={}, comment="示意图信息（JSON格式）- 已废弃，使用 modules_data")
    weld_layers = Column(JSONB, default=[], comment="焊层信息数组（JSON格式）- 已废弃，使用 modules_data")
    additional_info = Column(JSONB, default={}, comment="附加信息（JSON格式）- 已废弃，使用 modules_data")

    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    # owner = relationship("User", foreign_keys=[user_id], back_populates="wps_records")
    # company_rel = relationship("Company", back_populates="wps_records")
    # factory_rel = relationship("Factory", back_populates="wps_records")
    # reviewer = relationship("User", foreign_keys=[reviewed_by])
    # approver = relationship("User", foreign_keys=[approved_by])

    # ==================== 表级约束 ====================
    # 注意：部分唯一索引已在数据库迁移脚本中创建
    # 这里只定义普通索引以提高查询性能
    __table_args__ = (
        # 复合索引：提高查询性能
        Index('idx_wps_workspace_user', 'workspace_type', 'user_id'),
        Index('idx_wps_workspace_company', 'workspace_type', 'company_id'),
    )


class WPSRevision(Base):
    """WPS版本历史记录 model."""

    __tablename__ = "wps_revisions"

    id = Column(Integer, primary_key=True, index=True)
    wps_id = Column(Integer, ForeignKey("wps.id"), nullable=False, comment="原WPS ID")
    revision_number = Column(String(10), nullable=False, comment="版本号")

    # 变更信息
    change_summary = Column(Text, comment="变更摘要")
    change_reason = Column(Text, comment="变更原因")
    changes_made = Column(Text, comment="具体变更内容")

    # 变更人信息
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="变更人ID")
    change_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 附件和文档
    old_document_path = Column(Text, comment="旧文档路径")
    new_document_path = Column(Text, comment="新文档路径")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    wps = relationship("WPS", back_populates="revisions")
    changer = relationship("User")


# 为WPS模型添加反向关系
WPS.revisions = relationship("WPSRevision", back_populates="wps")
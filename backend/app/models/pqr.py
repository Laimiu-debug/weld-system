"""
PQR (Procedure Qualification Record) models for the welding system backend.
"""
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Mapped, relationship
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class PQR(Base):
    """PQR (Procedure Qualification Record) model."""

    __tablename__ = "pqr"

    id = Column(Integer, primary_key=True, index=True)

    # ==================== 数据隔离核心字段 ====================
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="创建用户ID")
    workspace_type = Column(String(20), nullable=False, default="personal", index=True, comment="工作区类型: personal/enterprise")
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="企业ID")
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True, comment="工厂ID")

    # 数据访问控制
    is_shared = Column(Boolean, default=False, comment="是否在企业内共享")
    access_level = Column(String(20), default="private", comment="访问级别: private/factory/company/public")

    # 审计字段
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="最后更新人ID")

    # 基本信息
    pqr_number = Column(String(50), unique=True, index=True, nullable=False, comment="PQR编号")
    title = Column(String(200), nullable=False, comment="标题")
    wps_number = Column(String(50), comment="对应的WPS编号")
    test_date = Column(DateTime, nullable=True, comment="试验日期")
    status = Column(String(20), default="draft", index=True, comment="状态: draft/review/approved/rejected/archived")

    # 关联信息（保留owner_id用于向后兼容）
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="所有者ID（已废弃，使用user_id）")
    company = Column(String(100), comment="公司名称")
    project_name = Column(String(100), comment="项目名称")
    test_location = Column(String(100), comment="试验地点")
    welding_operator = Column(String(100), comment="焊工姓名和编号")

    # 焊接工艺参数
    welding_process = Column(String(50), comment="焊接工艺: SMAW, GTAW, GMAW, FCAW, etc.")
    process_type = Column(String(20), comment="工艺类型: manual, semi-automatic, automatic, robotic")
    process_specification = Column(String(50), comment="工艺规范: AWS D1.1, ASME Section IX, ISO 15614, etc.")

    # 母材信息
    base_material_group = Column(String(50), comment="母材组号: P-No.1, P-No.2, etc.")
    base_material_spec = Column(String(50), comment="母材规格: ASTM A36, ASTM A516, etc.")
    base_material_thickness = Column(Float, comment="母材实际厚度: mm")
    base_material_heat_number = Column(String(50), comment="母材炉号")

    # 填充金属信息
    filler_material_spec = Column(String(50), comment="填充金属规格: AWS A5.1, AWS A5.18, etc.")
    filler_material_classification = Column(String(50), comment="填充金属分类: E7018, ER70S-6, etc.")
    filler_material_diameter = Column(Float, comment="填充金属直径: mm")
    filler_material_heat_number = Column(String(50), comment="填充金属炉号")

    # 保护气体信息
    shielding_gas = Column(String(50), comment="保护气体: Ar, CO2, Ar+CO2, etc.")
    gas_flow_rate = Column(Float, comment="实际气体流量: L/min")
    gas_composition = Column(String(50), comment="气体成分: 100%Ar, 75%Ar+25%CO2, etc.")

    # 电流参数（实际值）
    current_type = Column(String(10), comment="电流类型: AC, DCEN, DCEP")
    current_polarity = Column(String(10), comment="电极极性")
    current_actual = Column(Float, comment="实际电流: A")
    voltage_actual = Column(Float, comment="实际电压: V")

    # 速度参数（实际值）
    wire_feed_speed_actual = Column(Float, comment="实际送丝速度: mm/min")
    welding_speed_actual = Column(Float, comment="实际焊接速度: mm/min")
    travel_speed_actual = Column(Float, comment="实际行走速度: mm/min")

    # 热输入计算
    heat_input_calculated = Column(Float, comment="计算热输入: kJ/mm")
    heat_input_range_min = Column(Float, comment="热输入范围最小值: kJ/mm")
    heat_input_range_max = Column(Float, comment="热输入范围最大值: kJ/mm")

    # 焊道和焊层信息
    weld_passes_actual = Column(Integer, comment="实际焊道数量")
    weld_layer_actual = Column(Integer, comment="实际焊层数量")

    # 坡口设计信息
    joint_design = Column(String(50), comment="接头设计: butt, T-joint, corner, lap")
    groove_type = Column(String(50), comment="坡口类型: V-groove, U-groove, J-groove")
    groove_angle_actual = Column(Float, comment="实际坡口角度: 度")
    root_gap_actual = Column(Float, comment="实际根部间隙: mm")
    root_face_actual = Column(Float, comment="实际根部钝边: mm")

    # 预热和层间温度（实际值）
    preheat_temp_actual = Column(Float, comment="实际预热温度: °C")
    interpass_temp_max_actual = Column(Float, comment="实际最高层间温度: °C")
    ambient_temperature = Column(Float, comment="环境温度: °C")
    humidity = Column(Float, comment="湿度: %")

    # 焊后热处理（实际值）
    pwht_performed = Column(Boolean, default=False, comment="是否进行了焊后热处理")
    pwht_temperature_actual = Column(Float, comment="实际焊后热处理温度: °C")
    pwht_time_actual = Column(Float, comment="实际焊后热处理时间: hours")
    pwht_method = Column(String(50), comment="热处理方法: furnace, local, etc.")

    # 无损检测结果
    visual_inspection_result = Column(String(20), comment="目视检测结果: pass/fail")
    rt_result = Column(String(20), comment="射线检测结果: pass/fail/N/A")
    ut_result = Column(String(20), comment="超声检测结果: pass/fail/N/A")
    mt_result = Column(String(20), comment="磁粉检测结果: pass/fail/N/A")
    pt_result = Column(String(20), comment="渗透检测结果: pass/fail/N/A")
    ndt_report_number = Column(String(50), comment="无损检测报告编号")

    # 力学性能测试结果
    tensile_test_result = Column(String(20), comment="拉伸测试结果: pass/fail")
    tensile_strength_actual = Column(Float, comment="实际抗拉强度: MPa")
    tensile_yield_strength = Column(Float, comment="屈服强度: MPa")
    tensile_elongation = Column(Float, comment="延伸率: %")

    # 弯曲测试结果
    root_bend_result = Column(String(20), comment="根部弯曲结果: pass/fail")
    face_bend_result = Column(String(20), comment="表面弯曲结果: pass/fail")
    side_bend_result = Column(String(20), comment="侧面弯曲结果: pass/fail")
    bend_angle = Column(Float, comment="弯曲角度: 度")
    bend_radius = Column(Float, comment="弯曲半径: mm")

    # 冲击测试结果
    charpy_test_performed = Column(Boolean, default=False, comment="是否进行了冲击测试")
    charpy_test_temp = Column(Float, comment="冲击试验温度: °C")
    charpy_energy_avg = Column(Float, comment="平均冲击功: J")
    charpy_energy_min = Column(Float, comment="最小冲击功: J")
    charpy_lateral_expansion = Column(Float, comment="侧向膨胀: mm")

    # 硬度测试结果
    hardness_test_performed = Column(Boolean, default=False, comment="是否进行了硬度测试")
    hardness_values = Column(Text, comment="硬度值列表: HV")

    # 金相检验结果
    metallography_performed = Column(Boolean, default=False, comment="是否进行了金相检验")
    metallography_results = Column(Text, comment="金相检验结果")

    # 腐蚀测试结果
    corrosion_test_performed = Column(Boolean, default=False, comment="是否进行了腐蚀测试")
    corrosion_test_results = Column(Text, comment="腐蚀测试结果")

    # 总体评定结果
    qualification_result = Column(String(20), comment="评定结果: qualified/not qualified")
    qualification_date = Column(DateTime, comment="评定日期")
    qualified_by = Column(Integer, ForeignKey("users.id"), comment="评定人ID")

    # 有效范围
    thickness_range_qualified = Column(String(50), comment="合格的厚度范围")
    diameter_range_qualified = Column(String(50), comment="合格的直径范围")
    position_qualified = Column(String(100), comment="合格的焊接位置")
    filler_material_range = Column(String(100), comment="合格的填充材料范围")

    # 附加信息
    test_notes = Column(Text, comment="试验备注")
    deviation_notes = Column(Text, comment="偏离说明")
    recommendations = Column(Text, comment="建议")
    test_reports = Column(Text, comment="试验报告文件路径")
    attachments = Column(Text, comment="附件文件路径")

    # ==================== 模块化数据 ====================
    # 修改为外键 + SET NULL：当模板被删除时，已创建的PQR文档应该保持可编辑
    # template_id 设为 NULL 表示模板已被删除，但文档数据仍然完整保存在 modules_data 中
    template_id = Column(String(100), ForeignKey('wps_templates.id', ondelete='SET NULL'), nullable=True, index=True, comment="使用的模板ID（可为空，模板删除后自动设为NULL）")
    modules_data = Column(JSONB, comment="模块化数据（JSONB格式）")

    # 文档编辑模式：存储富文本HTML内容
    document_html = Column(Text, nullable=True, comment="文档HTML内容（用于文档编辑模式）")

    # ==================== 时间戳字段 ====================
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    # owner = relationship("User", foreign_keys=[user_id], back_populates="pqr_records")
    # company_rel = relationship("Company", back_populates="pqr_records")
    # factory_rel = relationship("Factory", back_populates="pqr_records")
    # qualifier = relationship("User", foreign_keys=[qualified_by])


class PQRTestSpecimen(Base):
    """PQR试样信息 model."""

    __tablename__ = "pqr_test_specimens"

    id = Column(Integer, primary_key=True, index=True)
    pqr_id = Column(Integer, ForeignKey("pqr.id"), nullable=False, comment="PQR ID")

    # 试样基本信息
    specimen_type = Column(String(50), comment="试样类型: tensile, bend_root, bend_face, charpy")
    specimen_number = Column(String(20), comment="试样编号")
    specimen_location = Column(String(50), comment="取样位置")

    # 试样尺寸
    specimen_dimensions = Column(Text, comment="试样尺寸")

    # 测试结果
    test_result = Column(String(20), comment="测试结果: pass/fail")
    test_value = Column(Float, comment="测试值")
    test_unit = Column(String(20), comment="测试单位")

    # 测试条件
    test_temperature = Column(Float, comment="试验温度: °C")
    test_speed = Column(Float, comment="试验速度")

    # 失效信息（如适用）
    failure_mode = Column(String(50), comment="失效模式")
    failure_location = Column(String(50), comment="失效位置")

    # 备注
    specimen_notes = Column(Text, comment="试样备注")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    pqr = relationship("PQR", back_populates="specimens")


# 为PQR模型添加反向关系
PQR.specimens = relationship("PQRTestSpecimen", back_populates="pqr")
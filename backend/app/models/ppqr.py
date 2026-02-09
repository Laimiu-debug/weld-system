"""
pPQR (Preliminary Procedure Qualification Record) models for the welding system backend.
"""
from typing import Optional
from datetime import datetime, date

from sqlalchemy.orm import Mapped, relationship
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class PPQR(Base):
    """pPQR (Preliminary Procedure Qualification Record) model."""

    __tablename__ = "ppqr"

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
    ppqr_number = Column(String(50), unique=True, index=True, nullable=False, comment="pPQR编号")
    title = Column(String(200), nullable=False, comment="标题")
    revision = Column(String(10), default="A", comment="版本号")
    status = Column(String(20), default="draft", comment="状态: draft, testing, completed, converted")
    planned_test_date = Column(Date, comment="计划测试日期")
    actual_test_date = Column(Date, comment="实际测试日期")

    # 模板和模块数据
    # 修改为外键 + SET NULL：当模板被删除时，已创建的pPQR文档应该保持可编辑
    # template_id 设为 NULL 表示模板已被删除，但文档数据仍然完整保存在 module_data 中
    template_id = Column(String(100), ForeignKey('wps_templates.id', ondelete='SET NULL'), nullable=True, index=True, comment="使用的模板ID（可为空，模板删除后自动设为NULL）")
    module_data = Column(JSONB, comment="模块数据(JSON)")

    # 关联信息
    company = Column(String(100), comment="公司名称")
    project_name = Column(String(100), comment="项目名称")
    test_location = Column(String(100), comment="试验地点")
    
    # 试验目的和方案
    test_purpose = Column(Text, comment="试验目的")
    purpose = Column(Text, comment="试验目的（别名）")
    test_plan = Column(Text, comment="试验方案")
    expected_results = Column(Text, comment="预期结果")

    # 焊接工艺参数（计划）
    welding_process = Column(String(50), comment="焊接工艺: SMAW, GTAW, GMAW, FCAW, etc.")
    process_type = Column(String(20), comment="工艺类型: manual, semi-automatic, automatic, robotic")
    process_specification = Column(String(50), comment="工艺规范: AWS D1.1, ASME Section IX, ISO 15614, etc.")

    # 母材信息（计划）
    base_material_group = Column(String(50), comment="母材组号: P-No.1, P-No.2, etc.")
    base_material_spec = Column(String(50), comment="母材规格: ASTM A36, ASTM A516, etc.")
    base_material_thickness = Column(Float, comment="母材厚度: mm")

    # 填充金属信息（计划）
    filler_material_spec = Column(String(50), comment="填充金属规格: AWS A5.1, AWS A5.18, etc.")
    filler_material_classification = Column(String(50), comment="填充金属分类: E7018, ER70S-6, etc.")
    filler_material_diameter = Column(Float, comment="填充金属直径: mm")

    # 保护气体信息（计划）
    shielding_gas = Column(String(50), comment="保护气体: Ar, CO2, Ar+CO2, etc.")
    gas_flow_rate = Column(Float, comment="气体流量: L/min")
    gas_composition = Column(String(50), comment="气体成分: 100%Ar, 75%Ar+25%CO2, etc.")

    # 电流参数（计划）
    current_type = Column(String(10), comment="电流类型: AC, DCEN, DCEP")
    current_range = Column(String(50), comment="电流范围: 90-130A")
    voltage_range = Column(String(50), comment="电压范围: 20-28V")

    # 速度参数（计划）
    wire_feed_speed = Column(String(50), comment="送丝速度: 200-400mm/min")
    welding_speed = Column(String(50), comment="焊接速度: 100-250mm/min")

    # 热输入（计划）
    heat_input_min = Column(Float, comment="最小热输入: kJ/mm")
    heat_input_max = Column(Float, comment="最大热输入: kJ/mm")

    # 坡口设计（计划）
    joint_design = Column(String(50), comment="接头设计: butt, T-joint, corner, lap")
    groove_type = Column(String(50), comment="坡口类型: V-groove, U-groove, J-groove")
    groove_angle = Column(String(50), comment="坡口角度: 60°")
    root_gap = Column(String(50), comment="根部间隙: 2-3mm")
    root_face = Column(String(50), comment="根部钝边: 1-2mm")

    # 预热和层间温度（计划）
    preheat_temp_min = Column(Float, comment="最低预热温度: °C")
    preheat_temp_max = Column(Float, comment="最高预热温度: °C")
    interpass_temp_max = Column(Float, comment="最高层间温度: °C")

    # 焊后热处理（计划）
    pwht_required = Column(Boolean, default=False, comment="是否需要焊后热处理")
    pwht_temperature = Column(Float, comment="焊后热处理温度: °C")
    pwht_time = Column(Float, comment="焊后热处理时间: hours")

    # 实际参数（试验后填写）
    actual_parameters = Column(Text, comment="实际参数(JSON)")
    actual_current = Column(Float, comment="实际电流: A")
    actual_voltage = Column(Float, comment="实际电压: V")
    actual_wire_feed_speed = Column(Float, comment="实际送丝速度: mm/min")
    actual_welding_speed = Column(Float, comment="实际焊接速度: mm/min")
    actual_heat_input = Column(Float, comment="实际热输入: kJ/mm")
    actual_preheat_temp = Column(Float, comment="实际预热温度: °C")
    actual_interpass_temp = Column(Float, comment="实际层间温度: °C")

    # 环境条件
    ambient_temperature = Column(Float, comment="环境温度: °C")
    humidity = Column(Float, comment="湿度: %")
    weather_conditions = Column(String(100), comment="天气条件")

    # 试验人员
    welder_id = Column(Integer, ForeignKey("welders.id"), comment="焊工ID")
    welder_name = Column(String(100), comment="焊工姓名")
    welder_certification = Column(String(100), comment="焊工资质")
    tester_id = Column(Integer, ForeignKey("users.id"), comment="试验人员ID")
    tester_name = Column(String(100), comment="试验人员姓名")

    # 试验结果
    is_successful = Column(Boolean, comment="试验是否成功")
    test_result_summary = Column(Text, comment="试验结果摘要")
    test_conclusion = Column(String(50), comment="试验结论: qualified/failed/pending")
    
    # 目视检验
    visual_inspection_result = Column(String(20), comment="目视检测结果: pass/fail")
    visual_inspection_notes = Column(Text, comment="目视检测备注")
    
    # 无损检测（如果进行）
    ndt_performed = Column(Boolean, default=False, comment="是否进行无损检测")
    rt_result = Column(String(20), comment="射线检测结果: pass/fail/N/A")
    ut_result = Column(String(20), comment="超声检测结果: pass/fail/N/A")
    mt_result = Column(String(20), comment="磁粉检测结果: pass/fail/N/A")
    pt_result = Column(String(20), comment="渗透检测结果: pass/fail/N/A")
    
    # 力学性能测试（如果进行）
    mechanical_testing_performed = Column(Boolean, default=False, comment="是否进行力学性能测试")
    tensile_test_result = Column(String(20), comment="拉伸测试结果: pass/fail/N/A")
    bend_test_result = Column(String(20), comment="弯曲测试结果: pass/fail/N/A")
    charpy_test_result = Column(String(20), comment="冲击测试结果: pass/fail/N/A")
    hardness_test_result = Column(String(20), comment="硬度测试结果: pass/fail/N/A")

    # 问题和改进
    issues_found = Column(Text, comment="发现的问题")
    improvements_needed = Column(Text, comment="需要改进的地方")
    lessons_learned = Column(Text, comment="经验教训")
    recommendations = Column(Text, comment="建议")

    # 多组试验
    test_group_number = Column(Integer, default=1, comment="试验组号")
    parent_ppqr_id = Column(Integer, ForeignKey("ppqr.id"), comment="父pPQR ID（用于对比试验）")

    # 转换信息
    convert_to_pqr = Column(Boolean, default=False, comment="是否已转换为PQR（别名）")
    converted_to_pqr = Column(Boolean, default=False, comment="是否已转换为PQR")
    converted_to_pqr_id = Column(Integer, ForeignKey("pqr.id"), comment="转换后的PQR ID")
    converted_at = Column(DateTime, comment="转换时间")
    converted_by = Column(Integer, ForeignKey("users.id"), comment="转换人ID")

    # 附件
    test_photos = Column(Text, comment="试验照片(JSON)")
    test_videos = Column(Text, comment="试验视频(JSON)")
    test_reports = Column(Text, comment="试验报告文件路径")
    attachments = Column(Text, comment="附件文件路径")

    # 协作
    shared_with = Column(Text, comment="共享给的用户列表(JSON)")
    comments = Column(Text, comment="评论列表(JSON)")

    # 附加信息
    notes = Column(Text, comment="备注")
    deviation_notes = Column(Text, comment="偏离说明")

    # 文档编辑模式：存储富文本HTML内容
    document_html = Column(Text, nullable=True, comment="文档HTML内容（用于文档编辑模式）")

    # ==================== 审计字段 ====================
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    # owner = relationship("User", foreign_keys=[user_id], back_populates="ppqr_records")
    # company_rel = relationship("Company", back_populates="ppqr_records")
    # factory_rel = relationship("Factory", back_populates="ppqr_records")
    # welder = relationship("Welder", back_populates="ppqr_records")
    # tester = relationship("User", foreign_keys=[tester_id])
    # parent_ppqr = relationship("PPQR", remote_side=[id], foreign_keys=[parent_ppqr_id])
    # converted_pqr = relationship("PQR", foreign_keys=[converted_to_pqr_id])

    def __repr__(self):
        return f"<PPQR(id={self.id}, number={self.ppqr_number}, title={self.title})>"


class PPQRTestParameter(Base):
    """pPQR试验参数记录 model."""

    __tablename__ = "ppqr_test_parameters"

    id = Column(Integer, primary_key=True, index=True)
    ppqr_id = Column(Integer, ForeignKey("ppqr.id", ondelete="CASCADE"), nullable=False, comment="pPQR ID")

    # 参数信息
    parameter_name = Column(String(100), nullable=False, comment="参数名称")
    parameter_type = Column(String(50), comment="参数类型")
    planned_value = Column(String(100), comment="计划值")
    actual_value = Column(String(100), comment="实际值")
    unit = Column(String(20), comment="单位")
    deviation = Column(Float, comment="偏差")
    is_within_tolerance = Column(Boolean, comment="是否在容差范围内")

    # 备注
    notes = Column(Text, comment="备注")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    # ppqr = relationship("PPQR", back_populates="test_parameters")

    def __repr__(self):
        return f"<PPQRTestParameter(id={self.id}, name={self.parameter_name})>"


class PPQRComparison(Base):
    """pPQR对比记录 model."""

    __tablename__ = "ppqr_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    
    # 对比的pPQR
    ppqr_1_id = Column(Integer, ForeignKey("ppqr.id", ondelete="CASCADE"), nullable=False, comment="pPQR 1 ID")
    ppqr_2_id = Column(Integer, ForeignKey("ppqr.id", ondelete="CASCADE"), nullable=False, comment="pPQR 2 ID")
    
    # 对比信息
    comparison_title = Column(String(255), comment="对比标题")
    comparison_purpose = Column(Text, comment="对比目的")
    comparison_results = Column(Text, comment="对比结果(JSON)")
    conclusion = Column(Text, comment="结论")
    recommendations = Column(Text, comment="建议")

    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    # ppqr_1 = relationship("PPQR", foreign_keys=[ppqr_1_id])
    # ppqr_2 = relationship("PPQR", foreign_keys=[ppqr_2_id])

    def __repr__(self):
        return f"<PPQRComparison(id={self.id}, title={self.comparison_title})>"


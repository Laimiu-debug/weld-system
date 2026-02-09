-- 添加质量检验详细字段
-- Add detailed defect fields and reinspection info to quality inspections
-- Created: 2025-10-21

-- 添加缺陷详细计数字段
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS crack_count INTEGER DEFAULT 0;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS porosity_count INTEGER DEFAULT 0;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS inclusion_count INTEGER DEFAULT 0;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS undercut_count INTEGER DEFAULT 0;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS incomplete_penetration_count INTEGER DEFAULT 0;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS incomplete_fusion_count INTEGER DEFAULT 0;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS other_defect_count INTEGER DEFAULT 0;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS other_defect_description TEXT;

-- 添加处理措施字段
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS corrective_action_required BOOLEAN DEFAULT FALSE;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS repair_required BOOLEAN DEFAULT FALSE;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS repair_description TEXT;

-- 添加复检信息字段
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS reinspection_required BOOLEAN DEFAULT FALSE;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS reinspection_date DATE;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS reinspection_result VARCHAR(50);
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS reinspection_inspector_id INTEGER REFERENCES users(id);
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS reinspection_notes TEXT;

-- 添加环境条件字段
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS ambient_temperature FLOAT;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS weather_conditions VARCHAR(100);

-- 添加附加信息字段
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS photos TEXT;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS reports TEXT;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS tags VARCHAR(500);

-- 添加注释
COMMENT ON COLUMN quality_inspections.crack_count IS '裂纹数量';
COMMENT ON COLUMN quality_inspections.porosity_count IS '气孔数量';
COMMENT ON COLUMN quality_inspections.inclusion_count IS '夹渣数量';
COMMENT ON COLUMN quality_inspections.undercut_count IS '咬边数量';
COMMENT ON COLUMN quality_inspections.incomplete_penetration_count IS '未焊透数量';
COMMENT ON COLUMN quality_inspections.incomplete_fusion_count IS '未熔合数量';
COMMENT ON COLUMN quality_inspections.other_defect_count IS '其他缺陷数量';
COMMENT ON COLUMN quality_inspections.other_defect_description IS '其他缺陷描述';

COMMENT ON COLUMN quality_inspections.corrective_action_required IS '是否需要纠正措施';
COMMENT ON COLUMN quality_inspections.repair_required IS '是否需要修复';
COMMENT ON COLUMN quality_inspections.repair_description IS '修复描述';

COMMENT ON COLUMN quality_inspections.reinspection_required IS '是否需要复检';
COMMENT ON COLUMN quality_inspections.reinspection_date IS '复检日期';
COMMENT ON COLUMN quality_inspections.reinspection_result IS '复检结果';
COMMENT ON COLUMN quality_inspections.reinspection_inspector_id IS '复检员ID';
COMMENT ON COLUMN quality_inspections.reinspection_notes IS '复检备注';

COMMENT ON COLUMN quality_inspections.ambient_temperature IS '环境温度(°C)';
COMMENT ON COLUMN quality_inspections.weather_conditions IS '天气条件';

COMMENT ON COLUMN quality_inspections.photos IS '照片(JSON)';
COMMENT ON COLUMN quality_inspections.reports IS '报告(JSON)';
COMMENT ON COLUMN quality_inspections.tags IS '标签';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_quality_inspections_reinspection_date ON quality_inspections(reinspection_date);
CREATE INDEX IF NOT EXISTS idx_quality_inspections_reinspection_inspector_id ON quality_inspections(reinspection_inspector_id);


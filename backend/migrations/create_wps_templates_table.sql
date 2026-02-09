-- ============================================================
-- WPS 模板表 - 用于存储不同焊接工艺和标准的字段定义
-- ============================================================

CREATE TABLE IF NOT EXISTS wps_templates (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- 适用范围
    welding_process VARCHAR(50) NOT NULL,  -- 111, 114, 121, 135, 141, 15, 311 等
    welding_process_name VARCHAR(100),     -- 手工电弧焊, GMAW, GTAW 等
    standard VARCHAR(50),                  -- AWS D1.1, ASME IX, EN ISO 15609-1, GB/T
    
    -- 模板配置（JSONB）
    field_schema JSONB NOT NULL,           -- 字段定义（JSON Schema格式）
    ui_layout JSONB NOT NULL,              -- UI布局配置
    validation_rules JSONB,                -- 验证规则
    default_values JSONB,                  -- 默认值
    
    -- 元数据
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,       -- 是否为系统内置模板
    
    -- 审计
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_template_created_by FOREIGN KEY (created_by) REFERENCES users(id),
    CONSTRAINT fk_template_updated_by FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- 索引
CREATE INDEX idx_wps_templates_process ON wps_templates(welding_process);
CREATE INDEX idx_wps_templates_standard ON wps_templates(standard);
CREATE INDEX idx_wps_templates_active ON wps_templates(is_active);

-- 注释
COMMENT ON TABLE wps_templates IS 'WPS模板定义表';
COMMENT ON COLUMN wps_templates.id IS '模板ID，格式：{standard}_{process}，如 en_iso_15609_1_135';
COMMENT ON COLUMN wps_templates.welding_process IS '焊接工艺代码：111, 114, 121, 135, 141, 15, 311';
COMMENT ON COLUMN wps_templates.field_schema IS '字段定义（JSON Schema格式）';
COMMENT ON COLUMN wps_templates.ui_layout IS 'UI布局配置（标签页、分组、字段顺序）';

-- 插入系统内置模板（示例）
INSERT INTO wps_templates (id, name, welding_process, welding_process_name, standard, field_schema, ui_layout, is_system, is_active)
VALUES 
(
    'en_iso_15609_1_135',
    'EN ISO 15609-1 MAG焊接模板',
    '135',
    'MAG焊（熔化极活性气体保护焊）',
    'EN ISO 15609-1',
    '{
        "tabs": [
            {
                "key": "header",
                "label": "表头数据",
                "fields": ["status", "wps_number", "revision", "title", "manufacturer", "product_name", "customer", "location", "order_number", "part_number", "drawing_number", "wpqr_number", "welder_qualification", "drafted_by", "drafted_date", "reviewed_by", "reviewed_date", "approved_by", "approved_date", "notes", "pdf_link"]
            },
            {
                "key": "summary",
                "label": "概要",
                "fields": ["backing_strip", "base_material_1", "base_material_2", "thickness", "outer_diameter", "weld_geometry", "weld_preparation", "root_treatment", "cleaning_method", "preheat_temp", "interpass_temp", "welding_position", "bead_shape", "heat_treatment", "hydrogen_removal"]
            },
            {
                "key": "diagram",
                "label": "示意图",
                "fields": ["joint_shape", "welding_sequence", "dimensions", "notes", "diagram_files"]
            },
            {
                "key": "weld_layers",
                "label": "焊层",
                "type": "array",
                "fields": ["layer_id", "process", "filler_metal", "shielding_gas", "current_type", "current_pulse", "current_values", "voltage", "transfer_mode", "wire_feed_speed", "travel_speed", "oscillation", "contact_tip_distance", "angle", "equipment", "heat_input"]
            },
            {
                "key": "additional",
                "label": "附加页面",
                "fields": ["additional_notes", "attachments"]
            }
        ]
    }'::jsonb,
    '{
        "layout": "tabs",
        "responsive": true
    }'::jsonb,
    true,
    true
)
ON CONFLICT (id) DO NOTHING;

-- 完成
SELECT 'WPS模板表创建完成！' AS message;


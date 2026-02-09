-- ============================================================
-- WPS 模板表 - 支持系统模板和用户自定义模板
-- ============================================================

-- 删除旧表（如果存在）
DROP TABLE IF EXISTS wps_templates CASCADE;

-- 创建WPS模板表
CREATE TABLE wps_templates (
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
    
    -- ==================== 数据隔离字段 ====================
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workspace_type VARCHAR(20) NOT NULL DEFAULT 'system',
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
    is_shared BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(20) DEFAULT 'private',
    template_source VARCHAR(20) NOT NULL DEFAULT 'system',
    
    -- 元数据
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,       -- 是否为系统内置模板
    
    -- 统计信息
    usage_count INTEGER DEFAULT 0,
    
    -- 审计
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_wps_templates_process ON wps_templates(welding_process);
CREATE INDEX idx_wps_templates_standard ON wps_templates(standard);
CREATE INDEX idx_wps_templates_active ON wps_templates(is_active);
CREATE INDEX idx_wps_templates_user_id ON wps_templates(user_id);
CREATE INDEX idx_wps_templates_workspace_type ON wps_templates(workspace_type);
CREATE INDEX idx_wps_templates_company_id ON wps_templates(company_id);
CREATE INDEX idx_wps_templates_source ON wps_templates(template_source);

-- 注释
COMMENT ON TABLE wps_templates IS 'WPS模板定义表（支持系统模板和用户自定义模板）';
COMMENT ON COLUMN wps_templates.id IS '模板ID，格式：{standard}_{process}，如 en_iso_15609_1_135';
COMMENT ON COLUMN wps_templates.welding_process IS '焊接工艺代码：111, 114, 121, 135, 141, 15, 311';
COMMENT ON COLUMN wps_templates.field_schema IS '字段定义（JSON Schema格式）';
COMMENT ON COLUMN wps_templates.ui_layout IS 'UI布局配置（标签页、分组、字段顺序）';
COMMENT ON COLUMN wps_templates.user_id IS '创建用户ID（系统模板为NULL）';
COMMENT ON COLUMN wps_templates.workspace_type IS '工作区类型: system/personal/enterprise';
COMMENT ON COLUMN wps_templates.template_source IS '模板来源: system/user/enterprise';
COMMENT ON COLUMN wps_templates.is_shared IS '是否在企业内共享（仅企业工作区）';
COMMENT ON COLUMN wps_templates.access_level IS '访问级别: private/factory/company/public';
COMMENT ON COLUMN wps_templates.usage_count IS '模板使用次数统计';

-- 完成
SELECT 'WPS模板表创建完成！' AS message;


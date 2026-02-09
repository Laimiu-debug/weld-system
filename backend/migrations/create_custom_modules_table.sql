-- 创建自定义模块表
-- 用于存储用户自定义的字段模块

CREATE TABLE IF NOT EXISTS custom_modules (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT 'BlockOutlined',
    category VARCHAR(20) DEFAULT 'basic',
    repeatable BOOLEAN DEFAULT FALSE,
    
    -- 字段定义（JSONB格式）
    fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- 数据隔离字段
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workspace_type VARCHAR(20) DEFAULT 'personal',
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
    
    -- 访问控制
    is_shared BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(20) DEFAULT 'private',
    
    -- 统计信息
    usage_count INTEGER DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT check_workspace_type CHECK (workspace_type IN ('personal', 'enterprise', 'system')),
    CONSTRAINT check_access_level CHECK (access_level IN ('private', 'shared', 'public')),
    CONSTRAINT check_category CHECK (category IN ('basic', 'material', 'gas', 'electrical', 'motion', 'equipment', 'calculation'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_custom_modules_user_id ON custom_modules(user_id);
CREATE INDEX IF NOT EXISTS idx_custom_modules_workspace_type ON custom_modules(workspace_type);
CREATE INDEX IF NOT EXISTS idx_custom_modules_company_id ON custom_modules(company_id);
CREATE INDEX IF NOT EXISTS idx_custom_modules_category ON custom_modules(category);
CREATE INDEX IF NOT EXISTS idx_custom_modules_created_at ON custom_modules(created_at);

-- 添加触发器自动更新 updated_at
CREATE OR REPLACE FUNCTION update_custom_modules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_custom_modules_updated_at
    BEFORE UPDATE ON custom_modules
    FOR EACH ROW
    EXECUTE FUNCTION update_custom_modules_updated_at();

-- 添加注释
COMMENT ON TABLE custom_modules IS '用户自定义字段模块表';
COMMENT ON COLUMN custom_modules.id IS '模块唯一标识';
COMMENT ON COLUMN custom_modules.name IS '模块名称';
COMMENT ON COLUMN custom_modules.description IS '模块描述';
COMMENT ON COLUMN custom_modules.icon IS '模块图标';
COMMENT ON COLUMN custom_modules.category IS '模块分类';
COMMENT ON COLUMN custom_modules.repeatable IS '是否可重复（用于多层多道焊）';
COMMENT ON COLUMN custom_modules.fields IS '字段定义（JSONB格式）';
COMMENT ON COLUMN custom_modules.user_id IS '创建用户ID';
COMMENT ON COLUMN custom_modules.workspace_type IS '工作空间类型';
COMMENT ON COLUMN custom_modules.company_id IS '企业ID';
COMMENT ON COLUMN custom_modules.factory_id IS '工厂ID';
COMMENT ON COLUMN custom_modules.is_shared IS '是否共享';
COMMENT ON COLUMN custom_modules.access_level IS '访问级别';
COMMENT ON COLUMN custom_modules.usage_count IS '使用次数';

-- 插入一些示例自定义模块（可选）
INSERT INTO custom_modules (id, name, description, icon, category, repeatable, fields, workspace_type, user_id)
VALUES 
(
    'custom_example_preheating',
    '预热参数',
    '预热温度、层间温度等参数',
    'FireOutlined',
    'basic',
    false,
    '{
        "preheat_temp": {
            "label": "预热温度",
            "type": "number",
            "unit": "°C",
            "min": 0
        },
        "interpass_temp": {
            "label": "层间温度",
            "type": "number",
            "unit": "°C",
            "min": 0
        },
        "max_interpass_temp": {
            "label": "最大层间温度",
            "type": "number",
            "unit": "°C",
            "min": 0
        }
    }'::jsonb,
    'system',
    NULL
)
ON CONFLICT (id) DO NOTHING;

COMMIT;


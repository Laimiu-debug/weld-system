-- 添加pPQR缺失的字段
-- 这些字段用于支持模块化表单系统和前端功能

-- 添加revision字段（版本号）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS revision VARCHAR(10) DEFAULT 'A';

-- 添加template_id字段（模板ID）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS template_id VARCHAR(50);

-- 添加module_data字段（模块数据，JSONB格式）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS module_data JSONB;

-- 添加test_purpose字段（试验目的，作为purpose的别名）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS test_purpose TEXT;

-- 添加test_conclusion字段（试验结论）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS test_conclusion VARCHAR(50);

-- 添加convert_to_pqr字段（是否转换为PQR，作为converted_to_pqr的别名）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS convert_to_pqr BOOLEAN DEFAULT FALSE;

-- 添加created_by字段（创建人ID）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);

-- 添加updated_by字段（更新人ID）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

-- 添加created_at字段（创建时间）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 添加updated_at字段（更新时间）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 添加is_active字段（是否启用）
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ppqr_user_id ON ppqr(user_id);
CREATE INDEX IF NOT EXISTS idx_ppqr_workspace_type ON ppqr(workspace_type);
CREATE INDEX IF NOT EXISTS idx_ppqr_company_id ON ppqr(company_id);
CREATE INDEX IF NOT EXISTS idx_ppqr_factory_id ON ppqr(factory_id);
CREATE INDEX IF NOT EXISTS idx_ppqr_status ON ppqr(status);
CREATE INDEX IF NOT EXISTS idx_ppqr_test_conclusion ON ppqr(test_conclusion);
CREATE INDEX IF NOT EXISTS idx_ppqr_created_at ON ppqr(created_at);


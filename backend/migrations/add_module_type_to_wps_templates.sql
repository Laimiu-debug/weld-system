-- 添加 module_type 字段到 wps_templates 表
-- 用于区分 WPS、PQR 和 pPQR 模板

-- 1. 添加 module_type 字段
ALTER TABLE wps_templates 
ADD COLUMN IF NOT EXISTS module_type VARCHAR(20) DEFAULT 'wps';

-- 2. 添加索引
CREATE INDEX IF NOT EXISTS ix_wps_templates_module_type ON wps_templates(module_type);

-- 3. 添加检查约束
ALTER TABLE wps_templates 
ADD CONSTRAINT IF NOT EXISTS check_module_type 
CHECK (module_type IN ('wps', 'pqr', 'ppqr'));

-- 4. 更新现有数据（将所有现有模板标记为 WPS 类型）
UPDATE wps_templates 
SET module_type = 'wps' 
WHERE module_type IS NULL;

-- 5. 将 module_type 设置为 NOT NULL
ALTER TABLE wps_templates 
ALTER COLUMN module_type SET NOT NULL;

COMMENT ON COLUMN wps_templates.module_type IS '模块类型: wps/pqr/ppqr';


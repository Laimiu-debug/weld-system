-- 添加 module_instances 字段到 wps_templates 表
-- 用于支持基于模块的模板创建方式

-- 添加 module_instances 列
ALTER TABLE wps_templates 
ADD COLUMN IF NOT EXISTS module_instances JSONB;

-- 添加注释
COMMENT ON COLUMN wps_templates.module_instances IS '模块实例列表（新方式，基于模块的模板）';

-- 更新现有字段的注释
COMMENT ON COLUMN wps_templates.field_schema IS '字段定义（JSON Schema格式，传统方式）';
COMMENT ON COLUMN wps_templates.ui_layout IS 'UI布局配置（传统方式）';

-- 修改 field_schema 和 ui_layout 为可空（因为新方式使用 module_instances）
ALTER TABLE wps_templates 
ALTER COLUMN field_schema DROP NOT NULL;

ALTER TABLE wps_templates 
ALTER COLUMN ui_layout DROP NOT NULL;

-- 添加检查约束：确保至少有一种方式定义模板
-- 要么使用传统方式（field_schema + ui_layout），要么使用新方式（module_instances）
ALTER TABLE wps_templates 
ADD CONSTRAINT check_template_definition 
CHECK (
    (field_schema IS NOT NULL AND ui_layout IS NOT NULL) OR 
    (module_instances IS NOT NULL)
);

COMMENT ON CONSTRAINT check_template_definition ON wps_templates IS '确保模板至少使用一种定义方式（传统方式或模块方式）';


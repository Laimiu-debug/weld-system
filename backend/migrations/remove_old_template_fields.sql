-- ============================================================
-- 从WPS模板表中移除旧的标准模板字段
-- 这些字段在新的模块化系统中不再需要
-- ============================================================

-- 备份旧字段数据（可选，用于恢复）
-- CREATE TABLE wps_templates_backup_old_fields AS 
-- SELECT id, name, field_schema, ui_layout, validation_rules, default_values 
-- FROM wps_templates 
-- WHERE field_schema IS NOT NULL OR ui_layout IS NOT NULL;

-- 移除旧字段
ALTER TABLE wps_templates 
DROP COLUMN IF EXISTS field_schema,
DROP COLUMN IF EXISTS ui_layout,
DROP COLUMN IF EXISTS validation_rules,
DROP COLUMN IF EXISTS default_values;

-- 验证字段已移除
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'wps_templates' 
ORDER BY ordinal_position;

-- 显示剩余的系统模板
SELECT id, name, welding_process, welding_process_name, is_system, module_instances IS NOT NULL as has_module_instances
FROM wps_templates 
WHERE is_system = true
ORDER BY id;


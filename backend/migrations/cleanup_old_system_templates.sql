-- ============================================================
-- 清理旧的系统模板数据
-- 删除所有基于 field_schema + ui_layout 的系统模板
-- ============================================================

-- 备份旧系统模板数据（可选，用于恢复）
-- CREATE TABLE wps_templates_backup AS 
-- SELECT * FROM wps_templates WHERE is_system = true AND field_schema IS NOT NULL;

-- 删除所有旧系统模板（is_system=true 且 field_schema 不为空）
DELETE FROM wps_templates 
WHERE is_system = true 
  AND field_schema IS NOT NULL
  AND id LIKE 'system_%';

-- 验证删除结果
SELECT COUNT(*) as remaining_system_templates 
FROM wps_templates 
WHERE is_system = true;

-- 验证预设模板仍然存在
SELECT id, name, welding_process FROM wps_templates 
WHERE id LIKE 'preset_%' 
ORDER BY welding_process;

-- 显示所有系统模板（应该只有预设模板）
SELECT id, name, welding_process, is_system, field_schema IS NOT NULL as has_field_schema, module_instances IS NOT NULL as has_module_instances
FROM wps_templates 
WHERE is_system = true
ORDER BY id;


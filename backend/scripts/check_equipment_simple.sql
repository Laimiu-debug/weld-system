-- 检查设备表中的 workspace_type 字段
SELECT 
    id,
    equipment_code,
    equipment_name,
    user_id,
    company_id,
    workspace_type,
    is_active
FROM equipment
ORDER BY id;

-- 统计各工作区类型的设备数量
SELECT 
    workspace_type,
    COUNT(*) as count
FROM equipment
WHERE is_active = true
GROUP BY workspace_type;


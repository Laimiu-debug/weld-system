-- 修复设备表中的 workspace_type 字段
-- 这个SQL脚本会根据 company_id 自动设置 workspace_type

-- 1. 首先查看当前状态
SELECT 
    '当前设备状态' as info,
    workspace_type,
    COUNT(*) as count
FROM equipment
GROUP BY workspace_type;

-- 2. 查看需要修复的设备
SELECT 
    id,
    equipment_code,
    equipment_name,
    user_id,
    company_id,
    workspace_type,
    CASE 
        WHEN company_id IS NOT NULL THEN 'enterprise'
        ELSE 'personal'
    END as suggested_type
FROM equipment
WHERE workspace_type IS NULL OR workspace_type = '';

-- 3. 执行修复（请在确认上面的查询结果后再执行）
-- 将有 company_id 的设备设置为 enterprise
UPDATE equipment
SET workspace_type = 'enterprise'
WHERE (workspace_type IS NULL OR workspace_type = '')
  AND company_id IS NOT NULL;

-- 将没有 company_id 的设备设置为 personal
UPDATE equipment
SET workspace_type = 'personal'
WHERE (workspace_type IS NULL OR workspace_type = '')
  AND company_id IS NULL;

-- 4. 验证修复结果
SELECT 
    '修复后状态' as info,
    workspace_type,
    COUNT(*) as count
FROM equipment
GROUP BY workspace_type;

-- 5. 检查是否还有无效的 workspace_type
SELECT 
    id,
    equipment_code,
    equipment_name,
    workspace_type
FROM equipment
WHERE workspace_type IS NULL OR workspace_type = '';


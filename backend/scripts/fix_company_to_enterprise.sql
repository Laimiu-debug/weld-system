-- 修复 workspace_type 字段：将 'company' 改为 'enterprise'
-- 这是因为代码中使用 'enterprise' 作为企业工作区的标识

-- 1. 查看当前状态
SELECT 
    '修复前状态' as info,
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
    workspace_type
FROM equipment
WHERE workspace_type = 'company';

-- 3. 执行修复：将 'company' 改为 'enterprise'
UPDATE equipment
SET workspace_type = 'enterprise'
WHERE workspace_type = 'company';

-- 4. 验证修复结果
SELECT 
    '修复后状态' as info,
    workspace_type,
    COUNT(*) as count
FROM equipment
GROUP BY workspace_type;

-- 5. 最终检查：确保所有设备都有有效的 workspace_type
SELECT 
    id,
    equipment_code,
    equipment_name,
    workspace_type,
    company_id
FROM equipment
WHERE workspace_type NOT IN ('personal', 'enterprise')
   OR workspace_type IS NULL;


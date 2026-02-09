-- 更新企业工作区设备的访问级别
-- 将所有企业工作区的设备访问级别从 'private' 更新为 'company'
-- 这样企业成员可以根据角色权限访问设备

-- 更新企业工作区的设备访问级别
UPDATE equipment
SET access_level = 'company'
WHERE workspace_type = 'enterprise'
  AND (access_level = 'private' OR access_level IS NULL);

-- 验证更新结果
SELECT 
    workspace_type,
    access_level,
    COUNT(*) as count
FROM equipment
GROUP BY workspace_type, access_level
ORDER BY workspace_type, access_level;


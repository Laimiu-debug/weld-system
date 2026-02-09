-- ============================================================
-- 设备工作区隔离问题诊断脚本
-- ============================================================

-- 1. 查看所有设备的详细信息
SELECT 
    '=== 所有设备信息 ===' as section;

SELECT 
    id,
    equipment_code,
    equipment_name,
    workspace_type,
    user_id,
    company_id,
    factory_id,
    is_active,
    created_at
FROM equipment
ORDER BY id;

-- 2. 统计设备的工作区类型分布
SELECT 
    '=== 设备工作区类型统计 ===' as section;

SELECT 
    workspace_type,
    COUNT(*) as count,
    COUNT(CASE WHEN company_id IS NOT NULL THEN 1 END) as with_company,
    COUNT(CASE WHEN company_id IS NULL THEN 1 END) as without_company
FROM equipment
GROUP BY workspace_type;

-- 3. 查看所有用户
SELECT 
    '=== 所有用户 ===' as section;

SELECT 
    id,
    username,
    email,
    full_name,
    is_active,
    membership_type,
    member_tier
FROM users
ORDER BY id;

-- 4. 查看企业员工关系
SELECT 
    '=== 企业员工关系 ===' as section;

SELECT 
    ce.id,
    ce.user_id,
    ce.company_id,
    ce.factory_id,
    ce.role,
    ce.status,
    u.username,
    u.email,
    c.name as company_name
FROM company_employees ce
JOIN users u ON ce.user_id = u.id
JOIN companies c ON ce.company_id = c.id
WHERE ce.status = 'active'
ORDER BY ce.user_id;

-- 5. 查看所有企业
SELECT 
    '=== 所有企业 ===' as section;

SELECT 
    id,
    name,
    owner_id,
    is_active,
    membership_tier,
    subscription_status
FROM companies
WHERE is_active = true
ORDER BY id;

-- 6. 检查设备和用户的匹配关系
SELECT 
    '=== 设备和用户匹配关系 ===' as section;

SELECT 
    e.id as equipment_id,
    e.equipment_code,
    e.workspace_type,
    e.user_id as equipment_user_id,
    e.company_id as equipment_company_id,
    u.username as equipment_owner,
    u.email as equipment_owner_email,
    CASE 
        WHEN e.workspace_type = 'personal' THEN '个人设备'
        WHEN e.workspace_type = 'enterprise' THEN '企业设备'
        ELSE '未知类型'
    END as type_description
FROM equipment e
LEFT JOIN users u ON e.user_id = u.id
ORDER BY e.id;

-- 7. 检查企业设备和企业员工的匹配关系
SELECT 
    '=== 企业设备和员工匹配关系 ===' as section;

SELECT 
    e.id as equipment_id,
    e.equipment_code,
    e.company_id,
    c.name as company_name,
    COUNT(ce.id) as employee_count,
    STRING_AGG(u.username, ', ') as employees
FROM equipment e
LEFT JOIN companies c ON e.company_id = c.id
LEFT JOIN company_employees ce ON ce.company_id = e.company_id AND ce.status = 'active'
LEFT JOIN users u ON ce.user_id = u.id
WHERE e.workspace_type = 'enterprise'
GROUP BY e.id, e.equipment_code, e.company_id, c.name
ORDER BY e.id;

-- 8. 检查是否有无效的 workspace_type
SELECT 
    '=== 无效的 workspace_type ===' as section;

SELECT 
    id,
    equipment_code,
    workspace_type,
    user_id,
    company_id
FROM equipment
WHERE workspace_type NOT IN ('personal', 'enterprise')
   OR workspace_type IS NULL;

-- 9. 检查数据一致性问题
SELECT 
    '=== 数据一致性检查 ===' as section;

-- 个人设备但有 company_id
SELECT 
    'personal设备但有company_id' as issue,
    id,
    equipment_code,
    workspace_type,
    user_id,
    company_id
FROM equipment
WHERE workspace_type = 'personal' AND company_id IS NOT NULL

UNION ALL

-- 企业设备但没有 company_id
SELECT 
    'enterprise设备但没有company_id' as issue,
    id,
    equipment_code,
    workspace_type,
    user_id,
    company_id
FROM equipment
WHERE workspace_type = 'enterprise' AND company_id IS NULL;


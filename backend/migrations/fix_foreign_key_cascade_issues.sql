-- ============================================================================
-- 修复外键级联删除问题
-- 
-- 问题1：共享模块/模板删除级联问题
-- 当用户删除自己工作区的模块/模板时，共享库中的副本也会被删除
-- 解决方案：将 ondelete='CASCADE' 改为 ondelete='SET NULL'
--
-- 问题2：模板删除导致已创建的WPS/PQR/pPQR文档无法编辑
-- 当模板被删除后，已创建的文档因为找不到模板而无法编辑
-- 解决方案：将 template_id 改为外键并设置 ondelete='SET NULL'
--
-- 创建日期: 2025-10-27
-- ============================================================================

BEGIN;

-- ============================================================================
-- 问题1：修复共享库的外键级联问题
-- ============================================================================

-- 1.1 修复 shared_modules 表的 original_module_id 外键
-- 删除旧的外键约束
ALTER TABLE shared_modules 
DROP CONSTRAINT IF EXISTS shared_modules_original_module_id_fkey;

-- 修改列为可空（因为原始模块可能被删除）
ALTER TABLE shared_modules 
ALTER COLUMN original_module_id DROP NOT NULL;

-- 添加新的外键约束，使用 SET NULL
ALTER TABLE shared_modules 
ADD CONSTRAINT shared_modules_original_module_id_fkey 
FOREIGN KEY (original_module_id) 
REFERENCES custom_modules(id) 
ON DELETE SET NULL;

-- 1.2 修复 shared_templates 表的 original_template_id 外键
-- 删除旧的外键约束
ALTER TABLE shared_templates 
DROP CONSTRAINT IF EXISTS shared_templates_original_template_id_fkey;

-- 修改列为可空（因为原始模板可能被删除）
ALTER TABLE shared_templates 
ALTER COLUMN original_template_id DROP NOT NULL;

-- 添加新的外键约束，使用 SET NULL
ALTER TABLE shared_templates 
ADD CONSTRAINT shared_templates_original_template_id_fkey 
FOREIGN KEY (original_template_id) 
REFERENCES wps_templates(id) 
ON DELETE SET NULL;

-- ============================================================================
-- 问题2：修复WPS/PQR/pPQR文档的模板外键问题
-- ============================================================================

-- 2.1 修复 wps 表的 template_id 外键
-- 删除旧的外键约束（如果存在）
ALTER TABLE wps 
DROP CONSTRAINT IF EXISTS wps_template_id_fkey;

-- template_id 已经是可空的，所以不需要修改列属性
-- 添加新的外键约束，使用 SET NULL
ALTER TABLE wps 
ADD CONSTRAINT wps_template_id_fkey 
FOREIGN KEY (template_id) 
REFERENCES wps_templates(id) 
ON DELETE SET NULL;

-- 2.2 修复 pqr 表的 template_id 外键
-- 删除旧的外键约束（如果存在）
ALTER TABLE pqr 
DROP CONSTRAINT IF EXISTS pqr_template_id_fkey;

-- template_id 已经是可空的，所以不需要修改列属性
-- 添加新的外键约束，使用 SET NULL
ALTER TABLE pqr 
ADD CONSTRAINT pqr_template_id_fkey 
FOREIGN KEY (template_id) 
REFERENCES wps_templates(id) 
ON DELETE SET NULL;

-- 2.3 修复 ppqr 表的 template_id 外键
-- 删除旧的外键约束（如果存在）
ALTER TABLE ppqr 
DROP CONSTRAINT IF EXISTS ppqr_template_id_fkey;

-- 确保 template_id 列的类型和长度与 wps_templates.id 一致
-- 如果需要，修改列类型
ALTER TABLE ppqr 
ALTER COLUMN template_id TYPE VARCHAR(100);

-- template_id 已经是可空的，所以不需要修改列属性
-- 添加新的外键约束，使用 SET NULL
ALTER TABLE ppqr 
ADD CONSTRAINT ppqr_template_id_fkey 
FOREIGN KEY (template_id) 
REFERENCES wps_templates(id) 
ON DELETE SET NULL;

-- ============================================================================
-- 验证修改
-- ============================================================================

-- 查看所有相关的外键约束
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
    AND rc.constraint_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name IN ('shared_modules', 'shared_templates', 'wps', 'pqr', 'ppqr')
    AND kcu.column_name IN ('original_module_id', 'original_template_id', 'template_id')
ORDER BY tc.table_name, kcu.column_name;

COMMIT;

-- ============================================================================
-- 说明
-- ============================================================================
-- 
-- 修改后的行为：
-- 
-- 1. 共享库独立性：
--    - 当用户删除自己工作区的模块时，共享库中的副本不会被删除
--    - original_module_id 会被设置为 NULL，表示原始模块已被删除
--    - 共享库中的模块仍然可以被其他用户下载和使用
--    - 同样适用于模板
-- 
-- 2. 文档编辑独立性：
--    - 当模板被删除时，已创建的 WPS/PQR/pPQR 文档不会受影响
--    - template_id 会被设置为 NULL，表示模板已被删除
--    - 文档的所有数据都保存在 modules_data 字段中，仍然可以正常编辑
--    - 前端应该处理 template_id 为 NULL 的情况，直接使用 modules_data 渲染表单
-- 
-- 3. 数据完整性：
--    - 所有已创建的文档数据都是完整的，不依赖于模板
--    - 模板只是用于创建文档时的结构定义
--    - 删除模板不会影响已创建文档的数据完整性
-- 
-- ============================================================================


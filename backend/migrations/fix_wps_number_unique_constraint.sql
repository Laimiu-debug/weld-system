-- ============================================================
-- WPS 编号唯一性约束修复
-- ============================================================
-- 目的：实现正确的数据隔离，允许不同工作区使用相同的 WPS 编号
-- 
-- 问题：
-- 1. wps_number 字段有全局唯一约束 (unique=True)
-- 2. 这导致个人工作区和企业工作区不能使用相同的 WPS 编号
-- 3. 不同企业也不能使用相同的 WPS 编号
-- 
-- 解决方案：
-- 1. 删除全局唯一约束
-- 2. 创建部分唯一索引（partial unique index）
--    - 个人工作区：workspace_type + user_id + wps_number 唯一
--    - 企业工作区：workspace_type + company_id + wps_number 唯一
-- ============================================================

-- 步骤 1: 删除现有的全局唯一约束
-- 注意：约束名称可能不同，需要先查询实际的约束名称
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    -- 查找 wps_number 字段的唯一约束名称
    SELECT conname INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'wps'::regclass
      AND contype = 'u'
      AND conkey = ARRAY[(
          SELECT attnum 
          FROM pg_attribute 
          WHERE attrelid = 'wps'::regclass 
            AND attname = 'wps_number'
      )];
    
    -- 如果找到约束，则删除
    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE wps DROP CONSTRAINT %I', constraint_name);
        RAISE NOTICE '已删除唯一约束: %', constraint_name;
    ELSE
        RAISE NOTICE '未找到 wps_number 的唯一约束';
    END IF;
END $$;

-- 步骤 2: 删除现有的唯一索引（如果存在）
DROP INDEX IF EXISTS wps_wps_number_key;
DROP INDEX IF EXISTS ix_wps_wps_number;

-- 步骤 3: 创建新的普通索引（用于查询性能）
CREATE INDEX IF NOT EXISTS idx_wps_number ON wps(wps_number);

-- 步骤 4: 创建部分唯一索引 - 个人工作区
-- 确保在个人工作区内，同一用户的 WPS 编号唯一
CREATE UNIQUE INDEX IF NOT EXISTS uq_wps_number_personal
ON wps (workspace_type, user_id, wps_number)
WHERE workspace_type = 'personal';

-- 步骤 5: 创建部分唯一索引 - 企业工作区
-- 确保在企业工作区内，同一企业的 WPS 编号唯一
CREATE UNIQUE INDEX IF NOT EXISTS uq_wps_number_enterprise
ON wps (workspace_type, company_id, wps_number)
WHERE workspace_type = 'enterprise';

-- 步骤 6: 创建复合索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_wps_workspace_user 
ON wps (workspace_type, user_id);

CREATE INDEX IF NOT EXISTS idx_wps_workspace_company 
ON wps (workspace_type, company_id);

-- 步骤 7: 验证索引创建成功
DO $$
BEGIN
    -- 检查个人工作区唯一索引
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'wps' 
          AND indexname = 'uq_wps_number_personal'
    ) THEN
        RAISE NOTICE '✓ 个人工作区唯一索引创建成功';
    ELSE
        RAISE WARNING '✗ 个人工作区唯一索引创建失败';
    END IF;
    
    -- 检查企业工作区唯一索引
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'wps' 
          AND indexname = 'uq_wps_number_enterprise'
    ) THEN
        RAISE NOTICE '✓ 企业工作区唯一索引创建成功';
    ELSE
        RAISE WARNING '✗ 企业工作区唯一索引创建失败';
    END IF;
END $$;

-- ============================================================
-- 测试数据隔离
-- ============================================================
-- 以下是测试 SQL，可以手动执行验证

/*
-- 测试 1: 个人工作区 - 同一用户不能创建重复编号
INSERT INTO wps (user_id, workspace_type, wps_number, title, created_by)
VALUES (1, 'personal', 'WPS-001', 'Test WPS 1', 1);

-- 应该失败（违反唯一约束）
INSERT INTO wps (user_id, workspace_type, wps_number, title, created_by)
VALUES (1, 'personal', 'WPS-001', 'Test WPS 2', 1);

-- 测试 2: 个人工作区 - 不同用户可以创建相同编号
-- 应该成功
INSERT INTO wps (user_id, workspace_type, wps_number, title, created_by)
VALUES (2, 'personal', 'WPS-001', 'Test WPS 3', 2);

-- 测试 3: 企业工作区 - 同一企业不能创建重复编号
INSERT INTO wps (user_id, workspace_type, company_id, wps_number, title, created_by)
VALUES (1, 'enterprise', 1, 'WPS-001', 'Test WPS 4', 1);

-- 应该失败（违反唯一约束）
INSERT INTO wps (user_id, workspace_type, company_id, wps_number, title, created_by)
VALUES (2, 'enterprise', 1, 'WPS-001', 'Test WPS 5', 2);

-- 测试 4: 企业工作区 - 不同企业可以创建相同编号
-- 应该成功
INSERT INTO wps (user_id, workspace_type, company_id, wps_number, title, created_by)
VALUES (3, 'enterprise', 2, 'WPS-001', 'Test WPS 6', 3);

-- 测试 5: 个人工作区和企业工作区可以有相同编号
-- 应该成功（已经有个人工作区的 WPS-001）
INSERT INTO wps (user_id, workspace_type, company_id, wps_number, title, created_by)
VALUES (4, 'enterprise', 3, 'WPS-001', 'Test WPS 7', 4);

-- 清理测试数据
DELETE FROM wps WHERE title LIKE 'Test WPS%';
*/

-- ============================================================
-- 完成
-- ============================================================
RAISE NOTICE '========================================';
RAISE NOTICE 'WPS 编号唯一性约束修复完成！';
RAISE NOTICE '========================================';
RAISE NOTICE '数据隔离规则：';
RAISE NOTICE '1. 个人工作区：同一用户的 WPS 编号必须唯一';
RAISE NOTICE '2. 企业工作区：同一企业的 WPS 编号必须唯一';
RAISE NOTICE '3. 不同用户/企业可以使用相同的 WPS 编号';
RAISE NOTICE '4. 个人工作区和企业工作区可以使用相同的 WPS 编号';
RAISE NOTICE '========================================';


-- 修复 approval_history 表的架构，使其与模型一致
-- 1. 重命名 comments 为 comment
-- 2. 添加 result 字段
-- 3. 添加 operator_role 字段

DO $$
BEGIN
    -- 检查并重命名 comments 为 comment
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'approval_history' 
        AND column_name = 'comments'
    ) THEN
        ALTER TABLE approval_history 
        RENAME COLUMN comments TO comment;
        RAISE NOTICE 'Renamed comments to comment';
    ELSE
        RAISE NOTICE 'comments column does not exist or already renamed';
    END IF;
    
    -- 添加 result 字段（如果不存在）
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'approval_history' 
        AND column_name = 'result'
    ) THEN
        ALTER TABLE approval_history 
        ADD COLUMN result VARCHAR(20);
        
        COMMENT ON COLUMN approval_history.result IS '结果: approved, rejected, returned';
        RAISE NOTICE 'result column added';
    ELSE
        RAISE NOTICE 'result column already exists';
    END IF;
    
    -- 添加 operator_role 字段（如果不存在）
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'approval_history' 
        AND column_name = 'operator_role'
    ) THEN
        ALTER TABLE approval_history 
        ADD COLUMN operator_role VARCHAR(100);
        
        COMMENT ON COLUMN approval_history.operator_role IS '操作人角色';
        RAISE NOTICE 'operator_role column added';
    ELSE
        RAISE NOTICE 'operator_role column already exists';
    END IF;
END $$;

-- 完成
SELECT 'Migration completed: approval_history schema fixed' AS result;


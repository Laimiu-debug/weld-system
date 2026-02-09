-- 添加 step_name 字段到 approval_history 表
-- 这个字段在模型中存在但在原始迁移中缺失

-- 检查字段是否已存在
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'approval_history' 
        AND column_name = 'step_name'
    ) THEN
        -- 添加 step_name 字段
        ALTER TABLE approval_history 
        ADD COLUMN step_name VARCHAR(100);
        
        -- 添加注释
        COMMENT ON COLUMN approval_history.step_name IS '步骤名称';
        
        RAISE NOTICE 'step_name column added to approval_history table';
    ELSE
        RAISE NOTICE 'step_name column already exists in approval_history table';
    END IF;
END $$;

-- 完成
SELECT 'Migration completed: step_name field added to approval_history' AS result;


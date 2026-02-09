-- 修复 approval_instances 表缺失的 workspace_type 字段
-- 创建日期: 2025-10-29

-- 检查并添加 workspace_type 字段
DO $$ 
BEGIN
    -- 检查字段是否存在
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='approval_instances' AND column_name='workspace_type'
    ) THEN
        -- 添加 workspace_type 字段
        ALTER TABLE approval_instances 
        ADD COLUMN workspace_type VARCHAR(20) NOT NULL DEFAULT 'enterprise';
        
        -- 添加索引
        CREATE INDEX IF NOT EXISTS ix_approval_instances_workspace_type 
        ON approval_instances(workspace_type);
        
        -- 添加注释
        COMMENT ON COLUMN approval_instances.workspace_type IS '工作区类型: personal/enterprise';
        
        RAISE NOTICE '✅ workspace_type 字段添加成功';
    ELSE
        RAISE NOTICE '⚠️  workspace_type 字段已存在，跳过';
    END IF;
END $$;

-- 检查并添加 current_step_name 字段（如果缺失）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='approval_instances' AND column_name='current_step_name'
    ) THEN
        ALTER TABLE approval_instances 
        ADD COLUMN current_step_name VARCHAR(100);
        
        COMMENT ON COLUMN approval_instances.current_step_name IS '当前步骤名称';
        
        RAISE NOTICE '✅ current_step_name 字段添加成功';
    ELSE
        RAISE NOTICE '⚠️  current_step_name 字段已存在，跳过';
    END IF;
END $$;

-- 检查并添加 final_approver_id 字段（如果缺失）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='approval_instances' AND column_name='final_approver_id'
    ) THEN
        ALTER TABLE approval_instances 
        ADD COLUMN final_approver_id INTEGER REFERENCES users(id);
        
        COMMENT ON COLUMN approval_instances.final_approver_id IS '最终批准人ID';
        
        RAISE NOTICE '✅ final_approver_id 字段添加成功';
    ELSE
        RAISE NOTICE '⚠️  final_approver_id 字段已存在，跳过';
    END IF;
END $$;

-- 完成
SELECT '✅ approval_instances 表字段修复完成！' AS result;


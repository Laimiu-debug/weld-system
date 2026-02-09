-- 修改焊工证书表，将 issue_date 字段改为可选
-- Migration: 20241021_update_welder_certification_issue_date.sql

-- 检查表是否存在
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'welder_certifications') THEN
        -- 修改 issue_date 字段，允许为空
        ALTER TABLE welder_certifications
        ALTER COLUMN issue_date DROP NOT NULL;

        RAISE NOTICE '成功修改 welder_certifications 表的 issue_date 字段';
    ELSE
        RAISE NOTICE 'welder_certifications 表不存在，跳过迁移';
    END IF;
END $$;
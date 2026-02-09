-- 添加焊工记录表的数据隔离字段
-- 为焊工工作记录表添加缺失的数据隔离字段

-- 为 welder_work_records 表添加数据隔离字段
ALTER TABLE welder_work_records
ADD COLUMN workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal';

-- 为 welder_training_records 表添加数据隔离字段
ALTER TABLE welder_training_records
ADD COLUMN workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal';

-- 为 welder_assessment_records 表添加数据隔离字段
ALTER TABLE welder_assessment_records
ADD COLUMN workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal';

-- 为已有记录设置工作区类型（假设都是企业数据）
UPDATE welder_work_records SET workspace_type = 'enterprise' WHERE company_id IS NOT NULL;
UPDATE welder_training_records SET workspace_type = 'enterprise' WHERE company_id IS NOT NULL;
UPDATE welder_assessment_records SET workspace_type = 'enterprise' WHERE company_id IS NOT NULL;

-- 为 welder_training_records 表添加 factory_id 字段（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='welder_training_records'
        AND column_name='factory_id'
    ) THEN
        ALTER TABLE welder_training_records
        ADD COLUMN factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 为 welder_assessment_records 表添加 factory_id 字段（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='welder_assessment_records'
        AND column_name='factory_id'
    ) THEN
        ALTER TABLE welder_assessment_records
        ADD COLUMN factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_welder_work_records_workspace_type ON welder_work_records(workspace_type);
CREATE INDEX IF NOT EXISTS idx_welder_work_records_company_id ON welder_work_records(company_id);
CREATE INDEX IF NOT EXISTS idx_welder_work_records_factory_id ON welder_work_records(factory_id);

CREATE INDEX IF NOT EXISTS idx_welder_training_records_workspace_type ON welder_training_records(workspace_type);
CREATE INDEX IF NOT EXISTS idx_welder_training_records_company_id ON welder_training_records(company_id);
CREATE INDEX IF NOT EXISTS idx_welder_training_records_factory_id ON welder_training_records(factory_id);

CREATE INDEX IF NOT EXISTS idx_welder_assessment_records_workspace_type ON welder_assessment_records(workspace_type);
CREATE INDEX IF NOT EXISTS idx_welder_assessment_records_company_id ON welder_assessment_records(company_id);
CREATE INDEX IF NOT EXISTS idx_welder_assessment_records_factory_id ON welder_assessment_records(factory_id);

COMMENT ON COLUMN welder_work_records.workspace_type IS '工作区类型：personal/enterprise';
COMMENT ON COLUMN welder_training_records.workspace_type IS '工作区类型：personal/enterprise';
COMMENT ON COLUMN welder_assessment_records.workspace_type IS '工作区类型：personal/enterprise';
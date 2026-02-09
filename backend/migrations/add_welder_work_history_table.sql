-- 创建焊工工作履历表
-- Migration: add_welder_work_history_table
-- Created: 2025-10-21

-- 创建焊工工作履历表
CREATE TABLE IF NOT EXISTS welder_work_histories (
    -- 主键
    id SERIAL PRIMARY KEY,
    
    -- 数据隔离核心字段
    workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
    
    -- 关联信息
    welder_id INTEGER NOT NULL REFERENCES welders(id) ON DELETE CASCADE,
    
    -- 工作履历信息
    company_name VARCHAR(255) NOT NULL,
    position VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    department VARCHAR(100),
    location VARCHAR(255),
    job_description TEXT,
    achievements TEXT,
    leaving_reason VARCHAR(255),
    
    -- 审计字段
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_welder_work_histories_workspace_type ON welder_work_histories(workspace_type);
CREATE INDEX IF NOT EXISTS idx_welder_work_histories_user_id ON welder_work_histories(user_id);
CREATE INDEX IF NOT EXISTS idx_welder_work_histories_company_id ON welder_work_histories(company_id);
CREATE INDEX IF NOT EXISTS idx_welder_work_histories_factory_id ON welder_work_histories(factory_id);
CREATE INDEX IF NOT EXISTS idx_welder_work_histories_welder_id ON welder_work_histories(welder_id);
CREATE INDEX IF NOT EXISTS idx_welder_work_histories_start_date ON welder_work_histories(start_date);

-- 添加注释
COMMENT ON TABLE welder_work_histories IS '焊工工作履历表';
COMMENT ON COLUMN welder_work_histories.id IS '主键ID';
COMMENT ON COLUMN welder_work_histories.workspace_type IS '工作区类型';
COMMENT ON COLUMN welder_work_histories.user_id IS '用户ID';
COMMENT ON COLUMN welder_work_histories.company_id IS '企业ID';
COMMENT ON COLUMN welder_work_histories.factory_id IS '工厂ID';
COMMENT ON COLUMN welder_work_histories.welder_id IS '焊工ID';
COMMENT ON COLUMN welder_work_histories.company_name IS '公司名称';
COMMENT ON COLUMN welder_work_histories.position IS '职位';
COMMENT ON COLUMN welder_work_histories.start_date IS '开始日期';
COMMENT ON COLUMN welder_work_histories.end_date IS '结束日期';
COMMENT ON COLUMN welder_work_histories.department IS '部门';
COMMENT ON COLUMN welder_work_histories.location IS '工作地点';
COMMENT ON COLUMN welder_work_histories.job_description IS '工作内容';
COMMENT ON COLUMN welder_work_histories.achievements IS '主要成就';
COMMENT ON COLUMN welder_work_histories.leaving_reason IS '离职原因';
COMMENT ON COLUMN welder_work_histories.created_by IS '创建人ID';
COMMENT ON COLUMN welder_work_histories.created_at IS '创建时间';
COMMENT ON COLUMN welder_work_histories.updated_at IS '更新时间';


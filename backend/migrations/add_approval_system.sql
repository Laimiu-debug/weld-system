-- 审批系统数据库迁移脚本
-- 创建日期: 2025-10-29

-- 1. 创建审批工作流定义表
CREATE TABLE IF NOT EXISTS approval_workflow_definitions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    description TEXT,
    document_type VARCHAR(50) NOT NULL,
    company_id INTEGER,
    factory_id INTEGER,
    steps JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_default BOOLEAN NOT NULL DEFAULT false,
    created_by INTEGER,
    updated_by INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_workflow_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    CONSTRAINT fk_workflow_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_workflow_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_approval_workflow_definitions_document_type ON approval_workflow_definitions(document_type);
CREATE INDEX IF NOT EXISTS ix_approval_workflow_definitions_company_id ON approval_workflow_definitions(company_id);
CREATE INDEX IF NOT EXISTS ix_approval_workflow_definitions_code ON approval_workflow_definitions(code);
CREATE INDEX IF NOT EXISTS ix_approval_workflow_definitions_is_active ON approval_workflow_definitions(is_active);

-- 2. 创建审批实例表
CREATE TABLE IF NOT EXISTS approval_instances (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    document_id INTEGER NOT NULL,
    document_number VARCHAR(100),
    document_title VARCHAR(200),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    current_step INTEGER NOT NULL DEFAULT 1,
    priority VARCHAR(20) DEFAULT 'normal',
    submitter_id INTEGER NOT NULL,
    submitted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    notes TEXT,
    company_id INTEGER,
    factory_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_instance_workflow FOREIGN KEY (workflow_id) REFERENCES approval_workflow_definitions(id) ON DELETE CASCADE,
    CONSTRAINT fk_instance_submitter FOREIGN KEY (submitter_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_instance_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_approval_instances_document_type ON approval_instances(document_type);
CREATE INDEX IF NOT EXISTS ix_approval_instances_document_id ON approval_instances(document_id);
CREATE INDEX IF NOT EXISTS ix_approval_instances_status ON approval_instances(status);
CREATE INDEX IF NOT EXISTS ix_approval_instances_submitter_id ON approval_instances(submitter_id);
CREATE INDEX IF NOT EXISTS ix_approval_instances_company_id ON approval_instances(company_id);
CREATE INDEX IF NOT EXISTS ix_approval_instances_submitted_at ON approval_instances(submitted_at);

-- 创建复合索引用于快速查询
CREATE INDEX IF NOT EXISTS ix_approval_instances_doc_type_id ON approval_instances(document_type, document_id);

-- 3. 创建审批历史表
CREATE TABLE IF NOT EXISTS approval_history (
    id SERIAL PRIMARY KEY,
    instance_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    operator_id INTEGER NOT NULL,
    operator_name VARCHAR(100) NOT NULL,
    comments TEXT,
    attachments JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_history_instance FOREIGN KEY (instance_id) REFERENCES approval_instances(id) ON DELETE CASCADE,
    CONSTRAINT fk_history_operator FOREIGN KEY (operator_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_approval_history_instance_id ON approval_history(instance_id);
CREATE INDEX IF NOT EXISTS ix_approval_history_operator_id ON approval_history(operator_id);
CREATE INDEX IF NOT EXISTS ix_approval_history_created_at ON approval_history(created_at);

-- 4. 创建审批通知表
CREATE TABLE IF NOT EXISTS approval_notifications (
    id SERIAL PRIMARY KEY,
    instance_id INTEGER NOT NULL,
    recipient_id INTEGER NOT NULL,
    notification_type VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMP,
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_notification_instance FOREIGN KEY (instance_id) REFERENCES approval_instances(id) ON DELETE CASCADE,
    CONSTRAINT fk_notification_recipient FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_approval_notifications_instance_id ON approval_notifications(instance_id);
CREATE INDEX IF NOT EXISTS ix_approval_notifications_recipient_id ON approval_notifications(recipient_id);
CREATE INDEX IF NOT EXISTS ix_approval_notifications_is_read ON approval_notifications(is_read);
CREATE INDEX IF NOT EXISTS ix_approval_notifications_sent_at ON approval_notifications(sent_at);

-- 创建复合索引用于快速查询未读通知
CREATE INDEX IF NOT EXISTS ix_approval_notifications_recipient_unread ON approval_notifications(recipient_id, is_read) WHERE is_read = false;

-- 添加注释
COMMENT ON TABLE approval_workflow_definitions IS '审批工作流定义表';
COMMENT ON TABLE approval_instances IS '审批实例表';
COMMENT ON TABLE approval_history IS '审批历史表';
COMMENT ON TABLE approval_notifications IS '审批通知表';

COMMENT ON COLUMN approval_workflow_definitions.steps IS '审批步骤配置(JSONB格式)';
COMMENT ON COLUMN approval_instances.status IS '审批状态: pending-待审批, in_progress-审批中, approved-已批准, rejected-已拒绝, returned-已退回, cancelled-已取消';
COMMENT ON COLUMN approval_history.action IS '操作类型: submit-提交, approve-批准, reject-拒绝, return-退回, cancel-取消';
COMMENT ON COLUMN approval_notifications.notification_type IS '通知类型: approval_request-审批请求, approval_result-审批结果, approval_reminder-审批提醒';

-- 完成
SELECT 'Approval system tables created successfully!' AS result;


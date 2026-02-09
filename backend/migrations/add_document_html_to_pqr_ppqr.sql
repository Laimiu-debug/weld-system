-- 为PQR和pPQR表添加document_html字段
-- 用于支持文档编辑模式的富文本HTML内容存储

-- 添加document_html字段到pqr表
ALTER TABLE pqr ADD COLUMN IF NOT EXISTS document_html TEXT;
COMMENT ON COLUMN pqr.document_html IS '文档HTML内容（用于文档编辑模式）';

-- 添加document_html字段到ppqr表
ALTER TABLE ppqr ADD COLUMN IF NOT EXISTS document_html TEXT;
COMMENT ON COLUMN ppqr.document_html IS '文档HTML内容（用于文档编辑模式）';


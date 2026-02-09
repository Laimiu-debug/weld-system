-- 添加document_html字段到WPS表
-- 用于存储富文本编辑器生成的HTML内容

ALTER TABLE wps ADD COLUMN IF NOT EXISTS document_html TEXT;

COMMENT ON COLUMN wps.document_html IS '文档HTML内容（用于文档编辑模式）';


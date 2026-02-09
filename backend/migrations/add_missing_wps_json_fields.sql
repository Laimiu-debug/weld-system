-- ============================================================
-- 添加缺失的WPS JSONB字段
-- 添加 header_info 和 diagram_info 字段
-- ============================================================

DO $$ 
BEGIN
    -- 添加 header_info（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='header_info') THEN
        ALTER TABLE wps ADD COLUMN header_info JSONB DEFAULT '{}'::jsonb;
        COMMENT ON COLUMN wps.header_info IS '表头数据（JSON格式）';
        CREATE INDEX idx_wps_header_info ON wps USING GIN (header_info);
        RAISE NOTICE '已添加 header_info 字段';
    ELSE
        RAISE NOTICE 'header_info 字段已存在';
    END IF;

    -- 添加 diagram_info（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='diagram_info') THEN
        ALTER TABLE wps ADD COLUMN diagram_info JSONB DEFAULT '{}'::jsonb;
        COMMENT ON COLUMN wps.diagram_info IS '示意图信息（JSON格式）';
        CREATE INDEX idx_wps_diagram_info ON wps USING GIN (diagram_info);
        RAISE NOTICE '已添加 diagram_info 字段';
    ELSE
        RAISE NOTICE 'diagram_info 字段已存在';
    END IF;

    -- 如果存在 joint_design 字段，可以考虑将数据迁移到 diagram_info
    -- 这里暂时不做数据迁移，保留两个字段
    
END $$;

-- 完成
SELECT 'WPS缺失字段添加完成！' AS message;


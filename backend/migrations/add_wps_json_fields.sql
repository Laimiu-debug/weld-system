-- ============================================================
-- WPS 表结构扩展 - 添加 JSON 字段和数据隔离字段
-- 方案：核心字段 + JSONB 动态字段 + 模板驱动
-- ============================================================

-- 第一步：添加数据隔离字段（如果不存在）
DO $$ 
BEGIN
    -- 添加 user_id（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='user_id') THEN
        ALTER TABLE wps ADD COLUMN user_id INTEGER;
        ALTER TABLE wps ADD CONSTRAINT fk_wps_user 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        CREATE INDEX idx_wps_user_id ON wps(user_id);
    END IF;

    -- 添加 workspace_type（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='workspace_type') THEN
        ALTER TABLE wps ADD COLUMN workspace_type VARCHAR(20) DEFAULT 'personal';
        CREATE INDEX idx_wps_workspace_type ON wps(workspace_type);
    END IF;

    -- 添加 is_shared（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='is_shared') THEN
        ALTER TABLE wps ADD COLUMN is_shared BOOLEAN DEFAULT FALSE;
    END IF;

    -- 添加 access_level（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='access_level') THEN
        ALTER TABLE wps ADD COLUMN access_level VARCHAR(20) DEFAULT 'private';
    END IF;

    -- 添加 created_by（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='created_by') THEN
        ALTER TABLE wps ADD COLUMN created_by INTEGER;
        ALTER TABLE wps ADD CONSTRAINT fk_wps_created_by 
            FOREIGN KEY (created_by) REFERENCES users(id);
    END IF;

    -- 添加 updated_by（如果不存在）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='updated_by') THEN
        ALTER TABLE wps ADD COLUMN updated_by INTEGER;
        ALTER TABLE wps ADD CONSTRAINT fk_wps_updated_by 
            FOREIGN KEY (updated_by) REFERENCES users(id);
    END IF;
END $$;

-- 第二步：迁移现有数据（将 owner_id 复制到 user_id 和 created_by）
UPDATE wps SET user_id = owner_id WHERE user_id IS NULL AND owner_id IS NOT NULL;
UPDATE wps SET created_by = owner_id WHERE created_by IS NULL AND owner_id IS NOT NULL;
UPDATE wps SET workspace_type = 'personal' WHERE workspace_type IS NULL;

-- 第三步：添加新的核心字段
DO $$ 
BEGIN
    -- 模板ID
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='template_id') THEN
        ALTER TABLE wps ADD COLUMN template_id VARCHAR(100);
        COMMENT ON COLUMN wps.template_id IS '使用的模板ID';
    END IF;

    -- 标准
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='standard') THEN
        ALTER TABLE wps ADD COLUMN standard VARCHAR(50);
        COMMENT ON COLUMN wps.standard IS '焊接标准: AWS D1.1, ASME IX, EN ISO 15609-1, GB/T';
        CREATE INDEX idx_wps_standard ON wps(standard);
    END IF;

    -- 产品名称
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='product_name') THEN
        ALTER TABLE wps ADD COLUMN product_name VARCHAR(200);
        COMMENT ON COLUMN wps.product_name IS '产品名称';
    END IF;

    -- 母材2
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='base_material_2') THEN
        ALTER TABLE wps ADD COLUMN base_material_2 VARCHAR(100);
        COMMENT ON COLUMN wps.base_material_2 IS '母材2规格';
    END IF;

    -- 用户/客户
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='customer') THEN
        ALTER TABLE wps ADD COLUMN customer VARCHAR(200);
        COMMENT ON COLUMN wps.customer IS '用户/客户名称';
    END IF;

    -- 订单编号
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='order_number') THEN
        ALTER TABLE wps ADD COLUMN order_number VARCHAR(100);
        COMMENT ON COLUMN wps.order_number IS '订单编号';
    END IF;

    -- 地点
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='location') THEN
        ALTER TABLE wps ADD COLUMN location VARCHAR(200);
        COMMENT ON COLUMN wps.location IS '地点';
    END IF;

    -- 部件编号
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='part_number') THEN
        ALTER TABLE wps ADD COLUMN part_number VARCHAR(100);
        COMMENT ON COLUMN wps.part_number IS '部件编号';
    END IF;

    -- 图纸编号
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='drawing_number') THEN
        ALTER TABLE wps ADD COLUMN drawing_number VARCHAR(100);
        COMMENT ON COLUMN wps.drawing_number IS '图纸编号';
    END IF;

    -- WPQR编号
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='wpqr_number') THEN
        ALTER TABLE wps ADD COLUMN wpqr_number VARCHAR(100);
        COMMENT ON COLUMN wps.wpqr_number IS 'WPQR编号/标准';
    END IF;

    -- 焊工资质
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='welder_qualification') THEN
        ALTER TABLE wps ADD COLUMN welder_qualification VARCHAR(200);
        COMMENT ON COLUMN wps.welder_qualification IS '焊工资质要求';
    END IF;

    -- 制造商
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='manufacturer') THEN
        ALTER TABLE wps ADD COLUMN manufacturer VARCHAR(200);
        COMMENT ON COLUMN wps.manufacturer IS '制造商';
    END IF;

    -- PDF链接
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='pdf_link') THEN
        ALTER TABLE wps ADD COLUMN pdf_link VARCHAR(500);
        COMMENT ON COLUMN wps.pdf_link IS 'WPS PDF文件链接';
    END IF;

    -- 起草人
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='drafted_by') THEN
        ALTER TABLE wps ADD COLUMN drafted_by INTEGER;
        ALTER TABLE wps ADD CONSTRAINT fk_wps_drafted_by 
            FOREIGN KEY (drafted_by) REFERENCES users(id);
    END IF;

    -- 起草日期
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='drafted_date') THEN
        ALTER TABLE wps ADD COLUMN drafted_date TIMESTAMP;
        COMMENT ON COLUMN wps.drafted_date IS '起草日期';
    END IF;
END $$;

-- 第四步：添加 JSONB 字段（核心功能）
DO $$ 
BEGIN
    -- 基本信息（表头数据标签页的其他字段）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='basic_info') THEN
        ALTER TABLE wps ADD COLUMN basic_info JSONB DEFAULT '{}'::jsonb;
        COMMENT ON COLUMN wps.basic_info IS '基本信息（JSON格式）';
        CREATE INDEX idx_wps_basic_info ON wps USING GIN (basic_info);
    END IF;

    -- 概要信息（概要标签页）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='summary_info') THEN
        ALTER TABLE wps ADD COLUMN summary_info JSONB DEFAULT '{}'::jsonb;
        COMMENT ON COLUMN wps.summary_info IS '概要信息（JSON格式）';
        CREATE INDEX idx_wps_summary_info ON wps USING GIN (summary_info);
    END IF;

    -- 接头设计和尺寸（示意图标签页）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='joint_design') THEN
        ALTER TABLE wps ADD COLUMN joint_design JSONB DEFAULT '{}'::jsonb;
        COMMENT ON COLUMN wps.joint_design IS '接头设计和尺寸参数（JSON格式）';
        CREATE INDEX idx_wps_joint_design ON wps USING GIN (joint_design);
    END IF;

    -- 焊层信息（焊层标签页 - 数组）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='weld_layers') THEN
        ALTER TABLE wps ADD COLUMN weld_layers JSONB DEFAULT '[]'::jsonb;
        COMMENT ON COLUMN wps.weld_layers IS '焊层信息数组（JSON格式）';
        CREATE INDEX idx_wps_weld_layers ON wps USING GIN (weld_layers);
    END IF;

    -- 附加信息（附加页面标签页）
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='additional_info') THEN
        ALTER TABLE wps ADD COLUMN additional_info JSONB DEFAULT '{}'::jsonb;
        COMMENT ON COLUMN wps.additional_info IS '附加信息（JSON格式）';
        CREATE INDEX idx_wps_additional_info ON wps USING GIN (additional_info);
    END IF;

    -- 示意图和附件
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='wps' AND column_name='diagrams') THEN
        ALTER TABLE wps ADD COLUMN diagrams JSONB DEFAULT '[]'::jsonb;
        COMMENT ON COLUMN wps.diagrams IS '示意图文件（JSON数组）';
    END IF;
END $$;

-- 第五步：添加索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_wps_welding_process ON wps(welding_process);
CREATE INDEX IF NOT EXISTS idx_wps_status ON wps(status);
CREATE INDEX IF NOT EXISTS idx_wps_company_id ON wps(company_id);
CREATE INDEX IF NOT EXISTS idx_wps_factory_id ON wps(factory_id);
CREATE INDEX IF NOT EXISTS idx_wps_template_id ON wps(template_id);

-- 第六步：添加注释
COMMENT ON COLUMN wps.user_id IS '创建用户ID（数据隔离）';
COMMENT ON COLUMN wps.workspace_type IS '工作区类型: personal/enterprise';
COMMENT ON COLUMN wps.is_shared IS '是否在企业内共享';
COMMENT ON COLUMN wps.access_level IS '访问级别: private/factory/company/public';

-- 完成
SELECT 'WPS表结构扩展完成！' AS message;


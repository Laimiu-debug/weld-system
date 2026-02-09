-- 数据隔离和工作区管理迁移脚本
-- Data Isolation and Workspace Management Migration Script
-- 执行日期: 2025-10-18

-- ============================================================
-- 第一部分：更新现有表，添加数据隔离字段
-- ============================================================

-- 1. 更新 WPS 表
ALTER TABLE wps ADD COLUMN IF NOT EXISTS user_id INTEGER;
ALTER TABLE wps ADD COLUMN IF NOT EXISTS workspace_type VARCHAR(20) DEFAULT 'personal';
ALTER TABLE wps ADD COLUMN IF NOT EXISTS company_id INTEGER;
ALTER TABLE wps ADD COLUMN IF NOT EXISTS factory_id INTEGER;
ALTER TABLE wps ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE;
ALTER TABLE wps ADD COLUMN IF NOT EXISTS access_level VARCHAR(20) DEFAULT 'private';
ALTER TABLE wps ADD COLUMN IF NOT EXISTS created_by INTEGER;
ALTER TABLE wps ADD COLUMN IF NOT EXISTS updated_by INTEGER;

-- 为 WPS 表添加外键约束
ALTER TABLE wps ADD CONSTRAINT fk_wps_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE wps ADD CONSTRAINT fk_wps_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;
ALTER TABLE wps ADD CONSTRAINT fk_wps_factory FOREIGN KEY (factory_id) REFERENCES factories(id) ON DELETE SET NULL;
ALTER TABLE wps ADD CONSTRAINT fk_wps_created_by FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE wps ADD CONSTRAINT fk_wps_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 为 WPS 表添加索引
CREATE INDEX IF NOT EXISTS idx_wps_user_id ON wps(user_id);
CREATE INDEX IF NOT EXISTS idx_wps_workspace_type ON wps(workspace_type);
CREATE INDEX IF NOT EXISTS idx_wps_company_id ON wps(company_id);
CREATE INDEX IF NOT EXISTS idx_wps_factory_id ON wps(factory_id);

-- 迁移 WPS 现有数据：将 owner_id 复制到 user_id 和 created_by
UPDATE wps SET user_id = owner_id WHERE user_id IS NULL AND owner_id IS NOT NULL;
UPDATE wps SET created_by = owner_id WHERE created_by IS NULL AND owner_id IS NOT NULL;

-- 2. 更新 PQR 表
ALTER TABLE pqr ADD COLUMN IF NOT EXISTS user_id INTEGER;
ALTER TABLE pqr ADD COLUMN IF NOT EXISTS workspace_type VARCHAR(20) DEFAULT 'personal';
ALTER TABLE pqr ADD COLUMN IF NOT EXISTS company_id INTEGER;
ALTER TABLE pqr ADD COLUMN IF NOT EXISTS factory_id INTEGER;
ALTER TABLE pqr ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE;
ALTER TABLE pqr ADD COLUMN IF NOT EXISTS access_level VARCHAR(20) DEFAULT 'private';
ALTER TABLE pqr ADD COLUMN IF NOT EXISTS created_by INTEGER;
ALTER TABLE pqr ADD COLUMN IF NOT EXISTS updated_by INTEGER;

-- 为 PQR 表添加外键约束
ALTER TABLE pqr ADD CONSTRAINT fk_pqr_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE pqr ADD CONSTRAINT fk_pqr_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;
ALTER TABLE pqr ADD CONSTRAINT fk_pqr_factory FOREIGN KEY (factory_id) REFERENCES factories(id) ON DELETE SET NULL;
ALTER TABLE pqr ADD CONSTRAINT fk_pqr_created_by FOREIGN KEY (created_by) REFERENCES users(id);
ALTER TABLE pqr ADD CONSTRAINT fk_pqr_updated_by FOREIGN KEY (updated_by) REFERENCES users(id);

-- 为 PQR 表添加索引
CREATE INDEX IF NOT EXISTS idx_pqr_user_id ON pqr(user_id);
CREATE INDEX IF NOT EXISTS idx_pqr_workspace_type ON pqr(workspace_type);
CREATE INDEX IF NOT EXISTS idx_pqr_company_id ON pqr(company_id);
CREATE INDEX IF NOT EXISTS idx_pqr_factory_id ON pqr(factory_id);

-- 迁移 PQR 现有数据
UPDATE pqr SET user_id = owner_id WHERE user_id IS NULL AND owner_id IS NOT NULL;
UPDATE pqr SET created_by = owner_id WHERE created_by IS NULL AND owner_id IS NOT NULL;

-- 3. 更新 Company 表，添加配额使用字段
ALTER TABLE companies ADD COLUMN IF NOT EXISTS wps_quota_used INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS pqr_quota_used INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS ppqr_quota_used INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS storage_quota_used BIGINT DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS max_ppqr_records INTEGER DEFAULT 0;

-- 4. 更新 User 表，添加配额使用字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS ppqr_quota_used INTEGER DEFAULT 0;

-- ============================================================
-- 第二部分：创建新的业务模块表
-- ============================================================

-- 1. 创建 pPQR 表
CREATE TABLE IF NOT EXISTS ppqr (
    id SERIAL PRIMARY KEY,
    
    -- 数据隔离核心字段
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
    is_shared BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(20) DEFAULT 'private',
    
    -- 基本信息
    ppqr_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    planned_test_date DATE,
    actual_test_date DATE,
    company VARCHAR(100),
    project_name VARCHAR(100),
    test_location VARCHAR(100),
    
    -- 试验目的和方案
    purpose TEXT,
    test_plan TEXT,
    expected_results TEXT,
    
    -- 焊接工艺参数（计划）
    welding_process VARCHAR(50),
    process_type VARCHAR(20),
    process_specification VARCHAR(50),
    
    -- 母材信息
    base_material_group VARCHAR(50),
    base_material_spec VARCHAR(50),
    base_material_thickness FLOAT,
    
    -- 填充金属信息
    filler_material_spec VARCHAR(50),
    filler_material_classification VARCHAR(50),
    filler_material_diameter FLOAT,
    
    -- 保护气体信息
    shielding_gas VARCHAR(50),
    gas_flow_rate FLOAT,
    gas_composition VARCHAR(50),
    
    -- 电流参数
    current_type VARCHAR(10),
    current_range VARCHAR(50),
    voltage_range VARCHAR(50),
    
    -- 速度参数
    wire_feed_speed VARCHAR(50),
    welding_speed VARCHAR(50),
    
    -- 热输入
    heat_input_min FLOAT,
    heat_input_max FLOAT,
    
    -- 坡口设计
    joint_design VARCHAR(50),
    groove_type VARCHAR(50),
    groove_angle VARCHAR(50),
    root_gap VARCHAR(50),
    root_face VARCHAR(50),
    
    -- 预热和层间温度
    preheat_temp_min FLOAT,
    preheat_temp_max FLOAT,
    interpass_temp_max FLOAT,
    
    -- 焊后热处理
    pwht_required BOOLEAN DEFAULT FALSE,
    pwht_temperature FLOAT,
    pwht_time FLOAT,
    
    -- 实际参数
    actual_parameters TEXT,
    actual_current FLOAT,
    actual_voltage FLOAT,
    actual_wire_feed_speed FLOAT,
    actual_welding_speed FLOAT,
    actual_heat_input FLOAT,
    actual_preheat_temp FLOAT,
    actual_interpass_temp FLOAT,
    
    -- 环境条件
    ambient_temperature FLOAT,
    humidity FLOAT,
    weather_conditions VARCHAR(100),
    
    -- 试验人员
    welder_id INTEGER,
    welder_name VARCHAR(100),
    welder_certification VARCHAR(100),
    tester_id INTEGER REFERENCES users(id),
    tester_name VARCHAR(100),
    
    -- 试验结果
    is_successful BOOLEAN,
    test_result_summary TEXT,
    visual_inspection_result VARCHAR(20),
    visual_inspection_notes TEXT,
    
    -- 无损检测
    ndt_performed BOOLEAN DEFAULT FALSE,
    rt_result VARCHAR(20),
    ut_result VARCHAR(20),
    mt_result VARCHAR(20),
    pt_result VARCHAR(20),
    
    -- 力学性能测试
    mechanical_testing_performed BOOLEAN DEFAULT FALSE,
    tensile_test_result VARCHAR(20),
    bend_test_result VARCHAR(20),
    charpy_test_result VARCHAR(20),
    hardness_test_result VARCHAR(20),
    
    -- 问题和改进
    issues_found TEXT,
    improvements_needed TEXT,
    lessons_learned TEXT,
    recommendations TEXT,
    
    -- 多组试验
    test_group_number INTEGER DEFAULT 1,
    parent_ppqr_id INTEGER REFERENCES ppqr(id),
    
    -- 转换信息
    converted_to_pqr BOOLEAN DEFAULT FALSE,
    converted_to_pqr_id INTEGER REFERENCES pqr(id),
    converted_at TIMESTAMP,
    converted_by INTEGER REFERENCES users(id),
    
    -- 附件
    test_photos TEXT,
    test_videos TEXT,
    test_reports TEXT,
    attachments TEXT,
    
    -- 协作
    shared_with TEXT,
    comments TEXT,
    
    -- 附加信息
    notes TEXT,
    deviation_notes TEXT,
    
    -- 审计字段
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- 为 pPQR 表添加索引
CREATE INDEX IF NOT EXISTS idx_ppqr_user_id ON ppqr(user_id);
CREATE INDEX IF NOT EXISTS idx_ppqr_workspace_type ON ppqr(workspace_type);
CREATE INDEX IF NOT EXISTS idx_ppqr_company_id ON ppqr(company_id);
CREATE INDEX IF NOT EXISTS idx_ppqr_factory_id ON ppqr(factory_id);
CREATE INDEX IF NOT EXISTS idx_ppqr_number ON ppqr(ppqr_number);
CREATE INDEX IF NOT EXISTS idx_ppqr_status ON ppqr(status);

-- 2. 创建焊材管理表
CREATE TABLE IF NOT EXISTS welding_materials (
    id SERIAL PRIMARY KEY,
    
    -- 数据隔离核心字段
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
    is_shared BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(20) DEFAULT 'private',
    
    -- 基本信息
    material_code VARCHAR(100) NOT NULL,
    material_name VARCHAR(255) NOT NULL,
    material_type VARCHAR(100),
    category VARCHAR(100),
    
    -- 规格信息
    specification VARCHAR(255),
    classification VARCHAR(100),
    diameter FLOAT,
    length FLOAT,
    weight FLOAT,
    
    -- 制造商信息
    manufacturer VARCHAR(255),
    brand VARCHAR(100),
    batch_number VARCHAR(100),
    production_date DATE,
    expiry_date DATE,
    
    -- 库存信息
    quantity FLOAT DEFAULT 0,
    unit VARCHAR(50),
    min_stock_level FLOAT,
    max_stock_level FLOAT,
    reorder_point FLOAT,
    location VARCHAR(255),
    
    -- 价格信息
    unit_price FLOAT,
    currency VARCHAR(10) DEFAULT 'CNY',
    total_value FLOAT,
    
    -- 质量信息
    quality_certificate_number VARCHAR(100),
    quality_status VARCHAR(50),
    inspection_date DATE,
    
    -- 使用信息
    total_used FLOAT DEFAULT 0,
    last_used_date DATE,
    
    -- 附加信息
    description TEXT,
    notes TEXT,
    documents TEXT,
    images TEXT,
    tags TEXT,
    
    -- 审计字段
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_materials_user_id ON welding_materials(user_id);
CREATE INDEX IF NOT EXISTS idx_materials_workspace_type ON welding_materials(workspace_type);
CREATE INDEX IF NOT EXISTS idx_materials_company_id ON welding_materials(company_id);
CREATE INDEX IF NOT EXISTS idx_materials_factory_id ON welding_materials(factory_id);
CREATE INDEX IF NOT EXISTS idx_materials_code ON welding_materials(material_code);

-- 注释：由于内容限制，其他表（焊工、设备、生产、质量）的创建脚本将在后续迁移文件中添加
-- 或者可以通过 SQLAlchemy 的 Base.metadata.create_all() 自动创建

-- ============================================================
-- 第三部分：数据迁移和清理
-- ============================================================

-- 设置现有 WPS 和 PQR 记录的 workspace_type 为 personal
UPDATE wps SET workspace_type = 'personal' WHERE workspace_type IS NULL;
UPDATE pqr SET workspace_type = 'personal' WHERE workspace_type IS NULL;

-- 设置现有记录的 access_level 为 private
UPDATE wps SET access_level = 'private' WHERE access_level IS NULL;
UPDATE pqr SET access_level = 'private' WHERE access_level IS NULL;

-- ============================================================
-- 完成
-- ============================================================

-- 输出迁移完成信息
DO $$
BEGIN
    RAISE NOTICE '数据隔离和工作区管理迁移脚本执行完成';
    RAISE NOTICE '已更新 WPS 和 PQR 表，添加数据隔离字段';
    RAISE NOTICE '已创建 pPQR 和焊材管理表';
    RAISE NOTICE '请使用 SQLAlchemy 创建其他业务模块表';
END $$;


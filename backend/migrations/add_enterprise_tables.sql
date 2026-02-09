-- 企业管理相关表的数据库迁移
-- 创建 companies, factories, company_employees 表

BEGIN;

-- 1. 创建企业表 (companies)
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 会员信息
    membership_tier VARCHAR(50) NOT NULL DEFAULT 'enterprise',  -- enterprise, enterprise_pro, enterprise_pro_max
    
    -- 配额限制
    max_factories INTEGER DEFAULT 1,
    max_employees INTEGER DEFAULT 10,
    max_wps_records INTEGER DEFAULT 200,
    max_pqr_records INTEGER DEFAULT 200,
    
    -- 企业信息
    business_license VARCHAR(255),                              -- 营业执照号码
    contact_person VARCHAR(100),                                -- 联系人
    contact_phone VARCHAR(20),                                  -- 联系电话
    contact_email VARCHAR(255),                                 -- 联系邮箱
    address TEXT,                                               -- 公司地址
    website VARCHAR(255),                                       -- 公司网站
    industry VARCHAR(100),                                      -- 行业类型
    company_size VARCHAR(50),                                   -- 公司规模
    description TEXT,                                           -- 公司描述
    logo_url VARCHAR(500),                                      -- 公司Logo URL
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,                          -- 是否已认证
    
    -- 订阅信息
    subscription_status VARCHAR(50) DEFAULT 'active',           -- active, expired, cancelled
    subscription_start_date TIMESTAMP,
    subscription_end_date TIMESTAMP,
    trial_end_date TIMESTAMP,
    auto_renewal BOOLEAN DEFAULT FALSE,
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- 2. 创建工厂表 (factories)
CREATE TABLE IF NOT EXISTS factories (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- 工厂信息
    name VARCHAR(255) NOT NULL,
    code VARCHAR(100) UNIQUE,                                   -- 工厂编码
    description TEXT,
    
    -- 地址信息
    address TEXT,
    city VARCHAR(100),
    province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'China',
    
    -- 联系信息
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    
    -- 其他信息
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    established_date DATE,                                      -- 成立日期
    certification_info JSONB,                                   -- 认证信息
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_headquarters BOOLEAN DEFAULT FALSE,                      -- 是否为总部
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- 3. 创建企业员工关联表 (company_employees)
CREATE TABLE IF NOT EXISTS company_employees (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 员工信息
    employee_number VARCHAR(100),                               -- 员工编号
    role VARCHAR(50) DEFAULT 'employee',                        -- admin, manager, employee
    status VARCHAR(50) DEFAULT 'active',                        -- active, inactive
    
    -- 分配信息
    factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
    department VARCHAR(100),                                    -- 部门
    position VARCHAR(100),                                      -- 职位
    
    -- 权限
    permissions JSONB,                                          -- 自定义权限配置
    data_access_scope VARCHAR(50) DEFAULT 'factory',            -- factory, company
    
    -- 时间信息
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,              -- 加入时间
    left_at TIMESTAMP,                                          -- 离职时间
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 统计信息
    total_wps_created INTEGER DEFAULT 0,                        -- 创建的 WPS 数量
    total_tasks_completed INTEGER DEFAULT 0,                    -- 完成的任务数量
    last_active_at TIMESTAMP,                                   -- 最后活跃时间
    
    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    
    -- 唯一约束：一个用户在一个企业中只能有一条记录
    UNIQUE(company_id, user_id)
);

-- 4. 创建索引
-- companies 表索引
CREATE INDEX IF NOT EXISTS idx_companies_owner_id ON companies(owner_id);
CREATE INDEX IF NOT EXISTS idx_companies_membership_tier ON companies(membership_tier);
CREATE INDEX IF NOT EXISTS idx_companies_is_active ON companies(is_active);
CREATE INDEX IF NOT EXISTS idx_companies_subscription_status ON companies(subscription_status);

-- factories 表索引
CREATE INDEX IF NOT EXISTS idx_factories_company_id ON factories(company_id);
CREATE INDEX IF NOT EXISTS idx_factories_code ON factories(code);
CREATE INDEX IF NOT EXISTS idx_factories_is_active ON factories(is_active);
CREATE INDEX IF NOT EXISTS idx_factories_location ON factories(city, province);

-- company_employees 表索引
CREATE INDEX IF NOT EXISTS idx_company_employees_company_id ON company_employees(company_id);
CREATE INDEX IF NOT EXISTS idx_company_employees_user_id ON company_employees(user_id);
CREATE INDEX IF NOT EXISTS idx_company_employees_factory_id ON company_employees(factory_id);
CREATE INDEX IF NOT EXISTS idx_company_employees_status ON company_employees(status);
CREATE INDEX IF NOT EXISTS idx_company_employees_role ON company_employees(role);
CREATE INDEX IF NOT EXISTS idx_company_employees_company_user ON company_employees(company_id, user_id);

-- 5. 添加注释
COMMENT ON TABLE companies IS '企业表';
COMMENT ON TABLE factories IS '工厂表';
COMMENT ON TABLE company_employees IS '企业员工关联表';

COMMENT ON COLUMN companies.owner_id IS '企业所有者（创建者）';
COMMENT ON COLUMN companies.membership_tier IS '企业会员等级';
COMMENT ON COLUMN companies.max_factories IS '最大工厂数量';
COMMENT ON COLUMN companies.max_employees IS '最大员工数量';

COMMENT ON COLUMN factories.is_headquarters IS '是否为总部工厂';
COMMENT ON COLUMN factories.certification_info IS '认证信息（JSON格式）';

COMMENT ON COLUMN company_employees.role IS '员工角色：admin-管理员, manager-经理, employee-普通员工';
COMMENT ON COLUMN company_employees.status IS '员工状态：active-在职, inactive-离职';
COMMENT ON COLUMN company_employees.data_access_scope IS '数据访问范围：factory-工厂级, company-企业级';
COMMENT ON COLUMN company_employees.permissions IS '自定义权限配置（JSON格式）';

COMMIT;


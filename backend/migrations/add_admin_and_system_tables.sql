-- 创建管理员相关的数据库表
-- 运行前请确保已连接到正确的数据库

-- 1. 为 users 表添加新字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS membership_type VARCHAR(50) DEFAULT 'personal';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'inactive';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auto_renewal BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS wps_quota_used INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS pqr_quota_used INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS ppqr_quota_used INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS storage_quota_used INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(50);

-- 2. 重建 admins 表（如果存在则先删除）
DROP TABLE IF EXISTS admins CASCADE;

CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 管理员信息
    admin_level VARCHAR(20) DEFAULT 'admin',       -- 级别: super_admin, admin
    permissions JSONB,                             -- 权限列表

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,                -- 是否活跃

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),

    -- 登录相关
    last_login_at TIMESTAMP,

    -- 约束
    UNIQUE (user_id)
);

-- 3. 创建系统公告表
CREATE TABLE IF NOT EXISTS system_announcements (
    id SERIAL PRIMARY KEY,

    -- 公告信息
    title VARCHAR(255) NOT NULL,                   -- 标题
    content TEXT NOT NULL,                         -- 内容
    announcement_type VARCHAR(50),                 -- 类型: info, warning, maintenance
    priority VARCHAR(20) DEFAULT 'normal',         -- 优先级: low, normal, high, urgent

    -- 显示设置
    is_published BOOLEAN DEFAULT FALSE,            -- 是否发布
    is_pinned BOOLEAN DEFAULT FALSE,               -- 是否置顶
    target_audience VARCHAR(50) DEFAULT 'all',     -- 目标受众: all, free, pro, enterprise

    -- 时间设置
    publish_at TIMESTAMP,                          -- 发布时间
    expire_at TIMESTAMP,                           -- 过期时间

    -- 统计
    view_count INTEGER DEFAULT 0,                  -- 查看次数

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- 4. 创建系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,

    -- 日志信息
    log_level VARCHAR(20),                         -- 级别: debug, info, warning, error, critical
    log_type VARCHAR(50),                          -- 类型: api, database, security, system
    message TEXT,                                  -- 消息
    details JSONB,                                 -- 详细信息

    -- 来源信息
    user_id INTEGER REFERENCES users(id),          -- 用户ID
    ip_address VARCHAR(50),                        -- IP 地址
    user_agent TEXT,                               -- 浏览器信息

    -- 请求信息
    request_method VARCHAR(10),                    -- 请求方法
    request_path VARCHAR(500),                     -- 请求路径
    request_params JSONB,                          -- 请求参数
    response_status INTEGER,                       -- 响应状态码
    response_time DECIMAL(10,3),                   -- 响应时间（毫秒）

    -- 错误信息
    error_message TEXT,                            -- 错误消息
    stack_trace TEXT,                              -- 堆栈跟踪

    -- 时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 创建订阅计划表（如果不存在）
CREATE TABLE IF NOT EXISTS subscription_plans (
    id VARCHAR(50) PRIMARY KEY,                    -- 计划ID，如 'personal_pro'
    name VARCHAR(255) NOT NULL,                    -- 计划名称，如 '个人专业版'
    description TEXT,

    -- 价格信息
    monthly_price DECIMAL(10,2) DEFAULT 0,
    quarterly_price DECIMAL(10,2) DEFAULT 0,
    yearly_price DECIMAL(10,2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'CNY',

    -- 功能限制
    max_wps_files INTEGER DEFAULT 0,
    max_pqr_files INTEGER DEFAULT 0,
    max_ppqr_files INTEGER DEFAULT 0,
    max_materials INTEGER DEFAULT 0,
    max_welders INTEGER DEFAULT 0,
    max_equipment INTEGER DEFAULT 0,
    max_factories INTEGER DEFAULT 0,
    max_employees INTEGER DEFAULT 0,

    -- 功能权限
    features TEXT,                                  -- 逗号分隔的功能列表

    -- 排序和显示
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_recommended BOOLEAN DEFAULT FALSE,

    -- 创建和更新时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 创建索引
-- users 表索引
CREATE INDEX IF NOT EXISTS idx_users_membership_tier ON users(member_tier);
CREATE INDEX IF NOT EXISTS idx_users_membership_type ON users(membership_type);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_users_last_login_at ON users(last_login_at);

-- admins 表索引
CREATE INDEX IF NOT EXISTS idx_admins_user_id ON admins(user_id);
CREATE INDEX IF NOT EXISTS idx_admins_admin_level ON admins(admin_level);
CREATE INDEX IF NOT EXISTS idx_admins_is_active ON admins(is_active);

-- system_announcements 表索引
CREATE INDEX IF NOT EXISTS idx_announcements_is_published ON system_announcements(is_published);
CREATE INDEX IF NOT EXISTS idx_announcements_publish_at ON system_announcements(publish_at);
CREATE INDEX IF NOT EXISTS idx_announcements_expire_at ON system_announcements(expire_at);
CREATE INDEX IF NOT EXISTS idx_announcements_type ON system_announcements(announcement_type);

-- system_logs 表索引
CREATE INDEX IF NOT EXISTS idx_logs_log_level ON system_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_logs_log_type ON system_logs(log_type);
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON system_logs(created_at);

-- subscription_plans 表索引
CREATE INDEX IF NOT EXISTS idx_plans_is_active ON subscription_plans(is_active);
CREATE INDEX IF NOT EXISTS idx_plans_sort_order ON subscription_plans(sort_order);

-- 7. 插入默认的订阅计划数据
INSERT INTO subscription_plans (id, name, description, monthly_price, quarterly_price, yearly_price, max_wps_files, max_pqr_files, max_ppqr_files, max_materials, max_welders, max_equipment, features, sort_order, is_recommended) VALUES
('free', '免费版', '适合个人用户基础使用', 0, 0, 0, 10, 10, 0, 0, 0, 0, 'WPS管理,PQR管理', 1, FALSE),
('personal_pro', '专业版', '适合专业焊接工程师', 19, 54, 216, 30, 30, 30, 50, 20, 0, 'WPS管理,PQR管理,pPQR管理,焊材管理,焊工管理', 2, TRUE),
('personal_advanced', '高级版', '适合高级焊接工程师', 49, 141, 564, 50, 50, 50, 100, 50, 20, 'WPS管理,PQR管理,pPQR管理,焊材管理,焊工管理,设备管理', 3, FALSE),
('personal_flagship', '旗舰版', '适合焊接专家和顾问', 99, 285, 1140, 100, 100, 100, 200, 100, 50, 'WPS管理,PQR管理,pPQR管理,焊材管理,焊工管理,设备管理,生产管理,质量管理', 4, FALSE),
('enterprise', '企业版', '适合中小型企业', 299, 861, 3444, 200, 200, 200, 500, 200, 100, 'WPS管理,PQR管理,pPQR管理,焊材管理,焊工管理,设备管理,生产管理,质量管理,报表统计', 5, FALSE),
('enterprise_pro', '企业版PRO', '适合大型企业', 599, 1725, 6900, 500, 500, 500, 1000, 500, 200, 'WPS管理,PQR管理,pPQR管理,焊材管理,焊工管理,设备管理,生产管理,质量管理,报表统计,API接口', 6, FALSE),
('enterprise_pro_max', '企业版PRO MAX', '适合超大型企业', 999, 2877, 11508, 1000, 1000, 1000, 2000, 1000, 500, 'WPS管理,PQR管理,pPQR管理,焊材管理,焊工管理,设备管理,生产管理,质量管理,报表统计,API接口,定制服务', 7, FALSE)
ON CONFLICT (id) DO NOTHING;

-- 8. 创建默认的超级管理员用户
-- 使用用户指定的管理员账号
INSERT INTO users (email, username, hashed_password, full_name, is_active, is_verified, is_superuser, is_admin, member_tier, membership_type, subscription_status, created_at, updated_at) VALUES
('Laimiu.new@gmail.com', 'Laimiu', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', '系统管理员', TRUE, TRUE, TRUE, TRUE, 'enterprise_pro_max', 'enterprise', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (email) DO NOTHING;

-- 9. 为默认管理员创建管理员记录
INSERT INTO admins (user_id, admin_level, is_active, created_at, permissions)
SELECT id, 'super_admin', TRUE, CURRENT_TIMESTAMP, '{"user_management": true, "system_management": true, "membership_management": true, "announcement_management": true, "log_management": true, "config_management": true}'::jsonb
FROM users
WHERE email = 'Laimiu.new@gmail.com'
AND NOT EXISTS (SELECT 1 FROM admins WHERE user_id = users.id);

COMMIT;
-- 添加功能权限字段到users表
ALTER TABLE users ADD COLUMN permissions TEXT;

-- 添加索引（可选）
CREATE INDEX idx_users_permissions ON users USING gin(to_tsvector('simple', permissions));

-- 添加注释
COMMENT ON COLUMN users.permissions IS '用户功能权限（JSON格式）';
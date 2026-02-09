-- 添加user_id字段到admins表
ALTER TABLE admins
ADD COLUMN user_id INTEGER REFERENCES users(id);

-- 添加索引
CREATE INDEX idx_admins_user_id ON admins(user_id);

-- 添加注释
COMMENT ON COLUMN admins.user_id IS '关联的用户ID（可选，如果管理员也是用户）';
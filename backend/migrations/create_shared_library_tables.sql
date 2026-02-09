-- 创建共享库相关的数据库表
-- 执行时间: 2025-01-XX

-- 1. 创建共享模块表
CREATE TABLE IF NOT EXISTS shared_modules (
    id VARCHAR(100) PRIMARY KEY,
    original_module_id VARCHAR(100) NOT NULL,

    -- 基本信息
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT 'BlockOutlined',
    category VARCHAR(20) DEFAULT 'basic',
    repeatable BOOLEAN DEFAULT FALSE,

    -- 字段定义
    fields JSONB NOT NULL DEFAULT '{}',

    -- 共享信息
    uploader_id INTEGER NOT NULL,
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 版本信息
    version VARCHAR(20) DEFAULT '1.0',
    changelog TEXT,

    -- 统计信息
    download_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    dislike_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,

    -- 状态管理
    status VARCHAR(20) DEFAULT 'pending',
    reviewer_id INTEGER,
    review_time TIMESTAMP WITH TIME ZONE,
    review_comment TEXT,

    -- 推荐标记
    is_featured BOOLEAN DEFAULT FALSE,
    featured_order INTEGER DEFAULT 0,

    -- 标签和分类
    tags JSONB DEFAULT '[]',
    difficulty_level VARCHAR(20) DEFAULT 'beginner',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 外键约束
    FOREIGN KEY (original_module_id) REFERENCES custom_modules(id) ON DELETE CASCADE,
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL,

    -- 约束
    CONSTRAINT check_shared_module_status CHECK (status IN ('pending', 'approved', 'rejected', 'removed')),
    CONSTRAINT check_shared_module_category CHECK (category IN ('basic', 'material', 'gas', 'electrical', 'motion', 'equipment', 'calculation')),
    CONSTRAINT check_difficulty_level CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced'))
);

-- 2. 创建共享模板表
CREATE TABLE IF NOT EXISTS shared_templates (
    id VARCHAR(100) PRIMARY KEY,
    original_template_id VARCHAR(100) NOT NULL,

    -- 基本信息
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- 适用范围
    welding_process VARCHAR(50),
    welding_process_name VARCHAR(100),
    standard VARCHAR(50),

    -- 模板配置
    module_instances JSONB NOT NULL,

    -- 共享信息
    uploader_id INTEGER NOT NULL,
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 版本信息
    version VARCHAR(20) DEFAULT '1.0',
    changelog TEXT,

    -- 统计信息
    download_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    dislike_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,

    -- 状态管理
    status VARCHAR(20) DEFAULT 'pending',
    reviewer_id INTEGER,
    review_time TIMESTAMP WITH TIME ZONE,
    review_comment TEXT,

    -- 推荐标记
    is_featured BOOLEAN DEFAULT FALSE,
    featured_order INTEGER DEFAULT 0,

    -- 标签和分类
    tags JSONB DEFAULT '[]',
    difficulty_level VARCHAR(20) DEFAULT 'beginner',
    industry_type VARCHAR(50),

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 外键约束
    FOREIGN KEY (original_template_id) REFERENCES wps_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL,

    -- 约束
    CONSTRAINT check_shared_template_status CHECK (status IN ('pending', 'approved', 'rejected', 'removed')),
    CONSTRAINT check_shared_template_difficulty CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced'))
);

-- 3. 创建用户评分表
CREATE TABLE IF NOT EXISTS user_ratings (
    id VARCHAR(100) PRIMARY KEY,
    user_id INTEGER NOT NULL,

    -- 评分对象
    target_type VARCHAR(20) NOT NULL,
    target_id VARCHAR(100) NOT NULL,

    -- 评分类型
    rating_type VARCHAR(10) NOT NULL,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- 约束
    CONSTRAINT check_rating_type CHECK (rating_type IN ('like', 'dislike')),
    CONSTRAINT check_target_type CHECK (target_type IN ('module', 'template')),

    -- 唯一约束：一个用户对同一个资源只能有一个评分
    UNIQUE(user_id, target_type, target_id)
);

-- 4. 创建下载记录表
CREATE TABLE IF NOT EXISTS shared_downloads (
    id VARCHAR(100) PRIMARY KEY,
    user_id INTEGER NOT NULL,

    -- 下载对象
    target_type VARCHAR(20) NOT NULL,
    target_id VARCHAR(100) NOT NULL,

    -- 下载信息
    download_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address VARCHAR(45),

    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- 约束
    CONSTRAINT check_download_target_type CHECK (target_type IN ('module', 'template'))
);

-- 5. 创建评论表
CREATE TABLE IF NOT EXISTS shared_comments (
    id VARCHAR(100) PRIMARY KEY,
    user_id INTEGER NOT NULL,

    -- 评论对象
    target_type VARCHAR(20) NOT NULL,
    target_id VARCHAR(100) NOT NULL,

    -- 评论内容
    content TEXT NOT NULL,
    parent_id VARCHAR(100),

    -- 状态
    status VARCHAR(20) DEFAULT 'active',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES shared_comments(id) ON DELETE CASCADE,

    -- 约束
    CONSTRAINT check_comment_target_type CHECK (target_type IN ('module', 'template')),
    CONSTRAINT check_comment_status CHECK (status IN ('active', 'hidden', 'deleted'))
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_shared_modules_status ON shared_modules(status);
CREATE INDEX IF NOT EXISTS idx_shared_modules_uploader ON shared_modules(uploader_id);
CREATE INDEX IF NOT EXISTS idx_shared_modules_category ON shared_modules(category);
CREATE INDEX IF NOT EXISTS idx_shared_modules_featured ON shared_modules(is_featured, featured_order);
CREATE INDEX IF NOT EXISTS idx_shared_modules_tags ON shared_modules USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_shared_templates_status ON shared_templates(status);
CREATE INDEX IF NOT EXISTS idx_shared_templates_uploader ON shared_templates(uploader_id);
CREATE INDEX IF NOT EXISTS idx_shared_templates_process ON shared_templates(welding_process);
CREATE INDEX IF NOT EXISTS idx_shared_templates_featured ON shared_templates(is_featured, featured_order);
CREATE INDEX IF NOT EXISTS idx_shared_templates_tags ON shared_templates USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_user_ratings_target ON user_ratings(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_user_ratings_user ON user_ratings(user_id);

CREATE INDEX IF NOT EXISTS idx_shared_downloads_target ON shared_downloads(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_shared_downloads_user ON shared_downloads(user_id);
CREATE INDEX IF NOT EXISTS idx_shared_downloads_time ON shared_downloads(download_time);

CREATE INDEX IF NOT EXISTS idx_shared_comments_target ON shared_comments(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_shared_comments_user ON shared_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_shared_comments_parent ON shared_comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_shared_comments_status ON shared_comments(status);
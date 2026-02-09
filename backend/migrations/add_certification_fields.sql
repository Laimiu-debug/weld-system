-- 添加焊工证书表的新字段
-- 添加认证体系、项目名称和复审相关字段

BEGIN;

-- 1. 添加认证体系和项目名称字段
ALTER TABLE welder_certifications
ADD COLUMN IF NOT EXISTS certification_system VARCHAR(50);

ALTER TABLE welder_certifications
ADD COLUMN IF NOT EXISTS project_name VARCHAR(200);

-- 2. 添加复审相关字段
ALTER TABLE welder_certifications
ADD COLUMN IF NOT EXISTS renewal_result VARCHAR(50);

ALTER TABLE welder_certifications
ADD COLUMN IF NOT EXISTS renewal_notes TEXT;

-- 3. 添加字段注释
COMMENT ON COLUMN welder_certifications.certification_system IS '认证体系';
COMMENT ON COLUMN welder_certifications.project_name IS '项目名称';
COMMENT ON COLUMN welder_certifications.renewal_result IS '复审结果';
COMMENT ON COLUMN welder_certifications.renewal_notes IS '复审备注';

-- 4. 更新现有字段注释
COMMENT ON COLUMN welder_certifications.renewal_date IS '最近复审日期';
COMMENT ON COLUMN welder_certifications.renewal_count IS '复审次数';
COMMENT ON COLUMN welder_certifications.next_renewal_date IS '下次复审日期';

-- 5. 创建索引以支持按认证体系和项目查询
CREATE INDEX IF NOT EXISTS idx_welder_certifications_system
ON welder_certifications(certification_system);

CREATE INDEX IF NOT EXISTS idx_welder_certifications_process
ON welder_certifications(qualified_process);

CREATE INDEX IF NOT EXISTS idx_welder_certifications_material
ON welder_certifications(qualified_material_group);

CREATE INDEX IF NOT EXISTS idx_welder_certifications_position
ON welder_certifications(qualified_position);

-- 6. 创建复合索引以支持焊工自动匹配查询
CREATE INDEX IF NOT EXISTS idx_welder_certifications_matching
ON welder_certifications(welder_id, status, qualified_process, qualified_material_group, qualified_position)
WHERE is_active = true AND status = 'valid';

COMMIT;


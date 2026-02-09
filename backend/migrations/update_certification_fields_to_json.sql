-- 更新证书表字段：将合格项目和合格范围改为JSON格式
-- 执行日期: 2025-01-XX

-- 1. 添加新的JSON字段
ALTER TABLE welder_certifications 
ADD COLUMN IF NOT EXISTS qualified_items TEXT COMMENT '合格项目列表（JSON格式）';

ALTER TABLE welder_certifications 
ADD COLUMN IF NOT EXISTS qualified_range TEXT COMMENT '合格范围列表（JSON格式）';

-- 2. 迁移现有数据到新字段（如果有数据的话）
-- 将旧的合格项目字段合并到JSON格式
UPDATE welder_certifications 
SET qualified_items = JSON_ARRAY(
    JSON_OBJECT(
        'item', CONCAT_WS('-', 
            COALESCE(qualified_process, ''),
            COALESCE(qualified_material_group, ''),
            COALESCE(qualified_position, '')
        ),
        'description', '',
        'notes', ''
    )
)
WHERE qualified_process IS NOT NULL 
   OR qualified_material_group IS NOT NULL 
   OR qualified_position IS NOT NULL;

-- 将旧的合格范围字段合并到JSON格式
UPDATE welder_certifications 
SET qualified_range = JSON_ARRAY(
    IF(qualified_thickness_range IS NOT NULL, 
        JSON_OBJECT('name', '厚度范围', 'value', qualified_thickness_range, 'notes', ''),
        NULL
    ),
    IF(qualified_diameter_range IS NOT NULL,
        JSON_OBJECT('name', '直径范围', 'value', qualified_diameter_range, 'notes', ''),
        NULL
    ),
    IF(qualified_filler_material IS NOT NULL,
        JSON_OBJECT('name', '填充材料', 'value', qualified_filler_material, 'notes', ''),
        NULL
    )
)
WHERE qualified_thickness_range IS NOT NULL 
   OR qualified_diameter_range IS NOT NULL 
   OR qualified_filler_material IS NOT NULL;

-- 3. 删除旧字段（可选，建议先备份数据）
-- 注释掉这些语句，等确认新字段工作正常后再执行
-- ALTER TABLE welder_certifications DROP COLUMN IF EXISTS qualified_process;
-- ALTER TABLE welder_certifications DROP COLUMN IF EXISTS qualified_material_group;
-- ALTER TABLE welder_certifications DROP COLUMN IF EXISTS qualified_position;
-- ALTER TABLE welder_certifications DROP COLUMN IF EXISTS qualified_thickness_range;
-- ALTER TABLE welder_certifications DROP COLUMN IF EXISTS qualified_diameter_range;
-- ALTER TABLE welder_certifications DROP COLUMN IF EXISTS qualified_filler_material;

-- 4. 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_welder_certifications_qualified_items 
ON welder_certifications(qualified_items(100));

CREATE INDEX IF NOT EXISTS idx_welder_certifications_qualified_range 
ON welder_certifications(qualified_range(100));

-- 完成
SELECT 'Migration completed successfully' AS status;


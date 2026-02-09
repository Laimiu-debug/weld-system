-- ============================================================================
-- 迁移脚本：为custom_modules表添加module_type字段
-- 目的：扩展自定义模块系统以支持WPS、PQR、pPQR三种记录类型
-- 创建日期：2025-10-25
-- ============================================================================

-- 开始事务
BEGIN;

-- ============================================================================
-- 第一步：添加module_type字段
-- ============================================================================
DO $$
BEGIN
    -- 检查字段是否已存在
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'custom_modules' 
        AND column_name = 'module_type'
    ) THEN
        -- 添加module_type字段，默认值为'wps'
        ALTER TABLE custom_modules 
        ADD COLUMN module_type VARCHAR(20) DEFAULT 'wps';
        
        RAISE NOTICE '✓ 已添加module_type字段';
    ELSE
        RAISE NOTICE '⊙ module_type字段已存在，跳过';
    END IF;
END $$;

-- ============================================================================
-- 第二步：更新现有数据
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    -- 将所有现有模块标记为WPS类型
    UPDATE custom_modules 
    SET module_type = 'wps' 
    WHERE module_type IS NULL OR module_type = '';
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE '✓ 已更新 % 条现有记录的module_type为wps', updated_count;
END $$;

-- ============================================================================
-- 第三步：设置NOT NULL约束
-- ============================================================================
DO $$
BEGIN
    -- 设置module_type为NOT NULL
    ALTER TABLE custom_modules 
    ALTER COLUMN module_type SET NOT NULL;
    
    RAISE NOTICE '✓ 已设置module_type为NOT NULL';
END $$;

-- ============================================================================
-- 第四步：删除旧的category约束（如果存在）
-- ============================================================================
DO $$
BEGIN
    -- 删除旧的check_category约束
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_category' 
        AND table_name = 'custom_modules'
    ) THEN
        ALTER TABLE custom_modules 
        DROP CONSTRAINT check_category;
        
        RAISE NOTICE '✓ 已删除旧的check_category约束';
    ELSE
        RAISE NOTICE '⊙ check_category约束不存在，跳过';
    END IF;
END $$;

-- ============================================================================
-- 第五步：添加module_type检查约束
-- ============================================================================
DO $$
BEGIN
    -- 删除旧约束（如果存在）
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_module_type' 
        AND table_name = 'custom_modules'
    ) THEN
        ALTER TABLE custom_modules 
        DROP CONSTRAINT check_module_type;
    END IF;
    
    -- 添加新的module_type约束
    ALTER TABLE custom_modules 
    ADD CONSTRAINT check_module_type CHECK (
        module_type IN ('wps', 'pqr', 'ppqr', 'common')
    );
    
    RAISE NOTICE '✓ 已添加check_module_type约束';
END $$;

-- ============================================================================
-- 第六步：迁移现有模块的category到新的通用分类（在添加约束之前）
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    -- 映射旧分类到新分类
    -- basic -> basic (保持不变)
    UPDATE custom_modules SET category = 'basic' WHERE category = 'basic';

    -- material, gas -> materials
    UPDATE custom_modules SET category = 'materials' WHERE category IN ('material', 'gas');

    -- electrical, motion -> parameters
    UPDATE custom_modules SET category = 'parameters' WHERE category IN ('electrical', 'motion');

    -- equipment -> equipment (保持不变)
    UPDATE custom_modules SET category = 'equipment' WHERE category = 'equipment';

    -- calculation -> results
    UPDATE custom_modules SET category = 'results' WHERE category = 'calculation';

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE '✓ 已迁移category分类';
END $$;

-- ============================================================================
-- 第七步：添加新的category检查约束（更通用的分类）
-- ============================================================================
DO $$
BEGIN
    -- 添加新的category约束
    ALTER TABLE custom_modules
    ADD CONSTRAINT check_category CHECK (
        category IN (
            'basic',        -- 基本信息
            'parameters',   -- 参数信息
            'materials',    -- 材料信息
            'tests',        -- 测试/试验
            'results',      -- 结果/评价
            'equipment',    -- 设备信息
            'attachments',  -- 附件
            'notes'         -- 备注
        )
    );

    RAISE NOTICE '✓ 已添加新的check_category约束';
END $$;

-- ============================================================================
-- 第八步：创建module_type索引
-- ============================================================================
DO $$
BEGIN
    -- 检查索引是否已存在
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE indexname = 'idx_custom_modules_module_type'
    ) THEN
        CREATE INDEX idx_custom_modules_module_type 
        ON custom_modules(module_type);
        
        RAISE NOTICE '✓ 已创建idx_custom_modules_module_type索引';
    ELSE
        RAISE NOTICE '⊙ idx_custom_modules_module_type索引已存在，跳过';
    END IF;
END $$;

-- ============================================================================
-- 第九步：创建组合索引（module_type + category）
-- ============================================================================
DO $$
BEGIN
    -- 检查索引是否已存在
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE indexname = 'idx_custom_modules_type_category'
    ) THEN
        CREATE INDEX idx_custom_modules_type_category 
        ON custom_modules(module_type, category);
        
        RAISE NOTICE '✓ 已创建idx_custom_modules_type_category组合索引';
    ELSE
        RAISE NOTICE '⊙ idx_custom_modules_type_category索引已存在，跳过';
    END IF;
END $$;

-- ============================================================================
-- 第十步：验证迁移结果
-- ============================================================================
DO $$
DECLARE
    total_count INTEGER;
    wps_count INTEGER;
    null_count INTEGER;
BEGIN
    -- 统计总数
    SELECT COUNT(*) INTO total_count FROM custom_modules;
    
    -- 统计WPS类型数量
    SELECT COUNT(*) INTO wps_count FROM custom_modules WHERE module_type = 'wps';
    
    -- 统计NULL数量（应该为0）
    SELECT COUNT(*) INTO null_count FROM custom_modules WHERE module_type IS NULL;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE '迁移验证结果：';
    RAISE NOTICE '  总模块数：%', total_count;
    RAISE NOTICE '  WPS类型：%', wps_count;
    RAISE NOTICE '  NULL值：% (应为0)', null_count;
    RAISE NOTICE '========================================';
    
    -- 如果有NULL值，回滚事务
    IF null_count > 0 THEN
        RAISE EXCEPTION '发现NULL值，迁移失败！';
    END IF;
END $$;

-- 提交事务
COMMIT;

-- ============================================================================
-- 迁移完成
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✓✓✓ 迁移成功完成！';
    RAISE NOTICE '现在custom_modules表支持以下module_type：';
    RAISE NOTICE '  - wps: WPS模块';
    RAISE NOTICE '  - pqr: PQR模块';
    RAISE NOTICE '  - ppqr: pPQR模块';
    RAISE NOTICE '  - common: 通用模块（可用于所有类型）';
END $$;


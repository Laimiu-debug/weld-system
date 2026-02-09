-- 创建企业角色表
CREATE TABLE IF NOT EXISTS company_roles (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50),
    description TEXT,
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    data_access_scope VARCHAR(50) DEFAULT 'factory',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_company_roles_company_id ON company_roles(company_id);
CREATE INDEX IF NOT EXISTS idx_company_roles_code ON company_roles(code);

-- 添加 company_role_id 列到 company_employees 表（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'company_employees' 
        AND column_name = 'company_role_id'
    ) THEN
        ALTER TABLE company_employees 
        ADD COLUMN company_role_id INTEGER REFERENCES company_roles(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 为每个企业创建默认角色
DO $$
DECLARE
    company_record RECORD;
    admin_role_id INTEGER;
    manager_role_id INTEGER;
    employee_role_id INTEGER;
BEGIN
    FOR company_record IN 
        SELECT id, name, owner_id FROM companies WHERE is_active = TRUE
    LOOP
        -- 检查是否已有角色
        IF NOT EXISTS (
            SELECT 1 FROM company_roles WHERE company_id = company_record.id
        ) THEN
            -- 创建企业管理员角色
            INSERT INTO company_roles (
                company_id, name, code, description, permissions, 
                data_access_scope, is_system, created_by
            ) VALUES (
                company_record.id,
                '企业管理员',
                'ADMIN',
                '拥有所有权限的管理员角色',
                '{"wps_management": {"view": true, "create": true, "edit": true, "delete": true}, "pqr_management": {"view": true, "create": true, "edit": true, "delete": true}, "ppqr_management": {"view": true, "create": true, "edit": true, "delete": true}, "equipment_management": {"view": true, "create": true, "edit": true, "delete": true}, "materials_management": {"view": true, "create": true, "edit": true, "delete": true}, "welders_management": {"view": true, "create": true, "edit": true, "delete": true}, "employee_management": {"view": true, "create": true, "edit": true, "delete": true}, "factory_management": {"view": true, "create": true, "edit": true, "delete": true}, "department_management": {"view": true, "create": true, "edit": true, "delete": true}, "role_management": {"view": true, "create": true, "edit": true, "delete": true}, "reports_management": {"view": true, "create": true, "edit": true, "delete": true}}'::jsonb,
                'company',
                true,
                company_record.owner_id
            ) RETURNING id INTO admin_role_id;
            
            -- 创建部门经理角色
            INSERT INTO company_roles (
                company_id, name, code, description, permissions, 
                data_access_scope, is_system, created_by
            ) VALUES (
                company_record.id,
                '部门经理',
                'MANAGER',
                '部门经理，可以管理本部门的数据',
                '{"wps_management": {"view": true, "create": true, "edit": true, "delete": false}, "pqr_management": {"view": true, "create": true, "edit": true, "delete": false}, "ppqr_management": {"view": true, "create": true, "edit": true, "delete": false}, "equipment_management": {"view": true, "create": true, "edit": true, "delete": false}, "materials_management": {"view": true, "create": true, "edit": false, "delete": false}, "welders_management": {"view": true, "create": false, "edit": false, "delete": false}, "employee_management": {"view": true, "create": false, "edit": false, "delete": false}, "factory_management": {"view": true, "create": false, "edit": false, "delete": false}, "department_management": {"view": true, "create": false, "edit": false, "delete": false}, "role_management": {"view": false, "create": false, "edit": false, "delete": false}, "reports_management": {"view": true, "create": true, "edit": false, "delete": false}}'::jsonb,
                'factory',
                true,
                company_record.owner_id
            ) RETURNING id INTO manager_role_id;
            
            -- 创建普通员工角色
            INSERT INTO company_roles (
                company_id, name, code, description, permissions, 
                data_access_scope, is_system, created_by
            ) VALUES (
                company_record.id,
                '普通员工',
                'EMPLOYEE',
                '普通员工，只能查看和创建基本数据',
                '{"wps_management": {"view": true, "create": true, "edit": false, "delete": false}, "pqr_management": {"view": true, "create": true, "edit": false, "delete": false}, "ppqr_management": {"view": true, "create": false, "edit": false, "delete": false}, "equipment_management": {"view": true, "create": false, "edit": false, "delete": false}, "materials_management": {"view": true, "create": false, "edit": false, "delete": false}, "welders_management": {"view": true, "create": false, "edit": false, "delete": false}, "employee_management": {"view": false, "create": false, "edit": false, "delete": false}, "factory_management": {"view": false, "create": false, "edit": false, "delete": false}, "department_management": {"view": false, "create": false, "edit": false, "delete": false}, "role_management": {"view": false, "create": false, "edit": false, "delete": false}, "reports_management": {"view": true, "create": false, "edit": false, "delete": false}}'::jsonb,
                'factory',
                true,
                company_record.owner_id
            ) RETURNING id INTO employee_role_id;
            
            -- 将企业所有者分配到管理员角色
            UPDATE company_employees 
            SET company_role_id = admin_role_id
            WHERE company_id = company_record.id 
            AND user_id = company_record.owner_id
            AND role = 'admin';
            
            RAISE NOTICE '为企业 % (ID: %) 创建了默认角色', company_record.name, company_record.id;
        END IF;
    END LOOP;
END $$;


-- Update production_tasks table schema to match the SQLAlchemy model
-- This migration updates the existing production_tasks table to match the new model structure

BEGIN;

-- First, create a backup of existing data
CREATE TABLE production_tasks_backup AS SELECT * FROM production_tasks;

-- Add missing columns to production_tasks table
ALTER TABLE production_tasks
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS access_level VARCHAR(20) DEFAULT 'private',
ADD COLUMN IF NOT EXISTS task_number VARCHAR(100) NOT NULL UNIQUE,
ADD COLUMN IF NOT EXISTS task_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS project_code VARCHAR(100),
ADD COLUMN IF NOT EXISTS pqr_id INTEGER REFERENCES pqr(id),
ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS customer_code VARCHAR(100),
ADD COLUMN IF NOT EXISTS planned_start_date DATE,
ADD COLUMN IF NOT EXISTS planned_end_date DATE,
ADD COLUMN IF NOT EXISTS actual_start_date DATE,
ADD COLUMN IF NOT EXISTS actual_end_date DATE,
ADD COLUMN IF NOT EXISTS estimated_duration_hours FLOAT,
ADD COLUMN IF NOT EXISTS actual_duration_hours FLOAT,
ADD COLUMN IF NOT EXISTS priority VARCHAR(50) DEFAULT 'normal',
ADD COLUMN IF NOT EXISTS progress_percentage FLOAT DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS assigned_welder_id INTEGER REFERENCES welders(id),
ADD COLUMN IF NOT EXISTS assigned_equipment_id INTEGER REFERENCES equipment(id),
ADD COLUMN IF NOT EXISTS team_leader_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS team_members TEXT,
ADD COLUMN IF NOT EXISTS work_description TEXT,
ADD COLUMN IF NOT EXISTS technical_requirements TEXT,
ADD COLUMN IF NOT EXISTS quality_requirements TEXT,
ADD COLUMN IF NOT EXISTS safety_requirements TEXT,
ADD COLUMN IF NOT EXISTS planned_quantity FLOAT,
ADD COLUMN IF NOT EXISTS completed_quantity FLOAT DEFAULT 0,
ADD COLUMN IF NOT EXISTS weld_length_planned FLOAT,
ADD COLUMN IF NOT EXISTS weld_length_actual FLOAT,
ADD COLUMN IF NOT EXISTS base_material VARCHAR(255),
ADD COLUMN IF NOT EXISTS filler_material VARCHAR(255),
ADD COLUMN IF NOT EXISTS material_thickness FLOAT,
ADD COLUMN IF NOT EXISTS material_quantity FLOAT,
ADD COLUMN IF NOT EXISTS estimated_cost FLOAT,
ADD COLUMN IF NOT EXISTS actual_cost FLOAT,
ADD COLUMN IF NOT EXISTS labor_cost FLOAT,
ADD COLUMN IF NOT EXISTS material_cost FLOAT,
ADD COLUMN IF NOT EXISTS equipment_cost FLOAT,
ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY',
ADD COLUMN IF NOT EXISTS quality_inspection_required BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS inspection_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS quality_result VARCHAR(50),
ADD COLUMN IF NOT EXISTS defect_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS rework_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS drawings TEXT,
ADD COLUMN IF NOT EXISTS documents TEXT,
ADD COLUMN IF NOT EXISTS images TEXT,
ADD COLUMN IF NOT EXISTS tags TEXT,
ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id) NOT NULL,
ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

-- Migrate data from owner_id to user_id if user_id is NULL
UPDATE production_tasks
SET user_id = owner_id
WHERE user_id IS NULL AND owner_id IS NOT NULL;

-- Set created_by field from owner_id if it's NULL
UPDATE production_tasks
SET created_by = owner_id
WHERE created_by IS NULL AND owner_id IS NOT NULL;

-- Generate task numbers for existing records
UPDATE production_tasks
SET task_number = 'TASK-' || LPAD(id::text, 6, '0')
WHERE task_number IS NULL OR task_number = '';

-- Make sure required columns are properly set
ALTER TABLE production_tasks
ALTER COLUMN user_id SET NOT NULL,
ALTER COLUMN task_number SET NOT NULL,
ALTER COLUMN task_name SET NOT NULL,
ALTER COLUMN created_by SET NOT NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_production_tasks_user_id ON production_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_production_tasks_workspace_type ON production_tasks(workspace_type);
CREATE INDEX IF NOT EXISTS idx_production_tasks_company_id ON production_tasks(company_id);
CREATE INDEX IF NOT EXISTS idx_production_tasks_factory_id ON production_tasks(factory_id);
CREATE INDEX IF NOT EXISTS idx_production_tasks_task_number ON production_tasks(task_number);
CREATE INDEX IF NOT EXISTS idx_production_tasks_status ON production_tasks(status);
CREATE INDEX IF NOT EXISTS idx_production_tasks_is_active ON production_tasks(is_active);

-- Drop the old owner_id column after migration (optional - keep for reference)
-- ALTER TABLE production_tasks DROP COLUMN IF EXISTS owner_id;

COMMIT;
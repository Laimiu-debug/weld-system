-- Migration: Add modules_data JSONB field to WPS table
-- Purpose: Support flexible, unlimited custom module data storage
-- Date: 2025-10-23

-- Add the new modules_data column to store all module data
-- Structure: { "module_instance_id": { "moduleId": "...", "customName": "...", "data": {...} }, ... }
ALTER TABLE wps
ADD COLUMN IF NOT EXISTS modules_data JSONB DEFAULT '{}' NOT NULL;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_wps_modules_data ON wps USING GIN (modules_data);

-- Add comment
COMMENT ON COLUMN wps.modules_data IS 'Complete module data storage (JSON format), supports unlimited custom modules. Structure: { "module_instance_id": { "moduleId": "...", "customName": "...", "data": {...} }, ... }';

-- Migration complete
SELECT 'Migration: add_modules_data_field completed successfully' AS status;


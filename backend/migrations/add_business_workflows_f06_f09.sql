-- Additive migration. Execute against the intended schema before deploying F06-F09.
-- Existing plans/inspections/reviews remain unlinked; historical standards are not invented.
BEGIN;
ALTER TABLE production_tasks ADD COLUMN IF NOT EXISTS plan_id INTEGER REFERENCES production_plans(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS ix_production_tasks_plan_id ON production_tasks(plan_id);
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS standard_id INTEGER REFERENCES quality_standards(id) ON DELETE RESTRICT;
ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS standard_snapshot JSONB;
CREATE INDEX IF NOT EXISTS ix_quality_inspections_standard_id ON quality_inspections(standard_id);
ALTER TABLE employee_performances ADD COLUMN IF NOT EXISTS adjustment_reason TEXT;
ALTER TABLE employee_performances ADD COLUMN IF NOT EXISTS evidence_snapshot JSONB;
ALTER TABLE report_templates ADD COLUMN IF NOT EXISTS group_by VARCHAR(100);
COMMIT;

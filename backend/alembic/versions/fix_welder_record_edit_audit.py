"""Add update audit fields for editable welder career records.

Revision ID: fix_welder_record_edit_audit
Revises: add_platform_ai_model_routing
"""
from alembic import op
import sqlalchemy as sa


revision = "fix_welder_record_edit_audit"
down_revision = "add_platform_ai_model_routing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        ALTER TABLE welder_training_records ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);
        ALTER TABLE welder_work_records ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);
        ALTER TABLE welder_work_records ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP;
        ALTER TABLE welder_assessment_records ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);
        ALTER TABLE welder_work_histories ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);
        ALTER TABLE equipment ADD COLUMN IF NOT EXISTS maintenance_base_date DATE;
        ALTER TABLE equipment ADD COLUMN IF NOT EXISTS maintenance_warning_days INTEGER NOT NULL DEFAULT 30;
        ALTER TABLE equipment ADD COLUMN IF NOT EXISTS maintenance_plan_type VARCHAR(50) NOT NULL DEFAULT 'routine';
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        ALTER TABLE welder_work_histories DROP COLUMN IF EXISTS updated_by;
        ALTER TABLE welder_assessment_records DROP COLUMN IF EXISTS updated_by;
        ALTER TABLE welder_work_records DROP COLUMN IF EXISTS updated_at;
        ALTER TABLE welder_work_records DROP COLUMN IF EXISTS updated_by;
        ALTER TABLE welder_training_records DROP COLUMN IF EXISTS updated_by;
        ALTER TABLE equipment DROP COLUMN IF EXISTS maintenance_plan_type;
        ALTER TABLE equipment DROP COLUMN IF EXISTS maintenance_warning_days;
        ALTER TABLE equipment DROP COLUMN IF EXISTS maintenance_base_date;
    """))

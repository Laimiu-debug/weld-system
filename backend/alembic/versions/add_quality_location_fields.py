"""Add quality inspection location hierarchy fields.

Revision ID: add_quality_location_fields
Revises: add_welder_certified_projects
Create Date: 2026-08-20
"""
from alembic import op

revision = "add_quality_location_fields"
down_revision = "add_welder_certified_projects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS inspection_type VARCHAR(50)"
    )
    op.execute(
        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS inspector_name VARCHAR(100)"
    )
    op.execute(
        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS project_name VARCHAR(200)"
    )
    op.execute(
        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS vessel_no VARCHAR(100)"
    )
    op.execute(
        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS work_order_no VARCHAR(100)"
    )
    op.execute(
        "ALTER TABLE quality_inspections ADD COLUMN IF NOT EXISTS weld_joint_number VARCHAR(100)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_quality_inspections_vessel_no ON quality_inspections (vessel_no)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_quality_inspections_work_order_no ON quality_inspections (work_order_no)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_quality_inspections_weld_joint_number ON quality_inspections (weld_joint_number)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_quality_inspections_weld_joint_number")
    op.execute("DROP INDEX IF EXISTS ix_quality_inspections_work_order_no")
    op.execute("DROP INDEX IF EXISTS ix_quality_inspections_vessel_no")
    op.execute("ALTER TABLE quality_inspections DROP COLUMN IF EXISTS weld_joint_number")
    op.execute("ALTER TABLE quality_inspections DROP COLUMN IF EXISTS work_order_no")
    op.execute("ALTER TABLE quality_inspections DROP COLUMN IF EXISTS vessel_no")
    op.execute("ALTER TABLE quality_inspections DROP COLUMN IF EXISTS project_name")
    op.execute("ALTER TABLE quality_inspections DROP COLUMN IF EXISTS inspector_name")
    op.execute("ALTER TABLE quality_inspections DROP COLUMN IF EXISTS inspection_type")

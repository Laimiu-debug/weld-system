"""Add company employee lookup index for approval permission checks.

Revision ID: add_employee_approve_index
Revises: add_equipment_records
Create Date: 2026-08-19
"""
from alembic import op

revision = "add_employee_approve_index"
down_revision = "add_equipment_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_company_employees_user_company_status "
        "ON company_employees (user_id, company_id, status)"
    )


def downgrade() -> None:
    op.drop_index("ix_company_employees_user_company_status", table_name="company_employees")

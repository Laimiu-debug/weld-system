"""Create equipment maintenance and usage record tables.

Revision ID: add_equipment_records
Revises: add_list_query_indexes
Create Date: 2026-08-19
"""
from alembic import op

revision = "add_equipment_records"
down_revision = "add_list_query_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS equipment_maintenance_records (
            id SERIAL PRIMARY KEY,
            equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
            factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
            maintenance_code VARCHAR(100),
            maintenance_type VARCHAR(50) NOT NULL,
            maintenance_category VARCHAR(100),
            scheduled_date DATE,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP,
            duration_hours FLOAT,
            technician_id INTEGER REFERENCES users(id),
            technician_name VARCHAR(100),
            team_members TEXT,
            maintenance_items TEXT,
            work_description TEXT,
            parts_replaced TEXT,
            materials_used TEXT,
            status VARCHAR(50) DEFAULT 'completed',
            result VARCHAR(50),
            issues_found TEXT,
            recommendations TEXT,
            labor_cost FLOAT,
            parts_cost FLOAT,
            total_cost FLOAT,
            currency VARCHAR(10) DEFAULT 'CNY',
            notes TEXT,
            attachments TEXT,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_equipment_maintenance_equipment_id ON equipment_maintenance_records (equipment_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_equipment_maintenance_user_id ON equipment_maintenance_records (user_id)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS equipment_usage_records (
            id SERIAL PRIMARY KEY,
            equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
            factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
            production_task_id INTEGER,
            operator_id INTEGER REFERENCES users(id),
            usage_date DATE NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_hours FLOAT,
            work_type VARCHAR(100),
            work_description TEXT,
            output_quantity FLOAT,
            output_unit VARCHAR(50),
            power_consumption FLOAT,
            efficiency FLOAT,
            quality_rating FLOAT,
            issues_occurred BOOLEAN DEFAULT FALSE,
            issue_description TEXT,
            downtime_hours FLOAT,
            notes TEXT,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_equipment_usage_equipment_id ON equipment_usage_records (equipment_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_equipment_usage_user_id ON equipment_usage_records (user_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS equipment_usage_records")
    op.execute("DROP TABLE IF EXISTS equipment_maintenance_records")

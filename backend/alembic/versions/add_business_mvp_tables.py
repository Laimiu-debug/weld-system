"""Create production plans, quality standards, performance and report template tables.

Revision ID: add_business_mvp_tables
Revises: add_quality_location_fields
Create Date: 2026-08-21
"""
from alembic import op

revision = "add_business_mvp_tables"
down_revision = "add_quality_location_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS production_plans (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
            company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
            factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
            plan_number VARCHAR(100) NOT NULL,
            plan_name VARCHAR(255) NOT NULL,
            plan_type VARCHAR(100),
            priority VARCHAR(50) DEFAULT 'normal',
            plan_start_date DATE NOT NULL,
            plan_end_date DATE NOT NULL,
            status VARCHAR(50) DEFAULT 'draft',
            progress_percentage FLOAT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            planned_quantity FLOAT,
            unit VARCHAR(50),
            assigned_team VARCHAR(255),
            quality_standards TEXT,
            description TEXT,
            objectives TEXT,
            tasks TEXT,
            created_by INTEGER NOT NULL REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_production_plans_user_id ON production_plans (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_production_plans_company_id ON production_plans (company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_production_plans_plan_number ON production_plans (plan_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_production_plans_workspace_type ON production_plans (workspace_type)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS quality_standards (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
            company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
            factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
            standard_code VARCHAR(100) NOT NULL,
            standard_name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            version VARCHAR(50),
            level VARCHAR(50),
            status VARCHAR(50) DEFAULT 'active',
            description TEXT,
            effective_date DATE,
            expiry_date DATE,
            test_methods TEXT,
            acceptance_criteria TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_by INTEGER NOT NULL REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_quality_standards_user_id ON quality_standards (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_quality_standards_company_id ON quality_standards (company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_quality_standards_code ON quality_standards (standard_code)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS employee_performances (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
            company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
            factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
            employee_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            employee_name VARCHAR(100) NOT NULL,
            department VARCHAR(100),
            position VARCHAR(100),
            review_period VARCHAR(100) NOT NULL,
            period_start DATE,
            period_end DATE,
            overall_score FLOAT DEFAULT 0,
            quality_score FLOAT,
            efficiency_score FLOAT,
            safety_score FLOAT,
            teamwork_score FLOAT,
            status VARCHAR(50) DEFAULT 'draft',
            goals TEXT,
            achievements TEXT,
            areas_for_improvement TEXT,
            reviewer_comment TEXT,
            reviewed_by INTEGER REFERENCES users(id),
            reviewed_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            created_by INTEGER NOT NULL REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_employee_performances_user_id ON employee_performances (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_employee_performances_company_id ON employee_performances (company_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_employee_performances_employee_user_id ON employee_performances (employee_user_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS report_templates (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            workspace_type VARCHAR(20) NOT NULL DEFAULT 'personal',
            company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
            factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            data_sources TEXT,
            metrics TEXT,
            filters TEXT,
            chart_type VARCHAR(50) DEFAULT 'table',
            time_range TEXT,
            is_public BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_by INTEGER NOT NULL REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_report_templates_user_id ON report_templates (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_report_templates_company_id ON report_templates (company_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS report_templates")
    op.execute("DROP TABLE IF EXISTS employee_performances")
    op.execute("DROP TABLE IF EXISTS quality_standards")
    op.execute("DROP TABLE IF EXISTS production_plans")

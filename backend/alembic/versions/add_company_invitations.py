"""Add company employee invitation table.

Revision ID: add_company_invitations
Revises: add_employee_approve_index
Create Date: 2026-08-19
"""
from alembic import op

revision = "add_company_invitations"
down_revision = "add_employee_approve_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS company_invitations (
            id SERIAL PRIMARY KEY,
            company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            email VARCHAR(255) NOT NULL,
            token VARCHAR(128) NOT NULL UNIQUE,
            invitation_code VARCHAR(32) NOT NULL UNIQUE,
            role VARCHAR(50) DEFAULT 'employee',
            company_role_id INTEGER REFERENCES company_roles(id) ON DELETE SET NULL,
            factory_id INTEGER REFERENCES factories(id) ON DELETE SET NULL,
            department VARCHAR(100),
            permissions JSONB,
            message TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            expires_at TIMESTAMP NOT NULL,
            accepted_at TIMESTAMP,
            accepted_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            invited_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_company_invitations_company_status "
        "ON company_invitations (company_id, status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_company_invitations_email_status "
        "ON company_invitations (email, status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_company_invitations_token "
        "ON company_invitations (token)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_company_invitations_token")
    op.execute("DROP INDEX IF EXISTS ix_company_invitations_email_status")
    op.execute("DROP INDEX IF EXISTS ix_company_invitations_company_status")
    op.execute("DROP TABLE IF EXISTS company_invitations")

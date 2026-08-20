"""Add users.preferences JSON text column.

Revision ID: add_user_preferences
Revises: add_company_invitations
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa

revision = "add_user_preferences"
down_revision = "add_company_invitations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences TEXT"
    )


def downgrade() -> None:
    op.drop_column("users", "preferences")

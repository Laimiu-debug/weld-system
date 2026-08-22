"""add user_feedbacks table

Revision ID: add_user_feedbacks
Revises: fix_production_plan_cols
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa


revision = "add_user_feedbacks"
down_revision = "fix_production_plan_cols"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_feedbacks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            contact VARCHAR(200),
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            read_at TIMESTAMP WITHOUT TIME ZONE,
            admin_note TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_feedbacks_user_id ON user_feedbacks (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_feedbacks_is_read ON user_feedbacks (is_read)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_feedbacks_created_at ON user_feedbacks (created_at)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_feedbacks_read_created ON user_feedbacks (is_read, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_feedbacks")

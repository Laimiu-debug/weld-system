"""Add welder_certified_projects table.

Revision ID: add_welder_certified_projects
Revises: add_user_preferences
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa

revision = "add_welder_certified_projects"
down_revision = "add_user_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Some installations created this table through the legacy bootstrap path
    # before Alembic became authoritative. Keep the migration compatible with
    # those databases while still creating the full table for a clean install.
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("welder_certified_projects"):
        op.create_table(
            "welder_certified_projects",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("certification_id", sa.Integer(), sa.ForeignKey("welder_certifications.id", ondelete="CASCADE"), nullable=False),
            sa.Column("welder_id", sa.Integer(), sa.ForeignKey("welders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("project_code", sa.String(100), nullable=True),
            sa.Column("project_name", sa.String(200), nullable=False),
            sa.Column("issue_date", sa.Date(), nullable=True),
            sa.Column("expiry_date", sa.Date(), nullable=True),
            sa.Column("renewal_date", sa.Date(), nullable=True),
            sa.Column("renewal_count", sa.Integer(), server_default="0"),
            sa.Column("next_renewal_date", sa.Date(), nullable=True),
            sa.Column("renewal_result", sa.String(50), nullable=True),
            sa.Column("renewal_notes", sa.Text(), nullable=True),
            sa.Column("status", sa.String(50), server_default="valid"),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_welder_certified_projects_certification_id "
        "ON welder_certified_projects (certification_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_welder_certified_projects_welder_id "
        "ON welder_certified_projects (welder_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS welder_certified_projects")

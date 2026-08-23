"""Add structured page and field progress to smart-import jobs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_smart_import_progress_detail"
down_revision = "add_approval_version_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "extraction_jobs",
        sa.Column(
            "progress_detail",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("extraction_jobs", "progress_detail", server_default=None)


def downgrade() -> None:
    op.drop_column("extraction_jobs", "progress_detail")

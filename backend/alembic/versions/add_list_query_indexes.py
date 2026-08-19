"""Add list/filter indexes for notifications, quality, and approvals.

Revision ID: add_list_query_indexes
Revises: add_auto_generated_flag
Create Date: 2026-08-19
"""
from alembic import op

revision = "add_list_query_indexes"
down_revision = "add_auto_generated_flag"
branch_labels = None
depends_on = None


INDEXES = [
    ("ix_unrs_user_unread", "user_notification_read_status", "user_id, is_read, is_deleted"),
    ("ix_unrs_user_announcement", "user_notification_read_status", "user_id, announcement_id"),
    ("ix_announcements_published_at", "system_announcements", "is_published, publish_at"),
    ("ix_approval_status_created", "approval_instances", "status, created_at"),
    ("ix_quality_owner_created", "quality_inspections", "owner_id, created_at"),
    ("ix_quality_company_result", "quality_inspections", "company_id, inspection_result"),
]


def upgrade() -> None:
    for name, table, columns in INDEXES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})")


def downgrade() -> None:
    for name, table, _columns in reversed(INDEXES):
        op.drop_index(name, table_name=table)

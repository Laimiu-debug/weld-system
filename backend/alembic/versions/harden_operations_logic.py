"""Harden production execution idempotency and active alert uniqueness.

Revision ID: harden_operations_logic
Revises: add_operations_security_p8
"""
from alembic import op
import sqlalchemy as sa


revision = "harden_operations_logic"
down_revision = "add_operations_security_p8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The P7 migration used ``unique=True`` and PostgreSQL generated the
    # historical name below. Some bootstrap-created databases used the ORM
    # constraint name instead, so accept both shapes.
    op.execute(
        sa.text(
            "ALTER TABLE production_execution_traces "
            "DROP CONSTRAINT IF EXISTS production_execution_traces_idempotency_key_key"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE production_execution_traces "
            "DROP CONSTRAINT IF EXISTS uq_production_execution_idempotency"
        )
    )
    op.create_unique_constraint(
        "uq_production_execution_task_idempotency",
        "production_execution_traces",
        ["production_task_id", "idempotency_key"],
    )
    op.drop_constraint(
        "uq_operational_alert_fingerprint_status",
        "operational_alerts",
        type_="unique",
    )
    op.create_index(
        "uq_operational_alert_active_fingerprint",
        "operational_alerts",
        ["fingerprint"],
        unique=True,
        postgresql_where=sa.text("status IN ('open', 'acknowledged')"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_operational_alert_active_fingerprint",
        table_name="operational_alerts",
    )
    op.create_unique_constraint(
        "uq_operational_alert_fingerprint_status",
        "operational_alerts",
        ["fingerprint", "status"],
    )
    op.execute(
        sa.text(
            "ALTER TABLE production_execution_traces "
            "DROP CONSTRAINT IF EXISTS uq_production_execution_task_idempotency"
        )
    )
    op.create_unique_constraint(
        "uq_production_execution_idempotency",
        "production_execution_traces",
        ["idempotency_key"],
    )

"""add P7 sequence production release and execution trace

Revision ID: add_production_release_p7
Revises: add_consumable_issue_lists
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_production_release_p7"
down_revision = "add_consumable_issue_lists"
branch_labels = None
depends_on = None


def ws():
    return [
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("workspace_type", sa.String(20), nullable=False),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "factory_id",
            sa.Integer(),
            sa.ForeignKey("factories.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "access_level", sa.String(20), nullable=False, server_default="private"
        ),
        sa.Column(
            "created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade():
    op.create_table(
        "production_release_batches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "product_revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "sequence_revision_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "consumable_issue_list_id",
            sa.String(36),
            sa.ForeignKey("consumable_issue_lists.id", ondelete="RESTRICT"),
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="released"),
        sa.Column("idempotency_key", sa.String(64), nullable=False, unique=True),
        sa.Column("sequence_frozen_hash", sa.String(64), nullable=False),
        sa.Column("source_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column(
            "released_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "released_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        *ws(),
        sa.CheckConstraint(
            "status IN ('released','superseded','cancelled')",
            name="ck_production_release_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_release_workspace",
        ),
        sa.UniqueConstraint(
            "sequence_revision_id", name="uq_production_release_sequence"
        ),
    )
    op.create_index(
        "ix_production_release_product",
        "production_release_batches",
        ["product_revision_id", "status"],
    )

    for name, column, target in [
        ("source_product_revision_id", sa.String(36), "product_revisions.id"),
        ("source_sequence_revision_id", sa.String(36), "weld_sequence_revisions.id"),
        ("source_sequence_step_id", sa.String(36), "weld_sequence_steps.id"),
        ("source_weld_joint_id", sa.String(36), "weld_joints.id"),
        ("source_match_freeze_id", sa.String(36), "wps_match_freezes.id"),
        ("production_release_id", sa.String(36), "production_release_batches.id"),
        ("consumable_issue_list_id", sa.String(36), "consumable_issue_lists.id"),
    ]:
        op.add_column("production_tasks", sa.Column(name, column))
        op.create_foreign_key(
            f"fk_production_task_{name}",
            "production_tasks",
            target.split(".")[0],
            [name],
            [target.split(".")[1]],
            ondelete="RESTRICT",
        )
    op.add_column(
        "production_tasks", sa.Column("source_sequence_frozen_hash", sa.String(64))
    )
    op.add_column(
        "production_tasks", sa.Column("source_step_snapshot", postgresql.JSONB())
    )
    op.create_unique_constraint(
        "uq_production_task_sequence_step",
        "production_tasks",
        ["source_sequence_revision_id", "source_sequence_step_id"],
    )
    op.create_index(
        "ix_production_task_release",
        "production_tasks",
        ["production_release_id", "source_sequence_step_id"],
    )

    op.create_table(
        "production_resource_authorizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "production_task_id",
            sa.Integer(),
            sa.ForeignKey("production_tasks.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "welder_id",
            sa.Integer(),
            sa.ForeignKey("welders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "equipment_id",
            sa.Integer(),
            sa.ForeignKey("equipment.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "wps_id",
            sa.Integer(),
            sa.ForeignKey("wps.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qualification_status", sa.String(20), nullable=False),
        sa.Column("qualification_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("override_reason", sa.Text()),
        sa.Column(
            "authorized_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("authorized_at", sa.DateTime()),
        *ws(),
        sa.CheckConstraint(
            "qualification_status IN ('qualified','pending_override','authorized','rejected')",
            name="ck_production_resource_qualification",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_resource_workspace",
        ),
    )
    op.create_index(
        "ix_production_resource_task",
        "production_resource_authorizations",
        ["production_task_id", "qualification_status"],
    )

    op.create_table(
        "production_quality_nodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "production_release_id",
            sa.String(36),
            sa.ForeignKey("production_release_batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "production_task_id",
            sa.Integer(),
            sa.ForeignKey("production_tasks.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "sequence_step_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_steps.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "quality_inspection_id",
            sa.Integer(),
            sa.ForeignKey("quality_inspections.id", ondelete="RESTRICT"),
        ),
        sa.Column("node_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("frozen_snapshot", postgresql.JSONB(), nullable=False),
        *ws(),
        sa.CheckConstraint(
            "node_type IN ('nde','pwht','inspection','closure')",
            name="ck_production_quality_node_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending','in_progress','passed','failed','waived')",
            name="ck_production_quality_node_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_quality_node_workspace",
        ),
        sa.UniqueConstraint(
            "production_release_id",
            "sequence_step_id",
            name="uq_production_quality_release_step",
        ),
    )

    op.create_table(
        "production_execution_traces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "production_release_id",
            sa.String(36),
            sa.ForeignKey("production_release_batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "production_task_id",
            sa.Integer(),
            sa.ForeignKey("production_tasks.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "production_record_id",
            sa.Integer(),
            sa.ForeignKey("production_records.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "sequence_revision_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "sequence_step_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_steps.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "weld_joint_id",
            sa.String(36),
            sa.ForeignKey("weld_joints.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "welder_id", sa.Integer(), sa.ForeignKey("welders.id", ondelete="RESTRICT")
        ),
        sa.Column(
            "equipment_id",
            sa.Integer(),
            sa.ForeignKey("equipment.id", ondelete="RESTRICT"),
        ),
        sa.Column("wps_id", sa.Integer(), sa.ForeignKey("wps.id", ondelete="RESTRICT")),
        sa.Column("status", sa.String(20), nullable=False, server_default="recorded"),
        sa.Column("design_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("actual_parameters", postgresql.JSONB(), nullable=False),
        sa.Column("consumable_usage_event_ids", postgresql.JSONB(), nullable=False),
        sa.Column("repair_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("quality_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "recorded_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "recorded_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        *ws(),
        sa.CheckConstraint(
            "status IN ('recorded','completed','voided')",
            name="ck_production_execution_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_execution_workspace",
        ),
    )
    op.create_index(
        "ix_production_execution_trace",
        "production_execution_traces",
        ["production_release_id", "sequence_step_id", "recorded_at"],
    )

    op.create_table(
        "production_sequence_change_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "production_release_id",
            sa.String(36),
            sa.ForeignKey("production_release_batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_sequence_revision_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "proposed_sequence_revision_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT"),
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("impact_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "approval_instance_id",
            sa.Integer(),
            sa.ForeignKey("approval_instances.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "requested_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "decided_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("decided_at", sa.DateTime()),
        *ws(),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected','applied')",
            name="ck_production_sequence_change_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_sequence_change_workspace",
        ),
    )
    op.create_index(
        "ix_production_sequence_change_release",
        "production_sequence_change_requests",
        ["production_release_id", "status"],
    )


def downgrade():
    op.drop_table("production_sequence_change_requests")
    op.drop_table("production_execution_traces")
    op.drop_table("production_quality_nodes")
    op.drop_table("production_resource_authorizations")
    op.drop_index("ix_production_task_release", table_name="production_tasks")
    op.drop_constraint(
        "uq_production_task_sequence_step", "production_tasks", type_="unique"
    )
    for name in [
        "source_step_snapshot",
        "source_sequence_frozen_hash",
        "consumable_issue_list_id",
        "production_release_id",
        "source_match_freeze_id",
        "source_weld_joint_id",
        "source_sequence_step_id",
        "source_sequence_revision_id",
        "source_product_revision_id",
    ]:
        op.drop_column("production_tasks", name)
    op.drop_table("production_release_batches")

"""add P5 weld sequence planning

Revision ID: add_weld_sequence_planning
Revises: add_wps_matching_core
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_weld_sequence_planning"
down_revision = "add_wps_matching_core"
branch_labels = None
depends_on = None


def workspace_columns():
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
        "weld_sequence_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "product_revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "parent_revision_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_revisions.id", ondelete="SET NULL"),
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("source_data_version", sa.Integer(), nullable=False),
        sa.Column(
            "template_code",
            sa.String(80),
            nullable=False,
            server_default="PRESSURE_VESSEL_V1",
        ),
        sa.Column(
            "template_version", sa.String(30), nullable=False, server_default="1.0.0"
        ),
        sa.Column(
            "strategy_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "source_match_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("source_match_hash", sa.String(64), nullable=False),
        sa.Column(
            "candidate_source",
            sa.String(20),
            nullable=False,
            server_default="deterministic",
        ),
        sa.Column("candidate_explanation", sa.Text()),
        sa.Column(
            "validation_result",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("validation_hash", sa.String(64)),
        sa.Column("change_summary", sa.Text()),
        sa.Column(
            "approval_instance_id",
            sa.Integer(),
            sa.ForeignKey("approval_instances.id", ondelete="SET NULL"),
        ),
        sa.Column("approval_snapshot_hash", sa.String(64)),
        sa.Column("frozen_snapshot", postgresql.JSONB()),
        sa.Column("frozen_hash", sa.String(64)),
        sa.Column("submitted_at", sa.DateTime()),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        *workspace_columns(),
        sa.CheckConstraint(
            "status IN ('draft','pending','approved','rejected','returned','superseded')",
            name="ck_weld_sequence_revision_status",
        ),
        sa.CheckConstraint(
            "candidate_source IN ('deterministic','ai_assisted','manual')",
            name="ck_weld_sequence_candidate_source",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_sequence_revision_workspace",
        ),
        sa.UniqueConstraint(
            "product_revision_id", "version_number", name="uq_weld_sequence_version"
        ),
    )
    op.create_index(
        "ix_weld_sequence_revision_product",
        "weld_sequence_revisions",
        ["product_revision_id", "version_number"],
    )
    op.create_table(
        "weld_sequence_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "sequence_revision_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_code", sa.String(100), nullable=False),
        sa.Column("step_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(80), nullable=False),
        sa.Column(
            "weld_joint_id",
            sa.String(36),
            sa.ForeignKey("weld_joints.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "match_freeze_id",
            sa.String(36),
            sa.ForeignKey("wps_match_freezes.id", ondelete="RESTRICT"),
        ),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "constraint_tags",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "process_parameters",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "inspection_node",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "source_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        *workspace_columns(),
        sa.CheckConstraint(
            "step_type IN ('assembly','weld','nde','pwht','inspection','closure')",
            name="ck_weld_sequence_step_type",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_sequence_step_workspace",
        ),
        sa.UniqueConstraint(
            "sequence_revision_id", "step_code", name="uq_weld_sequence_step_code"
        ),
        sa.UniqueConstraint(
            "sequence_revision_id", "order_index", name="uq_weld_sequence_step_order"
        ),
    )
    op.create_index(
        "ix_weld_sequence_step_revision",
        "weld_sequence_steps",
        ["sequence_revision_id", "order_index"],
    )
    op.create_table(
        "step_dependencies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "sequence_revision_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "predecessor_step_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_steps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "successor_step_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_steps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dependency_type", sa.String(30), nullable=False),
        sa.Column(
            "is_mandatory", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("explanation", sa.Text(), nullable=False),
        *workspace_columns(),
        sa.CheckConstraint(
            "dependency_type IN ('assembly','accessibility','nde','pwht','closed_space','manual')",
            name="ck_step_dependency_type",
        ),
        sa.CheckConstraint(
            "predecessor_step_id <> successor_step_id",
            name="ck_step_dependency_not_self",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_step_dependency_workspace",
        ),
        sa.UniqueConstraint(
            "sequence_revision_id",
            "predecessor_step_id",
            "successor_step_id",
            name="uq_step_dependency_edge",
        ),
    )
    op.create_index(
        "ix_step_dependency_revision", "step_dependencies", ["sequence_revision_id"]
    )
    op.execute(
        """
        INSERT INTO approval_workflow_definitions
            (name, code, description, document_type, company_id, factory_id, steps,
             is_active, is_default, created_at, updated_at)
        SELECT '焊序版本默认审批', 'SYSTEM_WELD_SEQUENCE_DEFAULT',
               '系统默认焊序工程师审批流程', 'weld_sequence_version', NULL, NULL,
               '[]'::jsonb,
               true, true, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM approval_workflow_definitions
            WHERE code = 'SYSTEM_WELD_SEQUENCE_DEFAULT'
        )
    """
    )


def downgrade():
    op.execute(
        "DELETE FROM approval_workflow_definitions WHERE code = 'SYSTEM_WELD_SEQUENCE_DEFAULT'"
    )
    op.drop_index("ix_step_dependency_revision", table_name="step_dependencies")
    op.drop_table("step_dependencies")
    op.drop_index("ix_weld_sequence_step_revision", table_name="weld_sequence_steps")
    op.drop_table("weld_sequence_steps")
    op.drop_index(
        "ix_weld_sequence_revision_product", table_name="weld_sequence_revisions"
    )
    op.drop_table("weld_sequence_revisions")

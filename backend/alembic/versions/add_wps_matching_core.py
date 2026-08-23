"""Add P4 deterministic WPS/PQR matching, criteria, gaps, and freezes."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_wps_matching_core"
down_revision = "add_engineering_drawing_core"
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


def upgrade() -> None:
    op.add_column("weld_requirements", sa.Column("welding_process", sa.String(100)))
    op.add_column("weld_requirements", sa.Column("material_group", sa.String(100)))
    op.add_column("weld_requirements", sa.Column("diameter_applicable", sa.Boolean()))
    op.add_column("weld_requirements", sa.Column("diameter_mm", sa.Float()))
    op.add_column(
        "weld_requirements", sa.Column("filler_material_spec", sa.String(100))
    )
    op.add_column(
        "weld_requirements", sa.Column("filler_material_classification", sa.String(100))
    )

    op.create_table(
        "wps_match_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trigger_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("source_data_version", sa.Integer(), nullable=False),
        sa.Column("rule_pack_code", sa.String(80), nullable=False),
        sa.Column("rule_pack_version", sa.String(40), nullable=False),
        sa.Column("capability_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("capability_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("policy_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("target_joint_ids", postgresql.JSONB(), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("gap_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        *ws(),
        sa.CheckConstraint(
            "trigger_type IN ('manual','field_change','drawing_change')",
            name="ck_wps_match_run_trigger",
        ),
        sa.CheckConstraint(
            "status IN ('processing','completed','approved','superseded','failed')",
            name="ck_wps_match_run_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_match_run_workspace",
        ),
    )
    op.create_index(
        "ix_wps_match_run_revision", "wps_match_runs", ["revision_id", "created_at"]
    )

    op.create_table(
        "wps_match_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("wps_match_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "weld_joint_id",
            sa.String(36),
            sa.ForeignKey("weld_joints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "support_link_id",
            sa.String(36),
            sa.ForeignKey("wps_pqr_support_links.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "wps_id",
            sa.Integer(),
            sa.ForeignKey("wps.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "pqr_id",
            sa.Integer(),
            sa.ForeignKey("pqr.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(30), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "is_recommended", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "confirmation_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("confirmation_note", sa.Text()),
        sa.Column(
            "confirmed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("confirmed_at", sa.DateTime()),
        sa.Column("requirement_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("wps_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("pqr_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("qualification_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("rule_snapshot", postgresql.JSONB(), nullable=False),
        *ws(),
        sa.CheckConstraint(
            "decision IN ('eligible','not_eligible','needs_confirmation')",
            name="ck_wps_match_candidate_decision",
        ),
        sa.CheckConstraint(
            "confirmation_status IN ('pending','confirmed','rejected')",
            name="ck_wps_match_candidate_confirmation",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_match_candidate_workspace",
        ),
        sa.UniqueConstraint(
            "run_id",
            "weld_joint_id",
            "support_link_id",
            name="uq_wps_match_candidate_link",
        ),
    )
    op.create_index(
        "ix_wps_match_candidate_joint_rank",
        "wps_match_candidates",
        ["run_id", "weld_joint_id", "rank"],
    )

    op.create_table(
        "wps_match_criteria",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.String(36),
            sa.ForeignKey("wps_match_candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dimension", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("required_value", postgresql.JSONB(), nullable=False),
        sa.Column("available_value", postgresql.JSONB(), nullable=False),
        sa.Column("basis", postgresql.JSONB(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *ws(),
        sa.CheckConstraint(
            "status IN ('pass','fail','boundary','insufficient')",
            name="ck_wps_match_criterion_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_match_criterion_workspace",
        ),
        sa.UniqueConstraint(
            "candidate_id", "dimension", name="uq_wps_match_criterion_dimension"
        ),
    )
    op.create_index(
        "ix_wps_match_criterion_candidate",
        "wps_match_criteria",
        ["candidate_id", "sort_order"],
    )

    op.create_table(
        "wps_capability_gaps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("wps_match_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "weld_joint_id",
            sa.String(36),
            sa.ForeignKey("weld_joints.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dimension", sa.String(40), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("requirement_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "linked_ppqr_id",
            sa.Integer(),
            sa.ForeignKey("ppqr.id", ondelete="SET NULL"),
        ),
        sa.Column("qualification_plan_reference", sa.String(200)),
        sa.Column("resolved_at", sa.DateTime()),
        *ws(),
        sa.CheckConstraint(
            "severity IN ('blocking','warning')", name="ck_wps_capability_gap_severity"
        ),
        sa.CheckConstraint(
            "status IN ('open','linked','resolved','dismissed')",
            name="ck_wps_capability_gap_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_capability_gap_workspace",
        ),
    )
    op.create_index(
        "ix_wps_capability_gap_run_joint",
        "wps_capability_gaps",
        ["run_id", "weld_joint_id"],
    )

    op.create_table(
        "wps_match_freezes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("wps_match_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            sa.String(36),
            sa.ForeignKey("wps_match_candidates.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "weld_joint_id",
            sa.String(36),
            sa.ForeignKey("weld_joints.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "frozen_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "frozen_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("weld_requirement_hash", sa.String(64), nullable=False),
        sa.Column("wps_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("pqr_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("rule_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("frozen_snapshot", postgresql.JSONB(), nullable=False),
        *ws(),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_match_freeze_workspace",
        ),
        sa.UniqueConstraint(
            "run_id", "weld_joint_id", name="uq_wps_match_freeze_joint"
        ),
    )
    op.create_index(
        "ix_wps_match_freeze_revision",
        "wps_match_freezes",
        ["revision_id", "weld_joint_id"],
    )


def downgrade() -> None:
    for table in (
        "wps_match_freezes",
        "wps_capability_gaps",
        "wps_match_criteria",
        "wps_match_candidates",
        "wps_match_runs",
    ):
        op.drop_table(table)
    for column in (
        "filler_material_classification",
        "filler_material_spec",
        "diameter_mm",
        "diameter_applicable",
        "material_group",
        "welding_process",
    ):
        op.drop_column("weld_requirements", column)

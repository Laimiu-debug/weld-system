"""add P6 consumable geometry and relational operation foundation

Revision ID: add_consumable_geometry_core
Revises: add_weld_sequence_planning
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_consumable_geometry_core"
down_revision = "add_weld_sequence_planning"
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
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
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
        "consumable_geometry_inputs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "product_revision_id",
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
            "sequence_revision_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "sequence_step_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_steps.id", ondelete="RESTRICT"),
        ),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("formula_version", sa.String(40), nullable=False),
        sa.Column("groove_type", sa.String(20), nullable=False),
        sa.Column("thickness_mm", sa.Float(), nullable=False, server_default="0"),
        sa.Column("included_angle_deg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("root_gap_mm", sa.Float(), nullable=False, server_default="0"),
        sa.Column("root_face_mm", sa.Float(), nullable=False, server_default="0"),
        sa.Column("radius_mm", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "upper_bevel_height_mm", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column(
            "lower_bevel_height_mm", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column("leg_size_mm", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reinforcement_mm", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "face_extra_each_side_mm", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column("fill_factor", sa.Float(), nullable=False, server_default="1"),
        sa.Column(
            "back_gouge_depth_mm", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column("back_gouge_opening_width_mm", sa.Float()),
        sa.Column(
            "gouge_strategy", sa.String(30), nullable=False, server_default="explicit"
        ),
        sa.Column(
            "reference_gouge_flare_ratio",
            sa.Float(),
            nullable=False,
            server_default="0.5",
        ),
        sa.Column("length_type", sa.String(30), nullable=False),
        sa.Column("weld_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("straight_length_mm", sa.Float()),
        sa.Column("diameter_mm", sa.Float()),
        sa.Column("diameter_basis", sa.String(20)),
        sa.Column(
            "included_length_angle_deg",
            sa.Float(),
            nullable=False,
            server_default="360",
        ),
        sa.Column("manual_confirmed_length_mm", sa.Float()),
        sa.Column(
            "geometry_input_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "length_input_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "geometry_result_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "length_result_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "warnings",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "confirmed_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("confirmed_at", sa.DateTime()),
        sa.Column("confirmation_note", sa.Text()),
        *workspace_columns(),
        sa.CheckConstraint(
            "status IN ('draft','confirmed','superseded')",
            name="ck_consumable_geometry_status",
        ),
        sa.CheckConstraint(
            "source IN ('manual','drawing')", name="ck_consumable_geometry_source"
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_consumable_geometry_workspace",
        ),
        sa.UniqueConstraint(
            "weld_joint_id",
            "version_number",
            name="uq_consumable_geometry_version",
        ),
    )
    op.create_index(
        "ix_consumable_geometry_product_joint",
        "consumable_geometry_inputs",
        ["product_revision_id", "weld_joint_id"],
    )
    op.create_table(
        "weld_consumable_operations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "geometry_input_id",
            sa.String(36),
            sa.ForeignKey("consumable_geometry_inputs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "product_revision_id",
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
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("operation_order", sa.Integer(), nullable=False),
        sa.Column("operation_role", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("welding_method", sa.String(80), nullable=False),
        sa.Column(
            "material_id",
            sa.Integer(),
            sa.ForeignKey("welding_materials.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "flux_material_id",
            sa.Integer(),
            sa.ForeignKey("welding_materials.id", ondelete="RESTRICT"),
        ),
        sa.Column("area_source", sa.String(30), nullable=False),
        sa.Column("area_mm2", sa.Float(), nullable=False),
        sa.Column("length_mm", sa.Float(), nullable=False),
        sa.Column("density_g_cm3", sa.Float(), nullable=False),
        sa.Column("deposition_efficiency", sa.Float(), nullable=False),
        sa.Column("deposition_rate_kg_h", sa.Float()),
        sa.Column("arc_time_h", sa.Float()),
        sa.Column("arc_time_ratio", sa.Float()),
        sa.Column("flux_wire_ratio", sa.Float()),
        sa.Column("gas_flow_l_min", sa.Float()),
        sa.Column("pass_count_description", sa.Integer()),
        sa.Column(
            "input_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "result_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("formula_version", sa.String(40), nullable=False),
        *workspace_columns(),
        sa.CheckConstraint(
            "operation_role IN ('face_fill','back_gouge_fill','tack','custom')",
            name="ck_weld_consumable_operation_role",
        ),
        sa.CheckConstraint(
            "status IN ('draft','calculated','superseded')",
            name="ck_weld_consumable_operation_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_consumable_operation_workspace",
        ),
        sa.UniqueConstraint(
            "sequence_step_id",
            "version_number",
            "operation_order",
            name="uq_weld_consumable_operation_order",
        ),
    )
    op.create_index(
        "ix_weld_consumable_operation_trace",
        "weld_consumable_operations",
        ["product_revision_id", "weld_joint_id", "sequence_step_id"],
    )


def downgrade():
    op.drop_index(
        "ix_weld_consumable_operation_trace",
        table_name="weld_consumable_operations",
    )
    op.drop_table("weld_consumable_operations")
    op.drop_index(
        "ix_consumable_geometry_product_joint",
        table_name="consumable_geometry_inputs",
    )
    op.drop_table("consumable_geometry_inputs")

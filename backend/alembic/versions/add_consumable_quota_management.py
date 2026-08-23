"""add P6 multi-operation parameters and versioned quota runs

Revision ID: add_consumable_quota_management
Revises: add_consumable_geometry_core
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_consumable_quota_management"
down_revision = "add_consumable_geometry_core"
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
    op.add_column("welding_materials", sa.Column("density_g_cm3", sa.Float()))
    op.add_column(
        "welding_materials", sa.Column("default_deposition_efficiency", sa.Float())
    )
    op.add_column(
        "welding_materials", sa.Column("default_deposition_rate_kg_h", sa.Float())
    )
    op.add_column("welding_materials", sa.Column("consumable_type", sa.String(50)))
    op.add_column(
        "welding_materials",
        sa.Column(
            "applicable_welding_methods",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "welding_materials",
        sa.Column(
            "parameter_version", sa.Integer(), nullable=False, server_default="1"
        ),
    )
    op.add_column(
        "welding_materials",
        sa.Column(
            "parameter_approval_status",
            sa.String(20),
            nullable=False,
            server_default="draft",
        ),
    )
    op.add_column(
        "welding_materials", sa.Column("parameter_effective_from", sa.DateTime())
    )
    op.add_column(
        "welding_materials", sa.Column("parameter_effective_to", sa.DateTime())
    )

    for name, default in (
        ("electrode_stub_loss_ratio", "0"),
        ("spatter_loss_ratio", "0"),
        ("flux_loss_ratio", "0"),
        ("enterprise_correction_factor", "1"),
    ):
        op.add_column(
            "weld_consumable_operations",
            sa.Column(name, sa.Float(), nullable=False, server_default=default),
        )
    op.add_column(
        "weld_consumable_operations", sa.Column("package_size_kg", sa.Float())
    )
    op.add_column(
        "weld_consumable_operations",
        sa.Column(
            "area_allocation_ratio", sa.Float(), nullable=False, server_default="1"
        ),
    )

    op.create_table(
        "consumable_method_parameters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("parameter_code", sa.String(80), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("welding_method", sa.String(80), nullable=False),
        sa.Column("consumable_type", sa.String(50), nullable=False),
        sa.Column(
            "compatible_material_types",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("default_deposition_efficiency", sa.Float(), nullable=False),
        sa.Column("default_deposition_rate_kg_h", sa.Float()),
        sa.Column("default_flux_wire_ratio", sa.Float()),
        sa.Column("default_gas_flow_l_min", sa.Float()),
        sa.Column("default_arc_time_ratio", sa.Float()),
        sa.Column(
            "approval_status", sa.String(20), nullable=False, server_default="draft"
        ),
        sa.Column("effective_from", sa.DateTime()),
        sa.Column("effective_to", sa.DateTime()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "supersedes_id",
            sa.String(36),
            sa.ForeignKey("consumable_method_parameters.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column(
            "parameter_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        *ws(),
        sa.CheckConstraint(
            "approval_status IN ('draft','pending','approved','rejected','superseded')",
            name="ck_consumable_method_parameter_approval",
        ),
        sa.UniqueConstraint(
            "workspace_type",
            "company_id",
            "factory_id",
            "parameter_code",
            "version_number",
            name="uq_consumable_method_parameter_version",
        ),
    )
    op.create_index(
        "ix_consumable_method_parameter_scope",
        "consumable_method_parameters",
        ["workspace_type", "company_id", "factory_id", "welding_method"],
    )

    op.create_table(
        "consumable_groove_presets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("preset_code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("groove_type", sa.String(20), nullable=False),
        sa.Column(
            "parameter_values",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "is_system_typical", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "approval_status", sa.String(20), nullable=False, server_default="draft"
        ),
        sa.Column("effective_from", sa.DateTime()),
        sa.Column("effective_to", sa.DateTime()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "supersedes_id",
            sa.String(36),
            sa.ForeignKey("consumable_groove_presets.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("approved_at", sa.DateTime()),
        *ws(),
        sa.CheckConstraint(
            "approval_status IN ('draft','pending','approved','rejected','superseded')",
            name="ck_consumable_groove_preset_approval",
        ),
        sa.UniqueConstraint(
            "workspace_type",
            "company_id",
            "factory_id",
            "preset_code",
            "version_number",
            name="uq_consumable_groove_preset_version",
        ),
    )

    op.create_table(
        "consumable_rule_sets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("formula_version", sa.String(40), nullable=False),
        sa.Column(
            "electrode_stub_loss_ratio", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column("spatter_loss_ratio", sa.Float(), nullable=False, server_default="0"),
        sa.Column("flux_loss_ratio", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "enterprise_correction_factor",
            sa.Float(),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "packaging_rules",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("effective_from", sa.DateTime()),
        sa.Column("effective_to", sa.DateTime()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "supersedes_id",
            sa.String(36),
            sa.ForeignKey("consumable_rule_sets.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column(
            "frozen_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        *ws(),
        sa.CheckConstraint(
            "status IN ('draft','pending','approved','rejected','superseded')",
            name="ck_consumable_rule_set_status",
        ),
        sa.UniqueConstraint(
            "workspace_type",
            "company_id",
            "factory_id",
            "rule_code",
            "version_number",
            name="uq_consumable_rule_set_version",
        ),
    )
    op.create_index(
        "ix_consumable_rule_set_scope",
        "consumable_rule_sets",
        ["workspace_type", "company_id", "factory_id", "status"],
    )

    op.create_table(
        "consumable_quota_runs",
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
            "rule_set_id",
            sa.String(36),
            sa.ForeignKey("consumable_rule_sets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "parent_run_id",
            sa.String(36),
            sa.ForeignKey("consumable_quota_runs.id", ondelete="RESTRICT"),
        ),
        sa.Column("run_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="calculated"),
        sa.Column("input_version_hash", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False, unique=True),
        sa.Column("formula_version", sa.String(40), nullable=False),
        sa.Column(
            "frozen_input_snapshot",
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
        sa.Column(
            "diff_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "stale_reasons",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "calculated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("issued_at", sa.DateTime()),
        *ws(),
        sa.CheckConstraint(
            "status IN ('calculated','pending','approved','issued','stale','superseded')",
            name="ck_consumable_quota_run_status",
        ),
        sa.UniqueConstraint(
            "product_revision_id",
            "sequence_revision_id",
            "run_version",
            name="uq_consumable_quota_run_version",
        ),
    )
    op.create_index(
        "ix_consumable_quota_run_trace",
        "consumable_quota_runs",
        ["product_revision_id", "sequence_revision_id", "status"],
    )

    op.create_table(
        "consumable_quota_operations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("consumable_quota_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_operation_id",
            sa.String(36),
            sa.ForeignKey("weld_consumable_operations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "weld_joint_id",
            sa.String(36),
            sa.ForeignKey("weld_joints.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "sequence_step_id",
            sa.String(36),
            sa.ForeignKey("weld_sequence_steps.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("operation_order", sa.Integer(), nullable=False),
        sa.Column("operation_role", sa.String(30), nullable=False),
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
        sa.Column("theoretical_deposit_kg", sa.Float(), nullable=False),
        sa.Column("process_primary_kg", sa.Float(), nullable=False),
        sa.Column("enterprise_primary_kg", sa.Float(), nullable=False),
        sa.Column("package_rounded_primary_kg", sa.Float(), nullable=False),
        sa.Column("suggested_primary_issue_kg", sa.Float(), nullable=False),
        sa.Column("flux_kg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("gas_l", sa.Float(), nullable=False, server_default="0"),
        sa.Column("arc_time_h", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_time_h", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "input_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "method_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "material_snapshot",
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
        sa.Column(
            "result_sources",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        *ws(),
        sa.UniqueConstraint(
            "run_id", "source_operation_id", name="uq_consumable_quota_operation_source"
        ),
    )
    op.create_index(
        "ix_consumable_quota_operation_trace",
        "consumable_quota_operations",
        ["run_id", "weld_joint_id", "sequence_step_id"],
    )

    op.create_table(
        "consumable_quota_summaries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("consumable_quota_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "summary_type", sa.String(30), nullable=False, server_default="run_total"
        ),
        sa.Column(
            "material_id",
            sa.Integer(),
            sa.ForeignKey("welding_materials.id", ondelete="RESTRICT"),
        ),
        sa.Column("material_type", sa.String(50), nullable=False),
        sa.Column("specification", sa.String(255)),
        sa.Column("theoretical_kg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("process_kg", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "enterprise_quota_kg", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column("package_rounded_kg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("suggested_issue_kg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("gas_l", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_time_h", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "trace_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        *ws(),
        sa.UniqueConstraint(
            "run_id",
            "summary_type",
            "material_id",
            name="uq_consumable_quota_summary_item",
        ),
    )

    op.create_table(
        "consumable_quota_override_audits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("consumable_quota_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "quota_operation_id",
            sa.String(36),
            sa.ForeignKey("consumable_quota_operations.id", ondelete="RESTRICT"),
        ),
        sa.Column("field_name", sa.String(80), nullable=False),
        sa.Column("previous_value", sa.Float(), nullable=False),
        sa.Column("override_value", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "review_status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column(
            "reviewed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("reviewed_at", sa.DateTime()),
        *ws(),
        sa.CheckConstraint(
            "review_status IN ('pending','approved','rejected')",
            name="ck_consumable_quota_override_review",
        ),
    )

    op.create_table(
        "consumable_legacy_migration_audits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column(
            "migrated_operation_id",
            sa.String(36),
            sa.ForeignKey("weld_consumable_operations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("migration_version", sa.String(40), nullable=False),
        sa.Column(
            "source_snapshot",
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
            "migrated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        *ws(),
        sa.UniqueConstraint(
            "source_type", "source_id", name="uq_consumable_legacy_migration_source"
        ),
    )


def downgrade():
    op.drop_table("consumable_legacy_migration_audits")
    op.drop_table("consumable_quota_override_audits")
    op.drop_table("consumable_quota_summaries")
    op.drop_index(
        "ix_consumable_quota_operation_trace", table_name="consumable_quota_operations"
    )
    op.drop_table("consumable_quota_operations")
    op.drop_index("ix_consumable_quota_run_trace", table_name="consumable_quota_runs")
    op.drop_table("consumable_quota_runs")
    op.drop_index("ix_consumable_rule_set_scope", table_name="consumable_rule_sets")
    op.drop_table("consumable_rule_sets")
    op.drop_table("consumable_groove_presets")
    op.drop_index(
        "ix_consumable_method_parameter_scope",
        table_name="consumable_method_parameters",
    )
    op.drop_table("consumable_method_parameters")
    op.drop_column("weld_consumable_operations", "package_size_kg")
    op.drop_column("weld_consumable_operations", "area_allocation_ratio")
    for name in (
        "enterprise_correction_factor",
        "flux_loss_ratio",
        "spatter_loss_ratio",
        "electrode_stub_loss_ratio",
    ):
        op.drop_column("weld_consumable_operations", name)
    for name in (
        "parameter_effective_to",
        "parameter_effective_from",
        "parameter_approval_status",
        "parameter_version",
        "applicable_welding_methods",
        "consumable_type",
        "default_deposition_rate_kg_h",
        "default_deposition_efficiency",
        "density_g_cm3",
    ):
        op.drop_column("welding_materials", name)

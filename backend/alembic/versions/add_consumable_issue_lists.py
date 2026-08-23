"""add P6 issue lists, inventory links and actual usage

Revision ID: add_consumable_issue_lists
Revises: add_consumable_quota_management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_consumable_issue_lists"
down_revision = "add_consumable_quota_management"
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
    # ``material_transactions`` belonged to an optional legacy inventory
    # module and is absent from some otherwise valid installations. Preserve
    # the linkage column everywhere and add the FK only where its target exists.
    material_transaction_fk = []
    if sa.inspect(op.get_bind()).has_table("material_transactions"):
        material_transaction_fk.append(
            sa.ForeignKey("material_transactions.id", ondelete="RESTRICT")
        )
    op.add_column(
        "weld_consumable_operations",
        sa.Column(
            "gas_material_id",
            sa.Integer(),
            sa.ForeignKey("welding_materials.id", ondelete="RESTRICT"),
        ),
    )
    op.add_column(
        "consumable_quota_operations",
        sa.Column(
            "gas_material_id",
            sa.Integer(),
            sa.ForeignKey("welding_materials.id", ondelete="RESTRICT"),
        ),
    )
    op.create_table(
        "consumable_issue_lists",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "quota_run_id",
            sa.String(36),
            sa.ForeignKey("consumable_quota_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
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
        sa.Column("document_number", sa.String(100), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="suggested"),
        sa.Column(
            "generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("issued_at", sa.DateTime()),
        sa.Column(
            "source_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "summary_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        *ws(),
        sa.CheckConstraint(
            "status IN ('suggested','approved','issued','closed','superseded')",
            name="ck_consumable_issue_list_status",
        ),
        sa.UniqueConstraint(
            "quota_run_id", "version_number", name="uq_consumable_issue_list_version"
        ),
        sa.UniqueConstraint(
            "workspace_type",
            "company_id",
            "user_id",
            "document_number",
            name="uq_consumable_issue_list_document",
        ),
    )
    op.create_index(
        "ix_consumable_issue_list_product",
        "consumable_issue_lists",
        ["product_revision_id", "sequence_revision_id", "status"],
    )
    op.create_table(
        "consumable_issue_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "issue_list_id",
            sa.String(36),
            sa.ForeignKey("consumable_issue_lists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column(
            "material_id",
            sa.Integer(),
            sa.ForeignKey("welding_materials.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("material_code", sa.String(100), nullable=False),
        sa.Column("material_name", sa.String(255), nullable=False),
        sa.Column("specification", sa.String(255)),
        sa.Column("batch_requirement", sa.String(255), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("theoretical_quantity", sa.Float(), nullable=False),
        sa.Column("quota_quantity", sa.Float(), nullable=False),
        sa.Column("suggested_quantity", sa.Float(), nullable=False),
        sa.Column("available_stock_snapshot", sa.Float(), nullable=False),
        sa.Column("shortage_quantity", sa.Float(), nullable=False),
        sa.Column(
            "actual_issued_quantity", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column(
            "actual_returned_quantity", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column(
            "actual_consumed_quantity", sa.Float(), nullable=False, server_default="0"
        ),
        sa.Column(
            "trace_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        *ws(),
        sa.CheckConstraint(
            "category IN ('solid_consumable','flux','shielding_gas')",
            name="ck_consumable_issue_item_category",
        ),
        sa.UniqueConstraint(
            "issue_list_id", "line_number", name="uq_consumable_issue_item_line"
        ),
    )
    op.create_index(
        "ix_consumable_issue_item_material",
        "consumable_issue_items",
        ["issue_list_id", "material_id", "category"],
    )
    op.create_table(
        "consumable_actual_usage_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "issue_list_id",
            sa.String(36),
            sa.ForeignKey("consumable_issue_lists.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "issue_item_id",
            sa.String(36),
            sa.ForeignKey("consumable_issue_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "quota_operation_id",
            sa.String(36),
            sa.ForeignKey("consumable_quota_operations.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "material_id",
            sa.Integer(),
            sa.ForeignKey("welding_materials.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "material_transaction_id",
            sa.Integer(),
            *material_transaction_fk,
        ),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("batch_number", sa.String(100)),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "recorded_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "recorded_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "trace_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        *ws(),
        sa.CheckConstraint(
            "event_type IN ('issue','return','consume')",
            name="ck_consumable_actual_usage_event_type",
        ),
        sa.CheckConstraint("quantity > 0", name="ck_consumable_actual_usage_quantity"),
        sa.UniqueConstraint(
            "idempotency_key", name="uq_consumable_actual_usage_idempotency"
        ),
    )
    op.create_index(
        "ix_consumable_actual_usage_trace",
        "consumable_actual_usage_events",
        ["issue_list_id", "issue_item_id", "event_type"],
    )


def downgrade():
    op.drop_index(
        "ix_consumable_actual_usage_trace", table_name="consumable_actual_usage_events"
    )
    op.drop_table("consumable_actual_usage_events")
    op.drop_index(
        "ix_consumable_issue_item_material", table_name="consumable_issue_items"
    )
    op.drop_table("consumable_issue_items")
    op.drop_index(
        "ix_consumable_issue_list_product", table_name="consumable_issue_lists"
    )
    op.drop_table("consumable_issue_lists")
    op.drop_column("consumable_quota_operations", "gas_material_id")
    op.drop_column("weld_consumable_operations", "gas_material_id")

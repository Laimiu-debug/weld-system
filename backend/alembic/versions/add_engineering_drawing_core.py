"""Add P3 engineering project, drawing revision, and review core."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "add_engineering_drawing_core"
down_revision = "add_qualification_capability"
branch_labels = None
depends_on = None

WS = [
    sa.Column(
        "user_id",
        sa.Integer(),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("workspace_type", sa.String(20), nullable=False),
    sa.Column(
        "company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE")
    ),
    sa.Column(
        "factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="SET NULL")
    ),
    sa.Column("access_level", sa.String(20), nullable=False, server_default="private"),
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


def ws():
    return [column._copy() for column in WS]


def upgrade() -> None:
    # Drawings reuse the private smart-import document store.
    op.drop_constraint("ck_import_batch_target", "import_batches", type_="check")
    op.create_check_constraint(
        "ck_import_batch_target",
        "import_batches",
        "target_entity_type IN ('wps','pqr','ppqr','welder','drawing')",
    )
    op.drop_constraint("ck_source_document_type", "source_documents", type_="check")
    op.create_check_constraint(
        "ck_source_document_type",
        "source_documents",
        "document_type IN ('wps','pqr','ppqr','welder','drawing','unknown')",
    )

    op.create_table(
        "engineering_projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *ws(),
        sa.CheckConstraint(
            "status IN ('active','archived')", name="ck_engineering_project_status"
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_project_workspace",
        ),
        sa.UniqueConstraint(
            "workspace_type",
            "company_id",
            "user_id",
            "code",
            name="uq_engineering_project_code",
        ),
    )
    op.create_index(
        "ix_engineering_project_workspace",
        "engineering_projects",
        ["workspace_type", "company_id", "user_id"],
    )

    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("engineering_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("product_type", sa.String(100)),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("current_revision_number", sa.Integer()),
        *ws(),
        sa.CheckConstraint(
            "status IN ('draft','active','archived')",
            name="ck_engineering_product_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_product_workspace",
        ),
        sa.UniqueConstraint("project_id", "code", name="uq_engineering_product_code"),
    )
    op.create_index(
        "ix_engineering_product_workspace",
        "engineering_products",
        ["workspace_type", "company_id", "user_id"],
    )

    op.create_table(
        "product_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column(
            "parent_revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="SET NULL"),
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "drawing_document_id",
            sa.String(36),
            sa.ForeignKey("source_documents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("drawing_sha256", sa.String(64), nullable=False),
        sa.Column("drawing_filename", sa.String(255), nullable=False),
        sa.Column(
            "drawing_page_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "drawing_metadata", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("data_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "parse_status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column(
            "approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("change_summary", sa.Text()),
        *ws(),
        sa.CheckConstraint(
            "status IN ('draft','review','approved','superseded')",
            name="ck_product_revision_status",
        ),
        sa.CheckConstraint(
            "parse_status IN ('pending','processing','completed','failed')",
            name="ck_product_revision_parse_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_product_revision_workspace",
        ),
        sa.UniqueConstraint(
            "product_id", "revision_number", name="uq_product_revision_number"
        ),
    )
    op.create_index(
        "ix_product_revision_workspace",
        "product_revisions",
        ["workspace_type", "company_id", "user_id"],
    )

    op.create_table(
        "parts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_part_id",
            sa.String(36),
            sa.ForeignKey("parts.id", ondelete="SET NULL"),
        ),
        sa.Column("part_number", sa.String(100)),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("material_spec", sa.String(200)),
        sa.Column("material_group", sa.String(80)),
        sa.Column("thickness_mm", sa.Float()),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("assembly_path", sa.String(500)),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float()),
        sa.Column(
            "review_status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        *ws(),
        sa.CheckConstraint(
            "review_status IN ('pending','accepted','corrected')",
            name="ck_engineering_part_review",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_part_workspace",
        ),
    )
    op.create_index(
        "ix_engineering_part_revision",
        "engineering_parts",
        ["revision_id", "is_deleted"],
    )

    op.create_table(
        "weld_joints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("weld_number", sa.String(100), nullable=False),
        sa.Column(
            "part_a_id", sa.String(36), sa.ForeignKey("parts.id", ondelete="SET NULL")
        ),
        sa.Column(
            "part_b_id", sa.String(36), sa.ForeignKey("parts.id", ondelete="SET NULL")
        ),
        sa.Column("joint_type", sa.String(100)),
        sa.Column("groove_type", sa.String(100)),
        sa.Column("groove_angle", sa.Float()),
        sa.Column("root_gap", sa.Float()),
        sa.Column("root_face", sa.Float()),
        sa.Column("weld_size", sa.Float()),
        sa.Column("length_mm", sa.Float()),
        sa.Column("weld_position", sa.String(80)),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float()),
        sa.Column(
            "review_status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        *ws(),
        sa.CheckConstraint(
            "review_status IN ('pending','accepted','corrected')",
            name="ck_weld_joint_review",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_joint_workspace",
        ),
    )
    op.create_index(
        "ix_weld_joint_revision", "weld_joints", ["revision_id", "is_deleted"]
    )

    op.create_table(
        "weld_requirements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "weld_joint_id",
            sa.String(36),
            sa.ForeignKey("weld_joints.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "nde_methods", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column("nde_rate", sa.String(80)),
        sa.Column("pwht_required", sa.Boolean()),
        sa.Column("pwht_temperature", sa.String(100)),
        sa.Column("pwht_duration", sa.String(100)),
        sa.Column("impact_required", sa.Boolean()),
        sa.Column("impact_temperature", sa.String(100)),
        sa.Column("special_requirements", sa.Text()),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float()),
        sa.Column(
            "review_status", sa.String(20), nullable=False, server_default="pending"
        ),
        *ws(),
        sa.CheckConstraint(
            "review_status IN ('pending','accepted','corrected')",
            name="ck_weld_requirement_review",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_requirement_workspace",
        ),
    )
    op.create_index(
        "ix_weld_requirement_revision",
        "weld_requirements",
        ["revision_id", "weld_joint_id"],
    )

    op.create_table(
        "drawing_parse_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "extraction_job_id",
            sa.String(36),
            sa.ForeignKey("extraction_jobs.id", ondelete="SET NULL"),
        ),
        sa.Column("provider", sa.String(80)),
        sa.Column("model", sa.String(120)),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("schema_version", sa.String(30), nullable=False),
        sa.Column(
            "output_snapshot", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("risks", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("error_message", sa.Text()),
        sa.Column("finished_at", sa.DateTime()),
        *ws(),
        sa.CheckConstraint(
            "status IN ('processing','completed','failed')",
            name="ck_drawing_parse_status",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_drawing_parse_workspace",
        ),
    )
    op.create_index(
        "ix_drawing_parse_revision", "drawing_parse_runs", ["revision_id", "created_at"]
    )

    op.create_table(
        "engineering_review_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.String(36)),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column(
            "previous_value", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("new_value", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "affected_joint_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("reason", sa.Text()),
        *ws(),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_review_workspace",
        ),
    )
    op.create_index(
        "ix_engineering_review_revision",
        "engineering_review_records",
        ["revision_id", "created_at"],
    )

    op.create_table(
        "engineering_dependency_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "revision_id",
            sa.String(36),
            sa.ForeignKey("product_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dependency_type", sa.String(20), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column(
            "affected_joint_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("source_data_version", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column(
            "invalidated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.DateTime()),
        *ws(),
        sa.CheckConstraint(
            "dependency_type IN ('matching','sequence','quota')",
            name="ck_engineering_dependency_type",
        ),
        sa.CheckConstraint(
            "status IN ('fresh','stale')", name="ck_engineering_dependency_status"
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_dependency_workspace",
        ),
    )
    op.create_index(
        "ix_engineering_dependency_revision",
        "engineering_dependency_states",
        ["revision_id", "status"],
    )


def downgrade() -> None:
    for table in (
        "engineering_dependency_states",
        "engineering_review_records",
        "drawing_parse_runs",
        "weld_requirements",
        "weld_joints",
        "parts",
        "product_revisions",
        "products",
        "engineering_projects",
    ):
        op.drop_table(table)
    op.drop_constraint("ck_source_document_type", "source_documents", type_="check")
    op.create_check_constraint(
        "ck_source_document_type",
        "source_documents",
        "document_type IN ('wps','pqr','ppqr','welder','unknown')",
    )
    op.drop_constraint("ck_import_batch_target", "import_batches", type_="check")
    op.create_check_constraint(
        "ck_import_batch_target",
        "import_batches",
        "target_entity_type IN ('wps','pqr','ppqr','welder')",
    )

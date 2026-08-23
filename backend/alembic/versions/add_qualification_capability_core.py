"""Add P2 qualification rule packs, results, and WPS/PQR support links."""
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_qualification_capability"
down_revision = "add_smart_import_progress_detail"
branch_labels = None
depends_on = None


PACK_ID = "47014000-2023-4000-8000-000000000001"


def upgrade() -> None:
    rule_packs = op.create_table(
        "qualification_rule_packs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("standard_code", sa.String(80), nullable=False),
        sa.Column("edition", sa.String(30), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("input_schema", postgresql.JSONB(), nullable=False),
        sa.Column("output_schema", postgresql.JSONB(), nullable=False),
        sa.Column("rules", postgresql.JSONB(), nullable=False),
        sa.Column("clause_references", postgresql.JSONB(), nullable=False),
        sa.Column("compliance_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("retired_at", sa.DateTime()),
        sa.Column(
            "created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft','review','published','retired')",
            name="ck_qualification_rule_pack_status",
        ),
        sa.UniqueConstraint(
            "code", "version", name="uq_qualification_rule_pack_version"
        ),
    )
    op.create_index(
        "ix_qualification_rule_pack_standard_status",
        "qualification_rule_packs",
        ["standard_code", "edition", "status"],
    )
    op.create_index(
        "ix_qualification_rule_packs_standard_code",
        "qualification_rule_packs",
        ["standard_code"],
    )
    op.create_index(
        "ix_qualification_rule_packs_status",
        "qualification_rule_packs",
        ["status"],
    )

    op.bulk_insert(
        rule_packs,
        [
            {
                "id": PACK_ID,
                "code": "NBT47014_2023",
                "name": "NB/T 47014—2023 承压设备焊接工艺评定",
                "standard_code": "NB/T 47014",
                "edition": "2023",
                "version": "1.0.0",
                "status": "published",
                "input_schema": {
                    "required": [
                        "qualification_result",
                        "approval_status",
                        "welding_processes",
                        "material_group",
                        "test_piece_thickness_mm",
                        "joint_type",
                        "welding_position",
                    ],
                    "optional": [
                        "test_piece_diameter_mm",
                        "test_piece_form",
                        "deposited_thickness_by_process",
                        "pwht_performed",
                        "impact_test_performed",
                        "impact_test_temperature_c",
                    ],
                },
                "output_schema": {
                    "dimensions": [
                        "thickness",
                        "diameter",
                        "positions",
                        "material_groups",
                        "welding_processes",
                        "pwht",
                        "impact",
                    ],
                    "outcomes": [
                        "qualified",
                        "not_qualified",
                        "needs_confirmation",
                        "insufficient_data",
                    ],
                },
                "rules": [
                    {"id": "NBT47014-2023-BASE", "kind": "eligibility"},
                    {"id": "NBT47014-2023-THICKNESS-CONSERVATIVE", "kind": "thickness"},
                    {"id": "NBT47014-2023-EXACT-DIMENSIONS", "kind": "exact_only"},
                    {"id": "NBT47014-2023-COMBINED-PROCESS", "kind": "manual_boundary"},
                ],
                "clause_references": [
                    {
                        "standard": "NB/T 47014—2023",
                        "locator": "焊接工艺评定因素及评定规则",
                        "quotation": None,
                    }
                ],
                "compliance_metadata": {
                    "official_registry": "https://std.samr.gov.cn/",
                    "citation_mode": "standard_and_locator_only",
                    "contains_standard_text": False,
                    "implementation_policy": "conservative_subset_requires_licensed_verification",
                },
                "published_at": datetime(2024, 6, 28),
                "retired_at": None,
                "created_by": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        ],
    )

    op.create_table(
        "pqr_qualification_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "pqr_id",
            sa.Integer(),
            sa.ForeignKey("pqr.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pqr_version_key", sa.String(100), nullable=False),
        sa.Column("pqr_snapshot_hash", sa.String(64), nullable=False),
        sa.Column(
            "rule_pack_id",
            sa.String(36),
            sa.ForeignKey("qualification_rule_packs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rule_pack_version", sa.String(40), nullable=False),
        sa.Column("calculation_key", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(30), nullable=False),
        sa.Column("input_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("basis", postgresql.JSONB(), nullable=False),
        sa.Column("missing_fields", postgresql.JSONB(), nullable=False),
        sa.Column("boundary_conditions", postgresql.JSONB(), nullable=False),
        sa.Column("requires_human_confirmation", sa.Boolean(), nullable=False),
        sa.Column(
            "supersedes_result_id",
            sa.String(36),
            sa.ForeignKey("pqr_qualification_results.id", ondelete="SET NULL"),
        ),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column(
            "calculated_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("calculated_at", sa.DateTime(), nullable=False),
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
        sa.Column("access_level", sa.String(20), nullable=False),
        sa.CheckConstraint(
            "outcome IN ('qualified','not_qualified','needs_confirmation','insufficient_data')",
            name="ck_pqr_qualification_outcome",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_pqr_qualification_workspace",
        ),
    )
    op.create_index(
        "ix_pqr_qualification_results_calculation_key",
        "pqr_qualification_results",
        ["calculation_key"],
    )
    op.create_index(
        "ix_pqr_qualification_results_outcome", "pqr_qualification_results", ["outcome"]
    )
    op.create_index(
        "ix_pqr_qualification_results_is_current",
        "pqr_qualification_results",
        ["is_current"],
    )
    op.create_index(
        "ix_pqr_qualification_current",
        "pqr_qualification_results",
        ["pqr_id", "is_current"],
    )
    op.create_index(
        "ix_pqr_qualification_workspace",
        "pqr_qualification_results",
        ["workspace_type", "company_id", "user_id"],
    )

    op.create_table(
        "wps_pqr_support_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "wps_id",
            sa.Integer(),
            sa.ForeignKey("wps.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pqr_id",
            sa.Integer(),
            sa.ForeignKey("pqr.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "qualification_result_id",
            sa.String(36),
            sa.ForeignKey("pqr_qualification_results.id", ondelete="SET NULL"),
        ),
        sa.Column("wps_version_key", sa.String(100), nullable=False),
        sa.Column("pqr_version_key", sa.String(100), nullable=False),
        sa.Column("wps_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("pqr_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("wps_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("pqr_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("supported_processes", postgresql.JSONB(), nullable=False),
        sa.Column("qualified_scope", postgresql.JSONB(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("confirmation_status", sa.String(20), nullable=False),
        sa.Column("confirmation_note", sa.Text()),
        sa.Column(
            "confirmed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("confirmed_at", sa.DateTime()),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
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
        sa.Column("access_level", sa.String(20), nullable=False),
        sa.CheckConstraint(
            "source IN ('manual','legacy','smart_import','rule_match')",
            name="ck_wps_pqr_support_source",
        ),
        sa.CheckConstraint(
            "confirmation_status IN ('pending','confirmed','rejected')",
            name="ck_wps_pqr_support_confirmation",
        ),
        sa.CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_pqr_support_workspace",
        ),
        sa.UniqueConstraint(
            "wps_id",
            "pqr_id",
            "wps_version_key",
            "pqr_version_key",
            name="uq_wps_pqr_support_version",
        ),
    )
    op.create_index(
        "ix_wps_pqr_support_links_is_active", "wps_pqr_support_links", ["is_active"]
    )
    op.create_index(
        "ix_wps_pqr_support_wps_active",
        "wps_pqr_support_links",
        ["wps_id", "is_active"],
    )
    op.create_index(
        "ix_wps_pqr_support_pqr_active",
        "wps_pqr_support_links",
        ["pqr_id", "is_active"],
    )
    op.create_index(
        "ix_wps_pqr_support_workspace",
        "wps_pqr_support_links",
        ["workspace_type", "company_id", "user_id"],
    )

    # Preserve legacy PQR.wps_number links as pending relationships. They are not
    # silently confirmed because a number match alone is not engineering approval.
    op.execute(
        """
        INSERT INTO wps_pqr_support_links (
          id, wps_id, pqr_id, wps_version_key, pqr_version_key,
          wps_snapshot_hash, pqr_snapshot_hash, wps_snapshot, pqr_snapshot,
          supported_processes, qualified_scope, source, confirmation_status,
          is_active, created_by, created_at, user_id, workspace_type,
          company_id, factory_id, access_level
        )
        SELECT
          substr(md5(w.id::text || ':' || p.id::text),1,8) || '-' ||
          substr(md5(w.id::text || ':' || p.id::text),9,4) || '-4' ||
          substr(md5(w.id::text || ':' || p.id::text),14,3) || '-8' ||
          substr(md5(w.id::text || ':' || p.id::text),18,3) || '-' ||
          substr(md5(w.id::text || ':' || p.id::text),21,12),
          w.id, p.id,
          coalesce(w.revision, 'legacy') || '@' || coalesce(w.updated_at::text, w.created_at::text),
          'legacy@' || coalesce(p.updated_at::text, p.created_at::text),
          md5(w.id::text || ':' || coalesce(w.updated_at::text, '')),
          md5(p.id::text || ':' || coalesce(p.updated_at::text, '')),
          jsonb_build_object('id', w.id, 'wps_number', w.wps_number, 'revision', w.revision, 'updated_at', w.updated_at),
          jsonb_build_object('id', p.id, 'pqr_number', p.pqr_number, 'updated_at', p.updated_at),
          CASE WHEN p.welding_process IS NULL THEN '[]'::jsonb ELSE jsonb_build_array(p.welding_process) END,
          '{}'::jsonb, 'legacy', 'pending', true,
          coalesce(p.created_by, p.user_id), now(), p.user_id, p.workspace_type,
          p.company_id, p.factory_id, coalesce(p.access_level, 'private')
        FROM pqr p
        JOIN wps w ON w.wps_number = p.wps_number
          AND w.workspace_type = p.workspace_type
          AND (
            (p.workspace_type = 'personal' AND w.user_id = p.user_id)
            OR (p.workspace_type = 'enterprise' AND w.company_id = p.company_id)
          )
        WHERE p.wps_number IS NOT NULL AND p.wps_number <> ''
        ON CONFLICT DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_table("wps_pqr_support_links")
    op.drop_table("pqr_qualification_results")
    op.drop_table("qualification_rule_packs")

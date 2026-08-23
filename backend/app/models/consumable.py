"""Relational P6 geometry inputs and per-operation consumable inputs."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.models.engineering import WorkspaceMixin


def _uuid() -> str:
    return str(uuid4())


class ConsumableGeometryInput(WorkspaceMixin, Base):
    """Confirmed, reproducible geometry and length input for one weld joint."""

    __tablename__ = "consumable_geometry_inputs"
    id = Column(String(36), primary_key=True, default=_uuid)
    product_revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    weld_joint_id = Column(
        String(36), ForeignKey("weld_joints.id", ondelete="RESTRICT"), nullable=False
    )
    sequence_revision_id = Column(
        String(36), ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT")
    )
    sequence_step_id = Column(
        String(36), ForeignKey("weld_sequence_steps.id", ondelete="RESTRICT")
    )
    version_number = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="draft")
    source = Column(String(20), nullable=False, default="manual")
    formula_version = Column(String(40), nullable=False)

    groove_type = Column(String(20), nullable=False)
    thickness_mm = Column(Float, nullable=False, default=0)
    included_angle_deg = Column(Float, nullable=False, default=0)
    root_gap_mm = Column(Float, nullable=False, default=0)
    root_face_mm = Column(Float, nullable=False, default=0)
    radius_mm = Column(Float, nullable=False, default=0)
    upper_bevel_height_mm = Column(Float, nullable=False, default=0)
    lower_bevel_height_mm = Column(Float, nullable=False, default=0)
    leg_size_mm = Column(Float, nullable=False, default=0)
    reinforcement_mm = Column(Float, nullable=False, default=0)
    face_extra_each_side_mm = Column(Float, nullable=False, default=0)
    fill_factor = Column(Float, nullable=False, default=1)
    back_gouge_depth_mm = Column(Float, nullable=False, default=0)
    back_gouge_opening_width_mm = Column(Float)
    gouge_strategy = Column(String(30), nullable=False, default="explicit")
    reference_gouge_flare_ratio = Column(Float, nullable=False, default=0.5)

    length_type = Column(String(30), nullable=False)
    weld_count = Column(Integer, nullable=False, default=1)
    straight_length_mm = Column(Float)
    diameter_mm = Column(Float)
    diameter_basis = Column(String(20))
    included_length_angle_deg = Column(Float, nullable=False, default=360)
    manual_confirmed_length_mm = Column(Float)

    geometry_input_snapshot = Column(JSONB, nullable=False, default=dict)
    length_input_snapshot = Column(JSONB, nullable=False, default=dict)
    geometry_result_snapshot = Column(JSONB, nullable=False, default=dict)
    length_result_snapshot = Column(JSONB, nullable=False, default=dict)
    warnings = Column(JSONB, nullable=False, default=list)
    confirmed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    confirmed_at = Column(DateTime)
    confirmation_note = Column(Text)
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','confirmed','superseded')",
            name="ck_consumable_geometry_status",
        ),
        CheckConstraint(
            "source IN ('manual','drawing')", name="ck_consumable_geometry_source"
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_consumable_geometry_workspace",
        ),
        UniqueConstraint(
            "weld_joint_id", "version_number", name="uq_consumable_geometry_version"
        ),
        Index(
            "ix_consumable_geometry_product_joint",
            "product_revision_id",
            "weld_joint_id",
        ),
    )


class WeldConsumableOperation(WorkspaceMixin, Base):
    """One queryable operation; JSONB is used only for immutable snapshots."""

    __tablename__ = "weld_consumable_operations"
    id = Column(String(36), primary_key=True, default=_uuid)
    geometry_input_id = Column(
        String(36),
        ForeignKey("consumable_geometry_inputs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    weld_joint_id = Column(
        String(36), ForeignKey("weld_joints.id", ondelete="RESTRICT"), nullable=False
    )
    sequence_revision_id = Column(
        String(36),
        ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sequence_step_id = Column(
        String(36),
        ForeignKey("weld_sequence_steps.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False, default=1)
    operation_order = Column(Integer, nullable=False)
    operation_role = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    welding_method = Column(String(80), nullable=False)
    material_id = Column(
        Integer, ForeignKey("welding_materials.id", ondelete="RESTRICT")
    )
    flux_material_id = Column(
        Integer, ForeignKey("welding_materials.id", ondelete="RESTRICT")
    )
    area_source = Column(String(30), nullable=False)
    area_allocation_ratio = Column(Float, nullable=False, default=1)
    area_mm2 = Column(Float, nullable=False)
    length_mm = Column(Float, nullable=False)
    density_g_cm3 = Column(Float, nullable=False)
    deposition_efficiency = Column(Float, nullable=False)
    deposition_rate_kg_h = Column(Float)
    arc_time_h = Column(Float)
    arc_time_ratio = Column(Float)
    flux_wire_ratio = Column(Float)
    gas_flow_l_min = Column(Float)
    electrode_stub_loss_ratio = Column(Float, nullable=False, default=0)
    spatter_loss_ratio = Column(Float, nullable=False, default=0)
    flux_loss_ratio = Column(Float, nullable=False, default=0)
    enterprise_correction_factor = Column(Float, nullable=False, default=1)
    package_size_kg = Column(Float)
    pass_count_description = Column(Integer)
    input_snapshot = Column(JSONB, nullable=False, default=dict)
    result_snapshot = Column(JSONB, nullable=False, default=dict)
    formula_version = Column(String(40), nullable=False)
    __table_args__ = (
        CheckConstraint(
            "operation_role IN ('face_fill','back_gouge_fill','tack','custom')",
            name="ck_weld_consumable_operation_role",
        ),
        CheckConstraint(
            "status IN ('draft','calculated','superseded')",
            name="ck_weld_consumable_operation_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_consumable_operation_workspace",
        ),
        UniqueConstraint(
            "sequence_step_id",
            "version_number",
            "operation_order",
            name="uq_weld_consumable_operation_order",
        ),
        Index(
            "ix_weld_consumable_operation_trace",
            "product_revision_id",
            "weld_joint_id",
            "sequence_step_id",
        ),
    )


class ConsumableMethodParameter(WorkspaceMixin, Base):
    """Versioned enterprise/factory welding-method defaults."""

    __tablename__ = "consumable_method_parameters"
    id = Column(String(36), primary_key=True, default=_uuid)
    parameter_code = Column(String(80), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    welding_method = Column(String(80), nullable=False)
    consumable_type = Column(String(50), nullable=False)
    compatible_material_types = Column(JSONB, nullable=False, default=list)
    default_deposition_efficiency = Column(Float, nullable=False)
    default_deposition_rate_kg_h = Column(Float)
    default_flux_wire_ratio = Column(Float)
    default_gas_flow_l_min = Column(Float)
    default_arc_time_ratio = Column(Float)
    approval_status = Column(String(20), nullable=False, default="draft")
    effective_from = Column(DateTime)
    effective_to = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)
    supersedes_id = Column(
        String(36), ForeignKey("consumable_method_parameters.id", ondelete="RESTRICT")
    )
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approved_at = Column(DateTime)
    parameter_snapshot = Column(JSONB, nullable=False, default=dict)
    __table_args__ = (
        CheckConstraint(
            "approval_status IN ('draft','pending','approved','rejected','superseded')",
            name="ck_consumable_method_parameter_approval",
        ),
        UniqueConstraint(
            "workspace_type",
            "company_id",
            "factory_id",
            "parameter_code",
            "version_number",
            name="uq_consumable_method_parameter_version",
        ),
        Index(
            "ix_consumable_method_parameter_scope",
            "workspace_type",
            "company_id",
            "factory_id",
            "welding_method",
        ),
    )


class ConsumableGroovePreset(WorkspaceMixin, Base):
    """Versioned typical or company-specific groove preset."""

    __tablename__ = "consumable_groove_presets"
    id = Column(String(36), primary_key=True, default=_uuid)
    preset_code = Column(String(80), nullable=False)
    name = Column(String(200), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    groove_type = Column(String(20), nullable=False)
    parameter_values = Column(JSONB, nullable=False, default=dict)
    is_system_typical = Column(Boolean, nullable=False, default=False)
    approval_status = Column(String(20), nullable=False, default="draft")
    effective_from = Column(DateTime)
    effective_to = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)
    supersedes_id = Column(
        String(36), ForeignKey("consumable_groove_presets.id", ondelete="RESTRICT")
    )
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approved_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "approval_status IN ('draft','pending','approved','rejected','superseded')",
            name="ck_consumable_groove_preset_approval",
        ),
        UniqueConstraint(
            "workspace_type",
            "company_id",
            "factory_id",
            "preset_code",
            "version_number",
            name="uq_consumable_groove_preset_version",
        ),
    )


class ConsumableRuleSet(WorkspaceMixin, Base):
    """Approved, immutable-by-reference enterprise quota coefficients."""

    __tablename__ = "consumable_rule_sets"
    id = Column(String(36), primary_key=True, default=_uuid)
    rule_code = Column(String(80), nullable=False)
    name = Column(String(200), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="draft")
    formula_version = Column(String(40), nullable=False)
    electrode_stub_loss_ratio = Column(Float, nullable=False, default=0)
    spatter_loss_ratio = Column(Float, nullable=False, default=0)
    flux_loss_ratio = Column(Float, nullable=False, default=0)
    enterprise_correction_factor = Column(Float, nullable=False, default=1)
    packaging_rules = Column(JSONB, nullable=False, default=dict)
    effective_from = Column(DateTime)
    effective_to = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True)
    supersedes_id = Column(
        String(36), ForeignKey("consumable_rule_sets.id", ondelete="RESTRICT")
    )
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approved_at = Column(DateTime)
    frozen_snapshot = Column(JSONB, nullable=False, default=dict)
    snapshot_hash = Column(String(64), nullable=False)
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','pending','approved','rejected','superseded')",
            name="ck_consumable_rule_set_status",
        ),
        UniqueConstraint(
            "workspace_type",
            "company_id",
            "factory_id",
            "rule_code",
            "version_number",
            name="uq_consumable_rule_set_version",
        ),
        Index(
            "ix_consumable_rule_set_scope",
            "workspace_type",
            "company_id",
            "factory_id",
            "status",
        ),
    )


class ConsumableQuotaRun(WorkspaceMixin, Base):
    __tablename__ = "consumable_quota_runs"
    id = Column(String(36), primary_key=True, default=_uuid)
    product_revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sequence_revision_id = Column(
        String(36),
        ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_set_id = Column(
        String(36),
        ForeignKey("consumable_rule_sets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parent_run_id = Column(
        String(36), ForeignKey("consumable_quota_runs.id", ondelete="RESTRICT")
    )
    run_version = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="calculated")
    input_version_hash = Column(String(64), nullable=False)
    idempotency_key = Column(String(64), nullable=False)
    formula_version = Column(String(40), nullable=False)
    frozen_input_snapshot = Column(JSONB, nullable=False, default=dict)
    result_snapshot = Column(JSONB, nullable=False, default=dict)
    diff_snapshot = Column(JSONB, nullable=False, default=dict)
    stale_reasons = Column(JSONB, nullable=False, default=list)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approved_at = Column(DateTime)
    issued_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "status IN ('calculated','pending','approved','issued','stale','superseded')",
            name="ck_consumable_quota_run_status",
        ),
        UniqueConstraint("idempotency_key", name="uq_consumable_quota_run_idempotency"),
        UniqueConstraint(
            "product_revision_id",
            "sequence_revision_id",
            "run_version",
            name="uq_consumable_quota_run_version",
        ),
        Index(
            "ix_consumable_quota_run_trace",
            "product_revision_id",
            "sequence_revision_id",
            "status",
        ),
    )


class ConsumableQuotaOperation(WorkspaceMixin, Base):
    __tablename__ = "consumable_quota_operations"
    id = Column(String(36), primary_key=True, default=_uuid)
    run_id = Column(
        String(36),
        ForeignKey("consumable_quota_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_operation_id = Column(
        String(36),
        ForeignKey("weld_consumable_operations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    weld_joint_id = Column(
        String(36), ForeignKey("weld_joints.id", ondelete="RESTRICT"), nullable=False
    )
    sequence_step_id = Column(
        String(36),
        ForeignKey("weld_sequence_steps.id", ondelete="RESTRICT"),
        nullable=False,
    )
    operation_order = Column(Integer, nullable=False)
    operation_role = Column(String(30), nullable=False)
    welding_method = Column(String(80), nullable=False)
    material_id = Column(
        Integer, ForeignKey("welding_materials.id", ondelete="RESTRICT")
    )
    flux_material_id = Column(
        Integer, ForeignKey("welding_materials.id", ondelete="RESTRICT")
    )
    theoretical_deposit_kg = Column(Float, nullable=False)
    process_primary_kg = Column(Float, nullable=False)
    enterprise_primary_kg = Column(Float, nullable=False)
    package_rounded_primary_kg = Column(Float, nullable=False)
    suggested_primary_issue_kg = Column(Float, nullable=False)
    flux_kg = Column(Float, nullable=False, default=0)
    gas_l = Column(Float, nullable=False, default=0)
    arc_time_h = Column(Float, nullable=False, default=0)
    total_time_h = Column(Float, nullable=False, default=0)
    input_snapshot = Column(JSONB, nullable=False, default=dict)
    method_snapshot = Column(JSONB, nullable=False, default=dict)
    material_snapshot = Column(JSONB, nullable=False, default=dict)
    result_snapshot = Column(JSONB, nullable=False, default=dict)
    result_sources = Column(JSONB, nullable=False, default=dict)
    __table_args__ = (
        UniqueConstraint(
            "run_id", "source_operation_id", name="uq_consumable_quota_operation_source"
        ),
        Index(
            "ix_consumable_quota_operation_trace",
            "run_id",
            "weld_joint_id",
            "sequence_step_id",
        ),
    )


class ConsumableQuotaSummary(WorkspaceMixin, Base):
    __tablename__ = "consumable_quota_summaries"
    id = Column(String(36), primary_key=True, default=_uuid)
    run_id = Column(
        String(36),
        ForeignKey("consumable_quota_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    summary_type = Column(String(30), nullable=False, default="run_total")
    material_id = Column(
        Integer, ForeignKey("welding_materials.id", ondelete="RESTRICT")
    )
    material_type = Column(String(50), nullable=False)
    specification = Column(String(255))
    theoretical_kg = Column(Float, nullable=False, default=0)
    process_kg = Column(Float, nullable=False, default=0)
    enterprise_quota_kg = Column(Float, nullable=False, default=0)
    package_rounded_kg = Column(Float, nullable=False, default=0)
    suggested_issue_kg = Column(Float, nullable=False, default=0)
    gas_l = Column(Float, nullable=False, default=0)
    total_time_h = Column(Float, nullable=False, default=0)
    trace_snapshot = Column(JSONB, nullable=False, default=dict)
    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "summary_type",
            "material_id",
            name="uq_consumable_quota_summary_item",
        ),
    )


class ConsumableQuotaOverrideAudit(WorkspaceMixin, Base):
    __tablename__ = "consumable_quota_override_audits"
    id = Column(String(36), primary_key=True, default=_uuid)
    run_id = Column(
        String(36),
        ForeignKey("consumable_quota_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quota_operation_id = Column(
        String(36), ForeignKey("consumable_quota_operations.id", ondelete="RESTRICT")
    )
    field_name = Column(String(80), nullable=False)
    previous_value = Column(Float, nullable=False)
    override_value = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    review_status = Column(String(20), nullable=False, default="pending")
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('pending','approved','rejected')",
            name="ck_consumable_quota_override_review",
        ),
    )


class ConsumableLegacyMigrationAudit(WorkspaceMixin, Base):
    __tablename__ = "consumable_legacy_migration_audits"
    id = Column(String(36), primary_key=True, default=_uuid)
    source_type = Column(String(50), nullable=False)
    source_id = Column(String(100), nullable=False)
    migrated_operation_id = Column(
        String(36),
        ForeignKey("weld_consumable_operations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    migration_version = Column(String(40), nullable=False)
    source_snapshot = Column(JSONB, nullable=False, default=dict)
    warnings = Column(JSONB, nullable=False, default=list)
    migrated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint(
            "source_type", "source_id", name="uq_consumable_legacy_migration_source"
        ),
    )

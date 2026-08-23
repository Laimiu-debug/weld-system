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
    area_mm2 = Column(Float, nullable=False)
    length_mm = Column(Float, nullable=False)
    density_g_cm3 = Column(Float, nullable=False)
    deposition_efficiency = Column(Float, nullable=False)
    deposition_rate_kg_h = Column(Float)
    arc_time_h = Column(Float)
    arc_time_ratio = Column(Float)
    flux_wire_ratio = Column(Float)
    gas_flow_l_min = Column(Float)
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

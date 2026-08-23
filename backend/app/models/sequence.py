"""Versioned weld sequence planning, dependencies, validation and freezes."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
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


class WeldSequenceRevision(WorkspaceMixin, Base):
    __tablename__ = "weld_sequence_revisions"
    id = Column(String(36), primary_key=True, default=_uuid)
    product_revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False)
    parent_revision_id = Column(
        String(36), ForeignKey("weld_sequence_revisions.id", ondelete="SET NULL")
    )
    status = Column(String(20), nullable=False, default="draft")
    source_data_version = Column(Integer, nullable=False)
    template_code = Column(String(80), nullable=False, default="PRESSURE_VESSEL_V1")
    template_version = Column(String(30), nullable=False, default="1.0.0")
    strategy_snapshot = Column(JSONB, nullable=False, default=dict)
    source_match_snapshot = Column(JSONB, nullable=False, default=list)
    source_match_hash = Column(String(64), nullable=False)
    candidate_source = Column(String(20), nullable=False, default="deterministic")
    candidate_explanation = Column(Text)
    validation_result = Column(JSONB, nullable=False, default=dict)
    validation_hash = Column(String(64))
    change_summary = Column(Text)
    approval_instance_id = Column(
        Integer, ForeignKey("approval_instances.id", ondelete="SET NULL")
    )
    approval_snapshot_hash = Column(String(64))
    frozen_snapshot = Column(JSONB)
    frozen_hash = Column(String(64))
    submitted_at = Column(DateTime)
    approved_at = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','pending','approved','rejected','returned','superseded')",
            name="ck_weld_sequence_revision_status",
        ),
        CheckConstraint(
            "candidate_source IN ('deterministic','ai_assisted','manual')",
            name="ck_weld_sequence_candidate_source",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_sequence_revision_workspace",
        ),
        UniqueConstraint(
            "product_revision_id", "version_number", name="uq_weld_sequence_version"
        ),
        Index(
            "ix_weld_sequence_revision_product",
            "product_revision_id",
            "version_number",
        ),
    )


class WeldSequenceStep(WorkspaceMixin, Base):
    __tablename__ = "weld_sequence_steps"
    id = Column(String(36), primary_key=True, default=_uuid)
    sequence_revision_id = Column(
        String(36),
        ForeignKey("weld_sequence_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_code = Column(String(100), nullable=False)
    step_type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    order_index = Column(Integer, nullable=False)
    phase = Column(String(80), nullable=False)
    weld_joint_id = Column(
        String(36), ForeignKey("weld_joints.id", ondelete="RESTRICT")
    )
    match_freeze_id = Column(
        String(36), ForeignKey("wps_match_freezes.id", ondelete="RESTRICT")
    )
    is_locked = Column(Boolean, nullable=False, default=False)
    constraint_tags = Column(JSONB, nullable=False, default=list)
    process_parameters = Column(JSONB, nullable=False, default=dict)
    inspection_node = Column(JSONB, nullable=False, default=dict)
    explanation = Column(Text, nullable=False)
    source_snapshot = Column(JSONB, nullable=False, default=dict)
    __table_args__ = (
        CheckConstraint(
            "step_type IN ('assembly','weld','nde','pwht','inspection','closure')",
            name="ck_weld_sequence_step_type",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_sequence_step_workspace",
        ),
        UniqueConstraint(
            "sequence_revision_id", "step_code", name="uq_weld_sequence_step_code"
        ),
        UniqueConstraint(
            "sequence_revision_id", "order_index", name="uq_weld_sequence_step_order"
        ),
        Index("ix_weld_sequence_step_revision", "sequence_revision_id", "order_index"),
    )


class StepDependency(WorkspaceMixin, Base):
    __tablename__ = "step_dependencies"
    id = Column(String(36), primary_key=True, default=_uuid)
    sequence_revision_id = Column(
        String(36),
        ForeignKey("weld_sequence_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    predecessor_step_id = Column(
        String(36),
        ForeignKey("weld_sequence_steps.id", ondelete="CASCADE"),
        nullable=False,
    )
    successor_step_id = Column(
        String(36),
        ForeignKey("weld_sequence_steps.id", ondelete="CASCADE"),
        nullable=False,
    )
    dependency_type = Column(String(30), nullable=False)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    explanation = Column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint(
            "dependency_type IN ('assembly','accessibility','nde','pwht','closed_space','manual')",
            name="ck_step_dependency_type",
        ),
        CheckConstraint(
            "predecessor_step_id <> successor_step_id",
            name="ck_step_dependency_not_self",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_step_dependency_workspace",
        ),
        UniqueConstraint(
            "sequence_revision_id",
            "predecessor_step_id",
            "successor_step_id",
            name="uq_step_dependency_edge",
        ),
        Index("ix_step_dependency_revision", "sequence_revision_id"),
    )

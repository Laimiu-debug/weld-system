"""P7 production release, resource authorization and execution trace models."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
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


class ProductionReleaseBatch(WorkspaceMixin, Base):
    __tablename__ = "production_release_batches"
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
    consumable_issue_list_id = Column(
        String(36), ForeignKey("consumable_issue_lists.id", ondelete="RESTRICT")
    )
    status = Column(String(20), nullable=False, default="released")
    idempotency_key = Column(String(64), nullable=False)
    sequence_frozen_hash = Column(String(64), nullable=False)
    source_snapshot = Column(JSONB, nullable=False, default=dict)
    released_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    released_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint(
            "status IN ('released','superseded','cancelled')",
            name="ck_production_release_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_release_workspace",
        ),
        UniqueConstraint("idempotency_key", name="uq_production_release_idempotency"),
        UniqueConstraint("sequence_revision_id", name="uq_production_release_sequence"),
        Index("ix_production_release_product", "product_revision_id", "status"),
    )


class ProductionResourceAuthorization(WorkspaceMixin, Base):
    __tablename__ = "production_resource_authorizations"
    id = Column(String(36), primary_key=True, default=_uuid)
    production_task_id = Column(
        Integer, ForeignKey("production_tasks.id", ondelete="RESTRICT"), nullable=False
    )
    welder_id = Column(
        Integer, ForeignKey("welders.id", ondelete="RESTRICT"), nullable=False
    )
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="RESTRICT"))
    wps_id = Column(Integer, ForeignKey("wps.id", ondelete="RESTRICT"), nullable=False)
    qualification_status = Column(String(20), nullable=False)
    qualification_snapshot = Column(JSONB, nullable=False, default=dict)
    override_reason = Column(Text)
    authorized_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    authorized_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint(
            "qualification_status IN ('qualified','pending_override','authorized','rejected')",
            name="ck_production_resource_qualification",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_resource_workspace",
        ),
        Index(
            "ix_production_resource_task", "production_task_id", "qualification_status"
        ),
    )


class ProductionQualityNode(WorkspaceMixin, Base):
    __tablename__ = "production_quality_nodes"
    id = Column(String(36), primary_key=True, default=_uuid)
    production_release_id = Column(
        String(36),
        ForeignKey("production_release_batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    production_task_id = Column(
        Integer, ForeignKey("production_tasks.id", ondelete="RESTRICT"), nullable=False
    )
    sequence_step_id = Column(
        String(36),
        ForeignKey("weld_sequence_steps.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quality_inspection_id = Column(
        Integer, ForeignKey("quality_inspections.id", ondelete="RESTRICT")
    )
    node_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    frozen_snapshot = Column(JSONB, nullable=False, default=dict)
    __table_args__ = (
        CheckConstraint(
            "node_type IN ('nde','pwht','inspection','closure')",
            name="ck_production_quality_node_type",
        ),
        CheckConstraint(
            "status IN ('pending','in_progress','passed','failed','waived')",
            name="ck_production_quality_node_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_quality_node_workspace",
        ),
        UniqueConstraint(
            "production_release_id",
            "sequence_step_id",
            name="uq_production_quality_release_step",
        ),
    )


class ProductionExecutionTrace(WorkspaceMixin, Base):
    __tablename__ = "production_execution_traces"
    id = Column(String(36), primary_key=True, default=_uuid)
    production_release_id = Column(
        String(36),
        ForeignKey("production_release_batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    production_task_id = Column(
        Integer, ForeignKey("production_tasks.id", ondelete="RESTRICT"), nullable=False
    )
    production_record_id = Column(
        Integer, ForeignKey("production_records.id", ondelete="RESTRICT")
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
    weld_joint_id = Column(
        String(36), ForeignKey("weld_joints.id", ondelete="RESTRICT")
    )
    welder_id = Column(Integer, ForeignKey("welders.id", ondelete="RESTRICT"))
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="RESTRICT"))
    wps_id = Column(Integer, ForeignKey("wps.id", ondelete="RESTRICT"))
    status = Column(String(20), nullable=False, default="recorded")
    design_snapshot_hash = Column(String(64), nullable=False)
    actual_parameters = Column(JSONB, nullable=False, default=dict)
    consumable_usage_event_ids = Column(JSONB, nullable=False, default=list)
    repair_snapshot = Column(JSONB, nullable=False, default=dict)
    quality_snapshot = Column(JSONB, nullable=False, default=dict)
    idempotency_key = Column(String(64), nullable=False)
    recorded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint(
            "status IN ('recorded','completed','voided')",
            name="ck_production_execution_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_execution_workspace",
        ),
        UniqueConstraint("idempotency_key", name="uq_production_execution_idempotency"),
        Index(
            "ix_production_execution_trace",
            "production_release_id",
            "sequence_step_id",
            "recorded_at",
        ),
    )


class ProductionSequenceChangeRequest(WorkspaceMixin, Base):
    __tablename__ = "production_sequence_change_requests"
    id = Column(String(36), primary_key=True, default=_uuid)
    production_release_id = Column(
        String(36),
        ForeignKey("production_release_batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_sequence_revision_id = Column(
        String(36),
        ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    proposed_sequence_revision_id = Column(
        String(36), ForeignKey("weld_sequence_revisions.id", ondelete="RESTRICT")
    )
    reason = Column(Text, nullable=False)
    impact_snapshot = Column(JSONB, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="pending")
    approval_instance_id = Column(
        Integer, ForeignKey("approval_instances.id", ondelete="SET NULL")
    )
    requested_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    decided_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    decided_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','approved','rejected','applied')",
            name="ck_production_sequence_change_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_production_sequence_change_workspace",
        ),
        Index(
            "ix_production_sequence_change_release", "production_release_id", "status"
        ),
    )

"""Deterministic, explainable WPS/PQR matching and frozen approvals."""
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


class WPSMatchRun(WorkspaceMixin, Base):
    __tablename__ = "wps_match_runs"
    id = Column(String(36), primary_key=True, default=_uuid)
    revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_type = Column(String(30), nullable=False, default="manual")
    status = Column(String(20), nullable=False, default="processing")
    source_data_version = Column(Integer, nullable=False)
    rule_pack_code = Column(String(80), nullable=False, default="NBT47014_2023")
    rule_pack_version = Column(String(40), nullable=False)
    capability_snapshot_hash = Column(String(64), nullable=False)
    capability_snapshot = Column(JSONB, nullable=False, default=list)
    policy_snapshot = Column(JSONB, nullable=False, default=dict)
    target_joint_ids = Column(JSONB, nullable=False, default=list)
    candidate_count = Column(Integer, nullable=False, default=0)
    gap_count = Column(Integer, nullable=False, default=0)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approved_at = Column(DateTime)
    completed_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "trigger_type IN ('manual','field_change','drawing_change')",
            name="ck_wps_match_run_trigger",
        ),
        CheckConstraint(
            "status IN ('processing','completed','approved','superseded','failed')",
            name="ck_wps_match_run_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_match_run_workspace",
        ),
        Index("ix_wps_match_run_revision", "revision_id", "created_at"),
    )


class WPSMatchCandidate(WorkspaceMixin, Base):
    __tablename__ = "wps_match_candidates"
    id = Column(String(36), primary_key=True, default=_uuid)
    run_id = Column(
        String(36), ForeignKey("wps_match_runs.id", ondelete="CASCADE"), nullable=False
    )
    weld_joint_id = Column(
        String(36), ForeignKey("weld_joints.id", ondelete="CASCADE"), nullable=False
    )
    support_link_id = Column(
        String(36),
        ForeignKey("wps_pqr_support_links.id", ondelete="RESTRICT"),
        nullable=False,
    )
    wps_id = Column(Integer, ForeignKey("wps.id", ondelete="RESTRICT"), nullable=False)
    pqr_id = Column(Integer, ForeignKey("pqr.id", ondelete="RESTRICT"), nullable=False)
    rank = Column(Integer, nullable=False)
    decision = Column(String(30), nullable=False)
    score = Column(Float, nullable=False, default=0)
    is_recommended = Column(Boolean, nullable=False, default=False)
    confirmation_status = Column(String(20), nullable=False, default="pending")
    confirmation_note = Column(Text)
    confirmed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    confirmed_at = Column(DateTime)
    requirement_snapshot = Column(JSONB, nullable=False, default=dict)
    wps_snapshot = Column(JSONB, nullable=False, default=dict)
    pqr_snapshot = Column(JSONB, nullable=False, default=dict)
    qualification_snapshot = Column(JSONB, nullable=False, default=dict)
    rule_snapshot = Column(JSONB, nullable=False, default=dict)
    __table_args__ = (
        CheckConstraint(
            "decision IN ('eligible','not_eligible','needs_confirmation')",
            name="ck_wps_match_candidate_decision",
        ),
        CheckConstraint(
            "confirmation_status IN ('pending','confirmed','rejected')",
            name="ck_wps_match_candidate_confirmation",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_match_candidate_workspace",
        ),
        UniqueConstraint(
            "run_id",
            "weld_joint_id",
            "support_link_id",
            name="uq_wps_match_candidate_link",
        ),
        Index("ix_wps_match_candidate_joint_rank", "run_id", "weld_joint_id", "rank"),
    )


class WPSMatchCriterion(WorkspaceMixin, Base):
    __tablename__ = "wps_match_criteria"
    id = Column(String(36), primary_key=True, default=_uuid)
    candidate_id = Column(
        String(36),
        ForeignKey("wps_match_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    dimension = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False)
    required_value = Column(JSONB, nullable=False, default=dict)
    available_value = Column(JSONB, nullable=False, default=dict)
    basis = Column(JSONB, nullable=False, default=dict)
    message = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    __table_args__ = (
        CheckConstraint(
            "status IN ('pass','fail','boundary','insufficient')",
            name="ck_wps_match_criterion_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_match_criterion_workspace",
        ),
        UniqueConstraint(
            "candidate_id", "dimension", name="uq_wps_match_criterion_dimension"
        ),
        Index("ix_wps_match_criterion_candidate", "candidate_id", "sort_order"),
    )


class WPSCapabilityGap(WorkspaceMixin, Base):
    __tablename__ = "wps_capability_gaps"
    id = Column(String(36), primary_key=True, default=_uuid)
    run_id = Column(
        String(36), ForeignKey("wps_match_runs.id", ondelete="CASCADE"), nullable=False
    )
    weld_joint_id = Column(
        String(36), ForeignKey("weld_joints.id", ondelete="CASCADE"), nullable=False
    )
    dimension = Column(String(40), nullable=False)
    code = Column(String(80), nullable=False)
    severity = Column(String(20), nullable=False, default="blocking")
    message = Column(Text, nullable=False)
    requirement_snapshot = Column(JSONB, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="open")
    linked_ppqr_id = Column(Integer, ForeignKey("ppqr.id", ondelete="SET NULL"))
    qualification_plan_reference = Column(String(200))
    resolved_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "severity IN ('blocking','warning')", name="ck_wps_capability_gap_severity"
        ),
        CheckConstraint(
            "status IN ('open','linked','resolved','dismissed')",
            name="ck_wps_capability_gap_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_capability_gap_workspace",
        ),
        Index("ix_wps_capability_gap_run_joint", "run_id", "weld_joint_id"),
    )


class WPSMatchFreeze(WorkspaceMixin, Base):
    __tablename__ = "wps_match_freezes"
    id = Column(String(36), primary_key=True, default=_uuid)
    run_id = Column(
        String(36), ForeignKey("wps_match_runs.id", ondelete="RESTRICT"), nullable=False
    )
    candidate_id = Column(
        String(36),
        ForeignKey("wps_match_candidates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    weld_joint_id = Column(
        String(36), ForeignKey("weld_joints.id", ondelete="RESTRICT"), nullable=False
    )
    frozen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    frozen_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    weld_requirement_hash = Column(String(64), nullable=False)
    wps_snapshot_hash = Column(String(64), nullable=False)
    pqr_snapshot_hash = Column(String(64), nullable=False)
    rule_snapshot_hash = Column(String(64), nullable=False)
    frozen_snapshot = Column(JSONB, nullable=False, default=dict)
    __table_args__ = (
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_match_freeze_workspace",
        ),
        UniqueConstraint("run_id", "weld_joint_id", name="uq_wps_match_freeze_joint"),
        Index("ix_wps_match_freeze_revision", "revision_id", "weld_joint_id"),
    )

"""Versioned welding-procedure qualification rules, results, and support links."""
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


def _uuid() -> str:
    return str(uuid4())


class QualificationRulePack(Base):
    __tablename__ = "qualification_rule_packs"

    id = Column(String(36), primary_key=True, default=_uuid)
    code = Column(String(80), nullable=False)
    name = Column(String(200), nullable=False)
    standard_code = Column(String(80), nullable=False, index=True)
    edition = Column(String(30), nullable=False)
    version = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)
    input_schema = Column(JSONB, nullable=False, default=dict)
    output_schema = Column(JSONB, nullable=False, default=dict)
    rules = Column(JSONB, nullable=False, default=list)
    clause_references = Column(JSONB, nullable=False, default=list)
    compliance_metadata = Column(JSONB, nullable=False, default=dict)
    published_at = Column(DateTime)
    retired_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("code", "version", name="uq_qualification_rule_pack_version"),
        CheckConstraint(
            "status IN ('draft','review','published','retired')",
            name="ck_qualification_rule_pack_status",
        ),
        Index(
            "ix_qualification_rule_pack_standard_status",
            "standard_code",
            "edition",
            "status",
        ),
    )


class PQRQualificationResult(Base):
    __tablename__ = "pqr_qualification_results"

    id = Column(String(36), primary_key=True, default=_uuid)
    pqr_id = Column(Integer, ForeignKey("pqr.id", ondelete="CASCADE"), nullable=False)
    pqr_version_key = Column(String(100), nullable=False)
    pqr_snapshot_hash = Column(String(64), nullable=False)
    rule_pack_id = Column(
        String(36),
        ForeignKey("qualification_rule_packs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_pack_version = Column(String(40), nullable=False)
    calculation_key = Column(String(64), nullable=False, index=True)
    outcome = Column(String(30), nullable=False, index=True)
    input_snapshot = Column(JSONB, nullable=False, default=dict)
    result = Column(JSONB, nullable=False, default=dict)
    basis = Column(JSONB, nullable=False, default=list)
    missing_fields = Column(JSONB, nullable=False, default=list)
    boundary_conditions = Column(JSONB, nullable=False, default=list)
    requires_human_confirmation = Column(Boolean, nullable=False, default=False)
    supersedes_result_id = Column(
        String(36), ForeignKey("pqr_qualification_results.id", ondelete="SET NULL")
    )
    is_current = Column(Boolean, nullable=False, default=True, index=True)
    calculated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workspace_type = Column(String(20), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"))
    access_level = Column(String(20), nullable=False, default="private")

    __table_args__ = (
        CheckConstraint(
            "outcome IN ('qualified','not_qualified','needs_confirmation','insufficient_data')",
            name="ck_pqr_qualification_outcome",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_pqr_qualification_workspace",
        ),
        Index("ix_pqr_qualification_current", "pqr_id", "is_current"),
        Index(
            "ix_pqr_qualification_workspace",
            "workspace_type",
            "company_id",
            "user_id",
        ),
    )


class WPSPQRSupportLink(Base):
    __tablename__ = "wps_pqr_support_links"

    id = Column(String(36), primary_key=True, default=_uuid)
    wps_id = Column(Integer, ForeignKey("wps.id", ondelete="CASCADE"), nullable=False)
    pqr_id = Column(Integer, ForeignKey("pqr.id", ondelete="CASCADE"), nullable=False)
    qualification_result_id = Column(
        String(36),
        ForeignKey("pqr_qualification_results.id", ondelete="SET NULL"),
    )
    wps_version_key = Column(String(100), nullable=False)
    pqr_version_key = Column(String(100), nullable=False)
    wps_snapshot_hash = Column(String(64), nullable=False)
    pqr_snapshot_hash = Column(String(64), nullable=False)
    wps_snapshot = Column(JSONB, nullable=False, default=dict)
    pqr_snapshot = Column(JSONB, nullable=False, default=dict)
    supported_processes = Column(JSONB, nullable=False, default=list)
    qualified_scope = Column(JSONB, nullable=False, default=dict)
    source = Column(String(20), nullable=False, default="manual")
    confirmation_status = Column(String(20), nullable=False, default="pending")
    confirmation_note = Column(Text)
    confirmed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    confirmed_at = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workspace_type = Column(String(20), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"))
    access_level = Column(String(20), nullable=False, default="private")

    __table_args__ = (
        UniqueConstraint(
            "wps_id",
            "pqr_id",
            "wps_version_key",
            "pqr_version_key",
            name="uq_wps_pqr_support_version",
        ),
        CheckConstraint(
            "source IN ('manual','legacy','smart_import','rule_match')",
            name="ck_wps_pqr_support_source",
        ),
        CheckConstraint(
            "confirmation_status IN ('pending','confirmed','rejected')",
            name="ck_wps_pqr_support_confirmation",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_wps_pqr_support_workspace",
        ),
        Index("ix_wps_pqr_support_wps_active", "wps_id", "is_active"),
        Index("ix_wps_pqr_support_pqr_active", "pqr_id", "is_active"),
        Index(
            "ix_wps_pqr_support_workspace",
            "workspace_type",
            "company_id",
            "user_id",
        ),
    )

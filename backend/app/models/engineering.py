"""Engineering projects, immutable drawing revisions, and reviewed weld data."""
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


def _uuid() -> str:
    return str(uuid4())


class WorkspaceMixin:
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workspace_type = Column(String(20), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"))
    access_level = Column(String(20), nullable=False, default="private")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class EngineeringProject(WorkspaceMixin, Base):
    __tablename__ = "engineering_projects"
    id = Column(String(36), primary_key=True, default=_uuid)
    code = Column(String(80), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False, default="active")
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (
        CheckConstraint(
            "status IN ('active','archived')", name="ck_engineering_project_status"
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_project_workspace",
        ),
        UniqueConstraint(
            "workspace_type",
            "company_id",
            "user_id",
            "code",
            name="uq_engineering_project_code",
        ),
        Index(
            "ix_engineering_project_workspace",
            "workspace_type",
            "company_id",
            "user_id",
        ),
    )


class Product(WorkspaceMixin, Base):
    __tablename__ = "products"
    id = Column(String(36), primary_key=True, default=_uuid)
    project_id = Column(
        String(36),
        ForeignKey("engineering_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    code = Column(String(80), nullable=False)
    name = Column(String(200), nullable=False)
    product_type = Column(String(100))
    status = Column(String(20), nullable=False, default="draft")
    current_revision_number = Column(Integer)
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','active','archived')",
            name="ck_engineering_product_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_product_workspace",
        ),
        UniqueConstraint("project_id", "code", name="uq_engineering_product_code"),
        Index(
            "ix_engineering_product_workspace",
            "workspace_type",
            "company_id",
            "user_id",
        ),
    )


class ProductRevision(WorkspaceMixin, Base):
    __tablename__ = "product_revisions"
    id = Column(String(36), primary_key=True, default=_uuid)
    product_id = Column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    revision_number = Column(Integer, nullable=False)
    parent_revision_id = Column(
        String(36), ForeignKey("product_revisions.id", ondelete="SET NULL")
    )
    status = Column(String(20), nullable=False, default="draft")
    drawing_document_id = Column(
        String(36),
        ForeignKey("source_documents.id", ondelete="RESTRICT"),
        nullable=False,
    )
    drawing_sha256 = Column(String(64), nullable=False)
    drawing_filename = Column(String(255), nullable=False)
    drawing_page_count = Column(Integer, nullable=False, default=0)
    drawing_metadata = Column(JSONB, nullable=False, default=dict)
    data_version = Column(Integer, nullable=False, default=1)
    parse_status = Column(String(20), nullable=False, default="pending")
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    approved_at = Column(DateTime)
    change_summary = Column(Text)
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','review','approved','superseded')",
            name="ck_product_revision_status",
        ),
        CheckConstraint(
            "parse_status IN ('pending','processing','completed','failed')",
            name="ck_product_revision_parse_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_product_revision_workspace",
        ),
        UniqueConstraint(
            "product_id", "revision_number", name="uq_product_revision_number"
        ),
        Index(
            "ix_product_revision_workspace", "workspace_type", "company_id", "user_id"
        ),
    )


class Part(WorkspaceMixin, Base):
    __tablename__ = "parts"
    id = Column(String(36), primary_key=True, default=_uuid)
    revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_part_id = Column(String(36), ForeignKey("parts.id", ondelete="SET NULL"))
    part_number = Column(String(100))
    name = Column(String(200), nullable=False)
    material_spec = Column(String(200))
    material_group = Column(String(80))
    thickness_mm = Column(Float)
    quantity = Column(Integer, nullable=True)
    assembly_path = Column(String(500))
    evidence = Column(JSONB, nullable=False, default=dict)
    confidence = Column(Float)
    review_status = Column(String(20), nullable=False, default="pending")
    is_deleted = Column(Boolean, nullable=False, default=False)
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('pending','accepted','corrected')",
            name="ck_engineering_part_review",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_part_workspace",
        ),
        Index("ix_engineering_part_revision", "revision_id", "is_deleted"),
    )


class WeldJoint(WorkspaceMixin, Base):
    __tablename__ = "weld_joints"
    id = Column(String(36), primary_key=True, default=_uuid)
    revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    weld_number = Column(String(100), nullable=False)
    part_a_id = Column(String(36), ForeignKey("parts.id", ondelete="SET NULL"))
    part_b_id = Column(String(36), ForeignKey("parts.id", ondelete="SET NULL"))
    joint_type = Column(String(100))
    groove_type = Column(String(100))
    groove_angle = Column(Float)
    root_gap = Column(Float)
    root_face = Column(Float)
    weld_size = Column(Float)
    length_mm = Column(Float)
    weld_position = Column(String(80))
    evidence = Column(JSONB, nullable=False, default=dict)
    confidence = Column(Float)
    review_status = Column(String(20), nullable=False, default="pending")
    is_deleted = Column(Boolean, nullable=False, default=False)
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('pending','accepted','corrected')",
            name="ck_weld_joint_review",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_joint_workspace",
        ),
        Index("ix_weld_joint_revision", "revision_id", "is_deleted"),
    )


class WeldRequirement(WorkspaceMixin, Base):
    __tablename__ = "weld_requirements"
    id = Column(String(36), primary_key=True, default=_uuid)
    revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    weld_joint_id = Column(String(36), ForeignKey("weld_joints.id", ondelete="CASCADE"))
    welding_process = Column(String(100))
    material_group = Column(String(100))
    diameter_applicable = Column(Boolean)
    diameter_mm = Column(Float)
    filler_material_spec = Column(String(100))
    filler_material_classification = Column(String(100))
    nde_methods = Column(JSONB, nullable=False, default=list)
    nde_rate = Column(String(80))
    treatment_plan = Column(JSONB, nullable=True)
    pwht_required = Column(Boolean)
    pwht_temperature = Column(String(100))
    pwht_duration = Column(String(100))
    impact_required = Column(Boolean)
    impact_temperature = Column(String(100))
    special_requirements = Column(Text)
    evidence = Column(JSONB, nullable=False, default=dict)
    confidence = Column(Float)
    review_status = Column(String(20), nullable=False, default="pending")
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('pending','accepted','corrected')",
            name="ck_weld_requirement_review",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_weld_requirement_workspace",
        ),
        Index("ix_weld_requirement_revision", "revision_id", "weld_joint_id"),
    )


class DrawingParseRun(WorkspaceMixin, Base):
    __tablename__ = "drawing_parse_runs"
    id = Column(String(36), primary_key=True, default=_uuid)
    revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    extraction_job_id = Column(
        String(36), ForeignKey("extraction_jobs.id", ondelete="SET NULL")
    )
    provider = Column(String(80))
    model = Column(String(120))
    mode = Column(String(20), nullable=False, default="platform")
    status = Column(String(20), nullable=False, default="processing")
    schema_version = Column(String(30), nullable=False, default="pressure-vessel-v1")
    output_snapshot = Column(JSONB, nullable=False, default=dict)
    risks = Column(JSONB, nullable=False, default=list)
    error_message = Column(Text)
    finished_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing','completed','failed')",
            name="ck_drawing_parse_status",
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_drawing_parse_workspace",
        ),
        Index("ix_drawing_parse_revision", "revision_id", "created_at"),
    )


class EngineeringReviewRecord(WorkspaceMixin, Base):
    __tablename__ = "engineering_review_records"
    id = Column(String(36), primary_key=True, default=_uuid)
    revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(String(36))
    action = Column(String(30), nullable=False)
    previous_value = Column(JSONB, nullable=False, default=dict)
    new_value = Column(JSONB, nullable=False, default=dict)
    affected_joint_ids = Column(JSONB, nullable=False, default=list)
    reason = Column(Text)
    __table_args__ = (
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_review_workspace",
        ),
        Index("ix_engineering_review_revision", "revision_id", "created_at"),
    )


class EngineeringDependencyState(WorkspaceMixin, Base):
    __tablename__ = "engineering_dependency_states"
    id = Column(String(36), primary_key=True, default=_uuid)
    revision_id = Column(
        String(36),
        ForeignKey("product_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    dependency_type = Column(String(20), nullable=False)
    scope = Column(String(20), nullable=False, default="all")
    affected_joint_ids = Column(JSONB, nullable=False, default=list)
    status = Column(String(20), nullable=False, default="stale")
    source_data_version = Column(Integer, nullable=False)
    reason = Column(Text)
    invalidated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    __table_args__ = (
        CheckConstraint(
            "dependency_type IN ('matching','sequence','quota')",
            name="ck_engineering_dependency_type",
        ),
        CheckConstraint(
            "status IN ('fresh','stale')", name="ck_engineering_dependency_status"
        ),
        CheckConstraint(
            "workspace_type IN ('personal','enterprise')",
            name="ck_engineering_dependency_workspace",
        ),
        Index("ix_engineering_dependency_revision", "revision_id", "status"),
    )

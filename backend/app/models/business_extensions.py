"""Employee performance and custom report template models."""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.core.database import Base


class EmployeePerformance(Base):
    """员工绩效评估记录"""

    __tablename__ = "employee_performances"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_type = Column(String(20), nullable=False, default="personal", index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True)

    employee_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    employee_name = Column(String(100), nullable=False)
    department = Column(String(100))
    position = Column(String(100))
    review_period = Column(String(100), nullable=False, comment="考核周期，如 2026-Q1")
    period_start = Column(Date)
    period_end = Column(Date)

    overall_score = Column(Float, default=0)
    quality_score = Column(Float)
    efficiency_score = Column(Float)
    safety_score = Column(Float)
    teamwork_score = Column(Float)
    status = Column(String(50), default="draft", comment="draft/submitted/reviewed/finalized")

    goals = Column(Text, comment="目标(JSON或文本)")
    achievements = Column(Text, comment="业绩(JSON或文本)")
    areas_for_improvement = Column(Text)
    reviewer_comment = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ReportTemplate(Base):
    """自定义报表模板"""

    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_type = Column(String(20), nullable=False, default="personal", index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    data_sources = Column(Text, comment="数据源列表 JSON，如 [\"wps\",\"quality\"]")
    metrics = Column(Text, comment="指标配置 JSON")
    filters = Column(Text, comment="筛选配置 JSON")
    chart_type = Column(String(50), default="table", comment="table/bar/line/pie")
    time_range = Column(Text, comment="时间范围 JSON")
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

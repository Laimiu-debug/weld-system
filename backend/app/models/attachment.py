"""Private attachments always belong to an existing business record."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, BigInteger, Index
from app.core.database import Base


class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(String(100), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_type = Column(String(20), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    factory_id = Column(Integer, ForeignKey("factories.id"))
    resource_type = Column(String(40), nullable=False)
    resource_id = Column(Integer, nullable=False)
    filename = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (Index("ix_attachments_resource", "resource_type", "resource_id"),)

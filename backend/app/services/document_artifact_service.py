"""Retention rules and cleanup for smart-import document artifacts."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.smart_import import DocumentArtifact
from app.services.document_storage_service import DocumentStorage


def artifact_expiry(
    retention_class: str, now: datetime | None = None
) -> datetime | None:
    current = now or datetime.now(UTC).replace(tzinfo=None)
    if retention_class == "original":
        days = settings.DOCUMENT_RETENTION_ORIGINAL_DAYS
        return current + timedelta(days=days) if days > 0 else None
    if retention_class == "temporary":
        return current + timedelta(hours=settings.DOCUMENT_RETENTION_TEMPORARY_HOURS)
    if retention_class == "evidence":
        return current + timedelta(days=settings.DOCUMENT_RETENTION_EVIDENCE_DAYS)
    if retention_class == "export":
        return current + timedelta(days=settings.DOCUMENT_RETENTION_EXPORT_DAYS)
    raise ValueError(f"不支持的产物保留类型: {retention_class}")


class DocumentArtifactRetentionService:
    def __init__(self, db: Session, storage: DocumentStorage):
        self.db = db
        self.storage = storage

    def purge_expired(self, now: datetime | None = None, batch_size: int = 200) -> int:
        current = now or datetime.now(UTC).replace(tzinfo=None)
        artifacts = (
            self.db.query(DocumentArtifact)
            .filter(
                DocumentArtifact.status == "active",
                DocumentArtifact.expires_at.isnot(None),
                DocumentArtifact.expires_at <= current,
            )
            .order_by(DocumentArtifact.expires_at, DocumentArtifact.id)
            .limit(max(1, min(batch_size, 1000)))
            .all()
        )
        purged = 0
        for artifact in artifacts:
            if artifact.storage_key:
                self.storage.delete(artifact.storage_key)
            artifact.status = "deleted"
            artifact.storage_key = None
            artifact.metadata_json = {
                **(artifact.metadata_json or {}),
                "deleted_at": current.isoformat(),
                "deletion_reason": "retention_expired",
            }
            purged += 1
        self.db.commit()
        return purged

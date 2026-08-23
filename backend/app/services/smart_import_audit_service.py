"""Security audit events for sensitive documents and external AI disclosure."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.data_access import WorkspaceContext
from app.models.system_log import SystemLog


class SmartImportAuditService:
    def __init__(self, db: Session):
        self.db = db

    def record_file_access(
        self,
        action: str,
        document: Any,
        user_id: int,
        context: WorkspaceContext,
    ) -> None:
        self.db.add(
            SystemLog(
                log_level="info",
                log_type="security",
                message=f"smart_import.file.{action}",
                user_id=user_id,
                details={
                    "event": "sensitive_file_access",
                    "action": action,
                    "document_id": document.id,
                    "batch_id": document.batch_id,
                    "document_type": document.document_type,
                    "workspace_type": str(context.workspace_type),
                    "company_id": context.company_id,
                    "factory_id": context.factory_id,
                    "sha256": document.sha256,
                },
            )
        )

    def record_ai_disclosure(
        self,
        *,
        job_id: str,
        document_id: str,
        user_id: int,
        provider: str,
        model: str,
        phase: str,
        page_numbers: list[int],
        workspace_type: str,
        company_id: int | None,
    ) -> None:
        self.db.add(
            SystemLog(
                log_level="info",
                log_type="security",
                message="smart_import.ai.disclosure",
                user_id=user_id,
                details={
                    "event": "ai_external_disclosure",
                    "job_id": job_id,
                    "document_id": document_id,
                    "provider": provider,
                    "model": model,
                    "phase": phase,
                    "page_numbers": page_numbers,
                    "workspace_type": workspace_type,
                    "company_id": company_id,
                    "contains_document_text": True,
                    "contains_api_key": False,
                },
            )
        )

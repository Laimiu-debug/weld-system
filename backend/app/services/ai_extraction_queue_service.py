"""Persistent lifecycle management for queued smart-import extraction jobs."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.data_access import WorkspaceContext
from app.models.smart_import import ExtractionJob
from app.models.user import User
from app.services.smart_import_service import SmartImportService


ACTIVE_JOB_STATUSES = ("queued", "processing")


class AIExtractionQueueService:
    def __init__(self, db: Session):
        self.db = db
        self.smart_import = SmartImportService(db)

    def get_job(
        self, job_id: str, user: User, context: WorkspaceContext
    ) -> ExtractionJob:
        job = (
            self.smart_import._scope_query(
                self.db.query(ExtractionJob), ExtractionJob, user, context
            )
            .filter(ExtractionJob.id == job_id)
            .first()
        )
        if not job:
            raise HTTPException(status_code=404, detail="提取任务不存在或无权访问")
        return job

    def list_document_jobs(
        self, document_id: str, user: User, context: WorkspaceContext
    ) -> list[ExtractionJob]:
        self.smart_import.get_document(document_id, user, context)
        return (
            self.smart_import._scope_query(
                self.db.query(ExtractionJob), ExtractionJob, user, context
            )
            .filter(ExtractionJob.document_id == document_id)
            .order_by(ExtractionJob.created_at.desc())
            .all()
        )

    def create_job(
        self,
        *,
        document_id: str,
        schema_snapshot: dict,
        template_id: str | None,
        mode: str,
        provider: str,
        model: str,
        provider_config_id: str | None,
        run_ocr: bool,
        user: User,
        context: WorkspaceContext,
        retry_of_job_id: str | None = None,
    ) -> ExtractionJob:
        document = self.smart_import.get_document(document_id, user, context)
        if document.status not in {"ready", "failed"}:
            raise HTTPException(status_code=422, detail="请先完成文档分页解析")
        duplicate = (
            self.smart_import._scope_query(
                self.db.query(ExtractionJob), ExtractionJob, user, context
            )
            .filter(
                ExtractionJob.document_id == document_id,
                ExtractionJob.status.in_(ACTIVE_JOB_STATUSES),
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="该文件已有正在执行的提取任务")
        active = self.smart_import._scope_query(
            self.db.query(ExtractionJob), ExtractionJob, user, context
        ).filter(ExtractionJob.status.in_(ACTIVE_JOB_STATUSES))
        if active.count() >= settings.AI_MAX_CONCURRENT_TASKS:
            raise HTTPException(
                status_code=429,
                detail=f"当前工作区最多同时运行 {settings.AI_MAX_CONCURRENT_TASKS} 个 AI 任务",
            )
        job = ExtractionJob(
            id=str(uuid4()),
            document_id=document.id,
            template_id=template_id,
            mode=mode,
            provider=provider,
            model=model,
            provider_config_id=provider_config_id,
            retry_of_job_id=retry_of_job_id,
            run_ocr=run_ocr,
            progress=0,
            schema_version=str(schema_snapshot.get("schema_version") or "1.0"),
            schema_snapshot=schema_snapshot,
            prompt_version="smart-import-v1",
            request_trace_id=str(uuid4()),
            status="queued",
            attempt_count=0,
            user_id=document.user_id,
            workspace_type=document.workspace_type,
            company_id=document.company_id,
            factory_id=document.factory_id,
            access_level=document.access_level,
        )
        batch = self.smart_import.get_batch(document.batch_id, user, context)
        batch.status = "queued"
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def retry_job(
        self, source: ExtractionJob, user: User, context: WorkspaceContext
    ) -> ExtractionJob:
        if source.status not in {"failed", "cancelled"}:
            raise HTTPException(status_code=409, detail="只有失败或已取消任务可以重试")
        return self.create_job(
            document_id=source.document_id,
            schema_snapshot=source.schema_snapshot,
            template_id=source.template_id,
            mode=source.mode,
            provider=source.provider,
            model=source.model,
            provider_config_id=source.provider_config_id,
            run_ocr=source.run_ocr,
            user=user,
            context=context,
            retry_of_job_id=source.id,
        )

    def cancel_job(self, job: ExtractionJob) -> ExtractionJob:
        if job.status in {"completed", "failed", "cancelled"}:
            raise HTTPException(status_code=409, detail="当前任务状态不能取消")
        job.status = "cancelled"
        job.error_code = "task_cancelled"
        job.error_message = "任务已由用户取消"
        job.completed_at = datetime.now(UTC).replace(tzinfo=None)
        self.db.commit()
        self.db.refresh(job)
        return job

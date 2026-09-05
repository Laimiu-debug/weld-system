"""Persistent lifecycle management for queued smart-import extraction jobs."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.data_access import WorkspaceContext
from app.models.smart_import import (
    ExtractedEntity,
    ExtractionJob,
    ImportBatch,
    SourceDocument,
)
from app.models.user import User
from app.services.smart_import_service import SmartImportService
from app.services.ai_quota_service import AIQuotaError, AIQuotaService


ACTIVE_JOB_STATUSES = ("queued", "processing")


class AIExtractionQueueService:
    def __init__(self, db: Session, quota_service: AIQuotaService | None = None):
        self.db = db
        self.smart_import = SmartImportService(db)
        self.quota = quota_service or AIQuotaService(db)

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

    def refresh_batch(self, batch: ImportBatch) -> ImportBatch:
        documents = (
            self.db.query(SourceDocument)
            .filter(SourceDocument.batch_id == batch.id)
            .all()
        )
        if not documents:
            return batch
        document_ids = [item.id for item in documents]
        jobs = (
            self.db.query(ExtractionJob)
            .filter(ExtractionJob.document_id.in_(document_ids))
            .order_by(ExtractionJob.created_at.desc())
            .all()
        )
        latest: dict[str, ExtractionJob] = {}
        for job in jobs:
            if (job.schema_snapshot or {}).get("job_kind") == "parse":
                continue
            latest.setdefault(job.document_id, job)
        entities = (
            self.db.query(ExtractedEntity)
            .filter(
                ExtractedEntity.document_id.in_(document_ids),
                ExtractedEntity.is_current.is_(True),
            )
            .all()
        )
        published = sum(item.status == "published" for item in entities)
        selected = list(latest.values())
        completed = sum(item.status == "completed" for item in selected)
        failed = sum(item.status in {"failed", "cancelled"} for item in selected)
        batch.progress = int(
            sum(item.progress or 0 for item in selected) / max(len(documents), 1)
        )
        if published == len(documents):
            batch.status = "completed"
            batch.progress = 100
        elif any(item.status == "processing" for item in selected):
            batch.status = "processing"
        elif any(item.status == "queued" for item in selected):
            batch.status = "queued"
        elif completed and failed:
            batch.status = "partial_success"
        elif completed == len(documents):
            batch.status = "review"
            batch.progress = 100
        elif failed == len(documents):
            batch.status = "failed"
        self.db.commit()
        self.db.refresh(batch)
        return batch

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
        if mode != "offline":
            try:
                self.quota.enforce_task_limits(
                    user,
                    context,
                    len(((schema_snapshot or {}).get("drawing_options") or {}).get("page_numbers") or []) or max(1, int(getattr(document, "page_count", 0) or 0)),
                    float(
                        ((schema_snapshot or {}).get("x-weld-routing") or {}).get(
                            "point_multiplier", 1
                        )
                    ),
                )
            except AIQuotaError as exc:
                raise HTTPException(
                    status_code=exc.status_code, detail=str(exc)
                ) from exc
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
        queued = self.smart_import._scope_query(
            self.db.query(ExtractionJob), ExtractionJob, user, context
        ).filter(ExtractionJob.status == "queued")
        if queued.count() >= settings.AI_MAX_QUEUED_TASKS:
            raise HTTPException(
                status_code=429,
                detail=f"当前工作区最多排队 {settings.AI_MAX_QUEUED_TASKS} 个 AI 任务",
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
            progress_detail={
                "job_kind": "extraction",
                "phase": "queued",
                "pages": {"completed": 0, "total": int(document.page_count or 0)},
                "fields": {
                    "completed": 0,
                    "total": sum(
                        1
                        for item in schema_snapshot.get("field_bindings", [])
                        if item.get("extractable")
                    ),
                },
            },
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

    def create_parse_job(
        self,
        document_id: str,
        user: User,
        context: WorkspaceContext,
        *,
        retry_of_job_id: str | None = None,
    ) -> ExtractionJob:
        """Create a non-AI Celery job for private document pagination."""
        document = self.smart_import.get_document(document_id, user, context)
        if document.status == "parsing":
            raise HTTPException(status_code=409, detail="文档正在解析，请勿重复提交")
        duplicate = (
            self.smart_import._scope_query(
                self.db.query(ExtractionJob), ExtractionJob, user, context
            )
            .filter(
                ExtractionJob.document_id == document.id,
                ExtractionJob.status.in_(ACTIVE_JOB_STATUSES),
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="该文件已有正在执行的后台任务")
        job = ExtractionJob(
            id=str(uuid4()),
            document_id=document.id,
            mode="offline",
            retry_of_job_id=retry_of_job_id,
            run_ocr=False,
            progress=0,
            progress_detail={
                "job_kind": "parse",
                "phase": "queued",
                "pages": {"completed": 0, "total": 0},
                "fields": {"completed": 0, "total": 0},
            },
            schema_version="parse-v1",
            schema_snapshot={"schema_version": "parse-v1", "job_kind": "parse"},
            prompt_version=None,
            request_trace_id=str(uuid4()),
            status="queued",
            attempt_count=0,
            user_id=document.user_id,
            workspace_type=document.workspace_type,
            company_id=document.company_id,
            factory_id=document.factory_id,
            access_level=document.access_level,
        )
        document.metadata_json = {
            **(document.metadata_json or {}),
            "parsing": {"status": "queued", "job_id": job.id},
        }
        batch = self.smart_import.get_batch(document.batch_id, user, context)
        batch.status = "queued"
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def retry_job(
        self, source: ExtractionJob, user: User, context: WorkspaceContext
    ) -> ExtractionJob:
        if (source.schema_snapshot or {}).get("job_kind") == "drawing":
            raise HTTPException(409, "请在图纸审核页重新选择模型并重试识别")
        if source.status not in {"failed", "cancelled"}:
            raise HTTPException(status_code=409, detail="只有失败或已取消任务可以重试")
        return self.create_job(
            document_id=source.document_id,
            schema_snapshot={**source.schema_snapshot, "actor_user_id": user.id},
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
        self.db.refresh(job, with_for_update=True)
        if job.status in {"completed", "failed", "cancelled"}:
            raise HTTPException(status_code=409, detail="当前任务状态不能取消")
        if (job.schema_snapshot or {}).get("job_kind") == "drawing":
            from app.models.engineering import ProductRevision
            revision = self.db.query(ProductRevision).filter(ProductRevision.id == job.schema_snapshot["drawing_revision_id"]).populate_existing().with_for_update().first()
            if revision:
                revision.parse_status = "failed"
        job.status = "cancelled"
        job.error_code = "task_cancelled"
        job.error_message = "任务已由用户取消"
        job.progress_detail = {**(job.progress_detail or {}), "phase": "cancelled"}
        job.completed_at = datetime.now(UTC).replace(tzinfo=None)
        self.db.commit()
        self.db.refresh(job)
        return job

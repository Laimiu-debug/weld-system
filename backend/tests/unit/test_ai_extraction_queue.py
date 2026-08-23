from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.core.data_access import WorkspaceContext, WorkspaceType
from app.models.smart_import import ExtractionJob
from app.services.ai_extraction_queue_service import AIExtractionQueueService


def test_cancel_job_persists_terminal_state() -> None:
    db = Mock()
    job = ExtractionJob(id="job-1", status="queued", progress=0)
    service = AIExtractionQueueService(db)

    result = service.cancel_job(job)

    assert result.status == "cancelled"
    assert result.error_code == "task_cancelled"
    assert result.completed_at is not None
    db.commit.assert_called_once()


def test_completed_job_cannot_be_cancelled() -> None:
    service = AIExtractionQueueService(Mock())
    with pytest.raises(HTTPException) as exc:
        service.cancel_job(ExtractionJob(id="job-1", status="completed"))
    assert exc.value.status_code == 409


def test_retry_creates_new_job_with_source_link() -> None:
    service = AIExtractionQueueService(Mock())
    service.create_job = Mock(return_value=SimpleNamespace(id="job-2"))
    source = ExtractionJob(
        id="job-1",
        document_id="document-1",
        status="failed",
        schema_snapshot={"schema_version": "1.0"},
        mode="platform",
        provider="openai_responses",
        model="model-1",
        run_ocr=True,
    )
    user = SimpleNamespace(id=7)
    context = WorkspaceContext(7, WorkspaceType.PERSONAL)

    result = service.retry_job(source, user, context)

    assert result.id == "job-2"
    assert service.create_job.call_args.kwargs["retry_of_job_id"] == "job-1"
    assert service.create_job.call_args.kwargs["document_id"] == "document-1"

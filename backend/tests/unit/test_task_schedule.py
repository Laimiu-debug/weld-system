"""Celery registration and schedule smoke tests."""

import pytest

pytest.importorskip("celery")

from app.tasks.celery_app import celery_app
from app.tasks.notification_tasks import (
    run_daily_notification_tasks,
    run_hourly_notification_tasks,
)
from app.tasks.smart_import_tasks import (
    run_smart_import_extraction,
    run_smart_import_parse,
)
from app.tasks.document_tasks import purge_expired_document_artifacts
from app.tasks.operations_tasks import detect_operations_alerts


def test_notification_tasks_are_registered() -> None:
    assert run_daily_notification_tasks.name == "notifications.daily"
    assert run_hourly_notification_tasks.name == "notifications.hourly"
    assert run_smart_import_extraction.name == "smart_import.extract"
    assert run_smart_import_parse.name == "smart_import.parse"
    assert purge_expired_document_artifacts.name == "documents.purge_expired_artifacts"
    assert detect_operations_alerts.name == "operations.detect_alerts"


def test_notification_schedule_contains_daily_and_hourly_jobs() -> None:
    schedule = celery_app.conf.beat_schedule
    assert schedule["daily-notifications-at-08-00"]["task"] == "notifications.daily"
    assert schedule["hourly-notifications"]["task"] == "notifications.hourly"
    assert (
        schedule["daily-document-retention-cleanup"]["task"]
        == "documents.purge_expired_artifacts"
    )
    assert celery_app.conf.worker_concurrency >= 1
    assert schedule["hourly-operations-alerts"]["task"] == "operations.detect_alerts"

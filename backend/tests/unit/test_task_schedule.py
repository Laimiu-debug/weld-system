"""Celery registration and schedule smoke tests."""

import pytest

pytest.importorskip("celery")

from app.tasks.celery_app import celery_app
from app.tasks.notification_tasks import (
    run_daily_notification_tasks,
    run_hourly_notification_tasks,
)
from app.tasks.smart_import_tasks import run_smart_import_extraction


def test_notification_tasks_are_registered() -> None:
    assert run_daily_notification_tasks.name == "notifications.daily"
    assert run_hourly_notification_tasks.name == "notifications.hourly"
    assert run_smart_import_extraction.name == "smart_import.extract"


def test_notification_schedule_contains_daily_and_hourly_jobs() -> None:
    schedule = celery_app.conf.beat_schedule
    assert schedule["daily-notifications-at-08-00"]["task"] == "notifications.daily"
    assert schedule["hourly-notifications"]["task"] == "notifications.hourly"
    assert celery_app.conf.worker_concurrency >= 1

"""Celery application and production notification schedule."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


def _broker_url(configured: str) -> str:
    if configured == "redis://localhost:6379/0":
        return settings.REDIS_URL
    return configured


celery_app = Celery(
    "weldsystem",
    broker=_broker_url(settings.CELERY_BROKER_URL),
    backend=_broker_url(settings.CELERY_RESULT_BACKEND),
    include=["app.tasks.notification_tasks"],
)

celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer="json",
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "daily-notifications-at-08-00": {
            "task": "notifications.daily",
            "schedule": crontab(hour=8, minute=0),
        },
        "hourly-notifications": {
            "task": "notifications.hourly",
            "schedule": crontab(minute=0),
        },
    },
)

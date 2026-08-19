"""Liveness and readiness probes. Readiness must not always return healthy."""
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, redis_client
from app.core.observability import pool_snapshot


def liveness() -> dict[str, Any]:
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEVELOPMENT else "production",
    }


def _postgres_ok() -> tuple[bool, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "ok"
    except Exception:
        return False, "unreachable"


def _redis_ok() -> tuple[bool, str]:
    try:
        redis_client.ping()
        return True, "ok"
    except Exception:
        return False, "unreachable"


def _alembic_revision() -> str | None:
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
            return str(row[0]) if row else None
    except Exception:
        return None


def readiness() -> dict[str, Any]:
    postgres_ok, postgres_detail = _postgres_ok()
    redis_ok, redis_detail = _redis_ok()
    ready = postgres_ok and redis_ok
    return {
        "status": "ready" if ready else "not_ready",
        "checks": {
            "postgres": {"ok": postgres_ok, "detail": postgres_detail},
            "redis": {"ok": redis_ok, "detail": redis_detail},
            "alembic_revision": _alembic_revision(),
            "db_pool": pool_snapshot(),
        },
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


def assert_ready_or_raise() -> None:
    """Used at startup in production: refuse to serve if dependencies are down."""
    report = readiness()
    if report["status"] != "ready" and not settings.DEVELOPMENT:
        raise RuntimeError("Readiness checks failed; refusing to start in production")

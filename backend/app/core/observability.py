"""Request ID, structured access logs, and database pool snapshots."""
from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.database import engine

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return request_id_var.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        for key in ("method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    if settings.DEVELOPMENT:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
        )
    else:
        handler.setFormatter(JsonLogFormatter())
    root.handlers = [handler]


def pool_snapshot() -> dict[str, Any]:
    pool = getattr(engine, "pool", None)
    if pool is None:
        return {"ok": False, "detail": "no_pool"}
    try:
        return {
            "ok": True,
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
    except Exception:
        return {"ok": False, "detail": "unavailable"}


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        logger = logging.getLogger("app.http")
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(duration_ms)
            logger.info(
                "http_request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            return response
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            logger.exception(
                "http_error",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise
        finally:
            request_id_var.reset(token)

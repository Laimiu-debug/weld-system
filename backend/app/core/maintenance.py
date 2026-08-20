"""Maintenance mode gate for non-admin user APIs."""
from __future__ import annotations

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.system_config_service import is_maintenance_mode


_ALLOW_PREFIXES = (
    "/health",
    "/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
)

_ALLOW_API_PREFIXES = (
    "/api/v1/health",
    "/api/v1/admin",
    "/api/v1/system/branding",
    "/api/v1/system/public-config",
)


def _is_allowed(path: str) -> bool:
    if path in _ALLOW_PREFIXES:
        return True
    for prefix in _ALLOW_PREFIXES:
        if path.startswith(prefix + "/"):
            return True
    for prefix in _ALLOW_API_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path or "/"
        if _is_allowed(path):
            return await call_next(request)

        if not is_maintenance_mode():
            return await call_next(request)

        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "detail": "系统维护中，暂时无法访问，请稍后再试",
                "code": "maintenance_mode",
            },
        )

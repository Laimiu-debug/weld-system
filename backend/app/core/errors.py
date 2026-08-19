"""Stable API errors, redaction, and FastAPI exception handlers."""
import logging
import re
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

SENSITIVE_PATTERN = re.compile(
    r"(password|passwd|token|secret|authorization|api[_-]?key|verify(?:ication)?[_-]?code|"
    r"otp|csrf|cookie|session|id_card|idcard|phone|mobile|email|card_no|bank)",
    re.IGNORECASE,
)


def error_body(code: str, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    payload.update(extra)
    return {"detail": payload}


def not_implemented(feature: str) -> None:
    """Raise 501 for unfinished capabilities. Never fake a success payload."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"code": "NOT_IMPLEMENTED", "message": f"{feature}尚未开放"},
    )


def redact_value(value: str, max_len: int = 200) -> str:
    text = value if len(value) <= max_len else value[:max_len] + "..."
    if SENSITIVE_PATTERN.search(text):
        return "[redacted]"
    return text


def redact_headers(headers: Any) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in headers.items():
        if SENSITIVE_PATTERN.search(str(key)):
            redacted[key] = "[redacted]"
        else:
            redacted[key] = redact_value(str(value), max_len=80)
    return redacted


def client_error_detail(exc: BaseException) -> str:
    """Never put raw exception text in API responses."""
    del exc
    return "服务器内部错误"


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_body(
            "VALIDATION_ERROR",
            "请求参数无效",
            errors=exc.errors(),
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled error on %s %s headers=%s",
        request.method,
        request.url.path,
        redact_headers(request.headers),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_body("INTERNAL_ERROR", client_error_detail(exc)),
    )


def register_exception_handlers(app: Any) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

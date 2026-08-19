"""IP/account rate limiting with Redis, in-memory fallback for tests."""
import threading
import time
from collections import defaultdict
from typing import DefaultDict

from fastapi import HTTPException, Request, status

from app.core.database import redis_client

_lock = threading.Lock()
_hits: DefaultDict[str, list[float]] = defaultdict(list)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def enforce_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    if _redis_limit(key, limit, window_seconds):
        return
    _memory_limit(key, limit, window_seconds)


def _redis_limit(key: str, limit: int, window_seconds: int) -> bool:
    try:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, window_seconds)
        if int(count) > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMITED", "message": "请求过于频繁，请稍后再试"},
            )
        return True
    except HTTPException:
        raise
    except Exception:
        return False


def _memory_limit(key: str, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    with _lock:
        window = [ts for ts in _hits[key] if now - ts < window_seconds]
        if len(window) >= limit:
            _hits[key] = window
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMITED", "message": "请求过于频繁，请稍后再试"},
            )
        window.append(now)
        _hits[key] = window

"""Persist non-secret routing identity; never silently switch a queued recipient."""
from fastapi import HTTPException
import hashlib
import json


def route_fingerprint(config) -> str:
    values = {
        key: (
            config.get(key) if isinstance(config, dict) else getattr(config, key, None)
        )
        for key in ("id", "provider", "base_url", "model")
    }
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def require_expected_route(expected: str | None, config) -> None:
    if expected and expected != route_fingerprint(config):
        raise HTTPException(409, "模型配置已变更，请刷新接收方信息后重新授权提交")


def routing_snapshot(config, task_type: str, complexity: str) -> dict:
    return {
        "config_id": getattr(config, "id", None),
        "task_type": task_type,
        "complexity": complexity,
        "point_multiplier": float(getattr(config, "point_multiplier", 1) or 1),
        "provider": config.provider,
        "base_url": config.base_url.rstrip("/"),
        "model": config.model,
    }


def validate_routing_snapshot(snapshot: dict, config) -> None:
    for field in ("provider", "base_url", "model"):
        expected = snapshot.get(field)
        actual = getattr(config, field, None)
        if field == "base_url" and actual:
            actual = actual.rstrip("/")
        if expected is not None and expected != actual:
            raise HTTPException(409, "任务的模型或接收地址已变更，请重新选择并授权后提交")

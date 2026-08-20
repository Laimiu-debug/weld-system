"""
Runtime system config for admin portal controls.
Env defaults + JSON override under uploads/.system (same pattern as branding).
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()

CONFIG_KEYS = (
    "maintenance_mode",
    "registration_enabled",
    "max_upload_size_mb",
    "session_timeout_minutes",
)


def _config_path() -> Path:
    return Path(settings.UPLOAD_DIR).resolve() / ".system" / "system_config.json"


def _defaults() -> Dict[str, Any]:
    return {
        "maintenance_mode": False,
        "registration_enabled": True,
        "max_upload_size_mb": max(1, int(getattr(settings, "MAX_FILE_SIZE", 10 * 1024 * 1024) / (1024 * 1024)) or 100),
        "session_timeout_minutes": int(settings.ACCESS_TOKEN_EXPIRE_MINUTES or 30),
    }


def _read_overrides() -> Dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        out: Dict[str, Any] = {}
        for key in CONFIG_KEYS:
            if key not in raw:
                continue
            value = raw[key]
            if key in ("maintenance_mode", "registration_enabled"):
                out[key] = bool(value)
            elif key in ("max_upload_size_mb", "session_timeout_minutes"):
                try:
                    out[key] = int(value)
                except (TypeError, ValueError):
                    continue
            else:
                out[key] = value
        return out
    except Exception as exc:
        logger.warning("读取系统配置失败 %s: %s", path, exc)
        return {}


def get_system_runtime_config() -> Dict[str, Any]:
    """合并默认值与文件覆盖."""
    merged = _defaults()
    overrides = _read_overrides()
    merged.update(overrides)
    # 边界校正
    merged["max_upload_size_mb"] = max(1, min(1024, int(merged["max_upload_size_mb"])))
    merged["session_timeout_minutes"] = max(5, min(1440, int(merged["session_timeout_minutes"])))
    return merged


def update_system_runtime_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """写入覆盖层；只更新已知字段."""
    with _lock:
        current = _read_overrides()
        for key in CONFIG_KEYS:
            if key not in data or data[key] is None:
                continue
            value = data[key]
            if key in ("maintenance_mode", "registration_enabled"):
                current[key] = bool(value)
            elif key == "max_upload_size_mb":
                current[key] = max(1, min(1024, int(value)))
            elif key == "session_timeout_minutes":
                current[key] = max(5, min(1440, int(value)))
        path = _config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return get_system_runtime_config()


def is_maintenance_mode() -> bool:
    return bool(get_system_runtime_config().get("maintenance_mode"))


def is_registration_enabled() -> bool:
    return bool(get_system_runtime_config().get("registration_enabled", True))


def get_access_token_expire_minutes() -> int:
    return int(get_system_runtime_config()["session_timeout_minutes"])


def get_max_upload_bytes() -> int:
    mb = int(get_system_runtime_config()["max_upload_size_mb"])
    return mb * 1024 * 1024


def get_public_system_config() -> Dict[str, Any]:
    cfg = get_system_runtime_config()
    return {
        "maintenance_mode": cfg["maintenance_mode"],
        "registration_enabled": cfg["registration_enabled"],
    }

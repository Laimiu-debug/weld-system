"""
Branding / org display name for private enterprise deployments.
Env defaults + optional JSON override file for admin UI edits.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings

logger = logging.getLogger(__name__)

BRANDING_KEYS = ("brand_name", "brand_subtitle", "org_name")


def _valid_display_text(value: str) -> bool:
    """Reject legacy values damaged by a non-UTF-8 deployment shell."""
    stripped = value.strip()
    return bool(stripped) and any(char not in {"?", "？", "�"} for char in stripped)


def _config_path() -> Path:
    """优先显式路径；默认写到 uploads/.system，随现有上传卷持久化."""
    configured = (settings.BRANDING_CONFIG_PATH or "").strip()
    # 默认路径占位时改走 uploads 下，避免无卷挂载丢失
    if configured and configured not in (
        "./storage/config/branding.json",
        "storage/config/branding.json",
    ):
        return Path(configured)
    return Path(settings.UPLOAD_DIR).resolve() / ".system" / "branding.json"


def _env_defaults() -> Dict[str, str]:
    brand_name = (settings.BRAND_NAME or "焊序").strip() or "焊序"
    brand_subtitle = (settings.BRAND_SUBTITLE or "Hanxu").strip() or "Hanxu"
    return {
        "brand_name": brand_name if _valid_display_text(brand_name) else "焊序",
        "brand_subtitle": brand_subtitle
        if _valid_display_text(brand_subtitle)
        else "Hanxu",
        "org_name": (settings.ORG_NAME or "").strip(),
    }


def _read_file_overrides() -> Dict[str, str]:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        out: Dict[str, str] = {}
        for key in BRANDING_KEYS:
            if key in raw and raw[key] is not None:
                out[key] = str(raw[key]).strip()
        return out
    except Exception as exc:
        logger.warning("读取品牌配置失败 %s: %s", path, exc)
        return {}


def get_branding() -> Dict[str, str]:
    """合并 env 默认值与文件覆盖；公开接口与侧栏共用."""
    merged = _env_defaults()
    overrides = _read_file_overrides()
    for key, value in overrides.items():
        if key in BRANDING_KEYS:
            if key == "org_name" or _valid_display_text(value):
                merged[key] = value
    # 副标题：有企业名时优先展示企业名
    display_subtitle = merged["org_name"] or merged["brand_subtitle"]
    collapsed = merged["brand_name"][:2] if merged["brand_name"] else "焊序"
    return {
        "brand_name": merged["brand_name"],
        "brand_subtitle": merged["brand_subtitle"],
        "org_name": merged["org_name"],
        "display_subtitle": display_subtitle,
        "collapsed_label": collapsed,
    }


def update_branding(data: Dict[str, Any]) -> Dict[str, str]:
    """写入文件覆盖层（不改 env）；仅更新传入字段."""
    current = _read_file_overrides()
    for key in BRANDING_KEYS:
        if key in data and data[key] is not None:
            current[key] = str(data[key]).strip()

    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(current, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return get_branding()

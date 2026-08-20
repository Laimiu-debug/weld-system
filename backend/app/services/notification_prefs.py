"""
User notification preference helpers.

Preferences are stored in users.preferences JSON and drive both
in-app delivery and outbound email/SMS filtering.
"""
from __future__ import annotations

import json
from datetime import datetime, time
from typing import Any, Dict, Optional

from app.models.user import User
from app.schemas.user import UserPreferences

# Logical notification categories → preference field names
CATEGORY_PREF_KEYS = {
    "system_updates": "systemUpdates",
    "security_alerts": "securityAlerts",
    "maintenance": "maintenance",
    "wps_updates": "wpsUpdates",
    "pqr_approvals": "pqrApprovals",
    "quality_alerts": "qualityAlerts",
    "equipment_maintenance": "equipmentMaintenance",
    "material_alerts": "materialAlerts",
    "welder_certifications": "welderCertifications",
    "production_deadlines": "productionDeadlines",
    "membership": "systemUpdates",
}


def default_notification_prefs() -> Dict[str, Any]:
    prefs = UserPreferences()
    return {
        "emailNotifications": prefs.emailNotifications,
        "pushNotifications": prefs.pushNotifications,
        "smsNotifications": prefs.smsNotifications,
        "desktopNotifications": prefs.desktopNotifications,
        "notificationSound": prefs.notificationSound,
        "quietHoursEnabled": prefs.quietHoursEnabled,
        "quietHoursStart": prefs.quietHoursStart,
        "quietHoursEnd": prefs.quietHoursEnd,
        "systemUpdates": prefs.systemUpdates,
        "securityAlerts": prefs.securityAlerts,
        "maintenance": prefs.maintenance,
        "wpsUpdates": prefs.wpsUpdates,
        "pqrApprovals": prefs.pqrApprovals,
        "qualityAlerts": prefs.qualityAlerts,
        "equipmentMaintenance": prefs.equipmentMaintenance,
        "materialAlerts": prefs.materialAlerts,
        "welderCertifications": prefs.welderCertifications,
        "productionDeadlines": prefs.productionDeadlines,
        "emailDigestFrequency": prefs.emailDigestFrequency,
        "loginNotifications": prefs.loginNotifications,
    }


def parse_user_prefs(user: Optional[User]) -> Dict[str, Any]:
    prefs = default_notification_prefs()
    if not user:
        return prefs
    raw = getattr(user, "preferences", None)
    data: Any = None
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            data = None
    if isinstance(data, dict):
        prefs.update({k: data[k] for k in prefs.keys() if k in data})
    return prefs


def _parse_hhmm(value: str, fallback: time) -> time:
    try:
        hour, minute = (value or "").split(":")
        return time(hour=int(hour), minute=int(minute))
    except Exception:
        return fallback


def in_quiet_hours(prefs: Dict[str, Any], now: Optional[datetime] = None) -> bool:
    if not prefs.get("quietHoursEnabled"):
        return False
    now = now or datetime.utcnow()
    start = _parse_hhmm(str(prefs.get("quietHoursStart") or "22:00"), time(22, 0))
    end = _parse_hhmm(str(prefs.get("quietHoursEnd") or "08:00"), time(8, 0))
    current = now.time().replace(second=0, microsecond=0)
    if start <= end:
        return start <= current < end
    # Overnight window, e.g. 22:00 → 08:00
    return current >= start or current < end


def category_enabled(prefs: Dict[str, Any], category: str) -> bool:
    key = CATEGORY_PREF_KEYS.get(category)
    if not key:
        return True
    return bool(prefs.get(key, True))


def is_urgent(priority: str) -> bool:
    return (priority or "").lower() in {"urgent", "high"}


def should_create_in_app(prefs: Dict[str, Any], category: str) -> bool:
    if not category_enabled(prefs, category):
        return False
    if category == "security_alerts" and not prefs.get("loginNotifications", True):
        return False
    return True


def should_send_email(
    prefs: Dict[str, Any],
    category: str,
    *,
    priority: str = "normal",
) -> bool:
    if not prefs.get("emailNotifications", True):
        return False
    if not category_enabled(prefs, category):
        return False
    if category == "security_alerts" and not prefs.get("loginNotifications", True):
        return False
    digest = str(prefs.get("emailDigestFrequency") or "immediate")
    if digest == "never":
        return False
    if digest in {"daily", "weekly"}:
        # 摘要模式：即时邮件跳过，交由后续摘要任务处理
        return False
    if in_quiet_hours(prefs) and not is_urgent(priority):
        return False
    return True


def should_send_sms(
    prefs: Dict[str, Any],
    category: str,
    *,
    priority: str = "normal",
) -> bool:
    if not prefs.get("smsNotifications", False):
        return False
    if not category_enabled(prefs, category):
        return False
    if in_quiet_hours(prefs) and not is_urgent(priority):
        return False
    # 短信仅用于紧急类，避免打扰
    return is_urgent(priority)


def should_browser_push(
    prefs: Dict[str, Any],
    category: str,
    *,
    priority: str = "normal",
) -> bool:
    if not (prefs.get("pushNotifications", True) or prefs.get("desktopNotifications", True)):
        return False
    if not category_enabled(prefs, category):
        return False
    if in_quiet_hours(prefs) and not is_urgent(priority):
        return False
    return True


def map_quota_category(quota_type: str) -> str:
    if quota_type == "wps":
        return "wps_updates"
    if quota_type in {"pqr", "ppqr"}:
        return "pqr_approvals"
    return "system_updates"


def map_document_category(document_type: str) -> str:
    dtype = (document_type or "").lower()
    if "wps" in dtype:
        return "wps_updates"
    if "pqr" in dtype or "ppqr" in dtype:
        return "pqr_approvals"
    if "quality" in dtype:
        return "quality_alerts"
    return "pqr_approvals"


def announce_type_category(announcement_type: Optional[str]) -> str:
    atype = (announcement_type or "info").lower()
    if atype == "maintenance":
        return "maintenance"
    if atype in {"warning", "error"}:
        return "system_updates"
    return "system_updates"

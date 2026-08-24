"""
Default subscription plan seed data helpers.
"""
from __future__ import annotations

import json
import logging
from typing import Any, List

from sqlalchemy.orm import Session

from app.models.subscription import SubscriptionPlan

logger = logging.getLogger(__name__)


AI_ENTITLEMENT_DESCRIPTIONS = {
    "free": "平台 AI：10 点/月、5 点/日，单次最多 10 页",
    "personal_free": "平台 AI：10 点/月、5 点/日，单次最多 10 页",
    "personal_pro": "平台 AI：100 点/月、50 点/日，单次最多 30 页",
    "personal_advanced": "平台 AI：300 点/月、50 点/日，单次最多 30 页",
    "personal_flagship": "平台 AI：1000 点/月、50 点/日，单次最多 30 页",
    "enterprise": "企业工作区共享平台 AI：2000 点/月、500 点/日，单次最多 30 页",
    "enterprise_pro": "企业工作区共享平台 AI：6000 点/月、500 点/日，单次最多 30 页",
    "enterprise_pro_max": "企业工作区共享平台 AI：20000 点/月、500 点/日，单次最多 30 页",
}


def ai_entitlement_features(tier_key: str) -> List[str]:
    description = AI_ENTITLEMENT_DESCRIPTIONS.get(tier_key)
    if not description:
        return []
    return [
        description,
        "自有 API Key 不扣平台 AI 点数，但仍受单次页数和任务并发限制",
    ]

DEFAULT_SUBSCRIPTION_PLANS: List[dict] = [
    {
        "id": "free",
        "name": "个人免费版",
        "description": "基础功能，适合个人用户试用",
        "monthly_price": 0,
        "quarterly_price": 0,
        "yearly_price": 0,
        "currency": "CNY",
        "max_wps_files": 10,
        "max_pqr_files": 10,
        "max_ppqr_files": 0,
        "max_materials": 0,
        "max_welders": 0,
        "max_equipment": 0,
        "max_factories": 0,
        "max_employees": 0,
        "features": "WPS管理模块（10个）,PQR管理模块（10个）",
        "sort_order": 1,
        "is_recommended": False,
        "is_active": True,
    },
    {
        "id": "personal_pro",
        "name": "个人专业版",
        "description": "适合个人专业用户，包含基础管理功能",
        "monthly_price": 19,
        "quarterly_price": 51,
        "yearly_price": 183,
        "currency": "CNY",
        "max_wps_files": 30,
        "max_pqr_files": 30,
        "max_ppqr_files": 30,
        "max_materials": 50,
        "max_welders": 20,
        "max_equipment": 0,
        "max_factories": 0,
        "max_employees": 0,
        "features": "WPS管理模块（30个）,PQR管理模块（30个）,pPQR管理模块（30个）,焊材管理模块,焊工管理模块",
        "sort_order": 2,
        "is_recommended": True,
        "is_active": True,
    },
    {
        "id": "personal_advanced",
        "name": "个人高级版",
        "description": "适合需要高级功能的个人用户",
        "monthly_price": 49,
        "quarterly_price": 132,
        "yearly_price": 470,
        "currency": "CNY",
        "max_wps_files": 50,
        "max_pqr_files": 50,
        "max_ppqr_files": 50,
        "max_materials": 100,
        "max_welders": 50,
        "max_equipment": 20,
        "max_factories": 0,
        "max_employees": 0,
        "features": "WPS管理模块（50个）,PQR管理模块（50个）,pPQR管理模块（50个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块",
        "sort_order": 3,
        "is_recommended": False,
        "is_active": True,
    },
    {
        "id": "personal_flagship",
        "name": "个人旗舰版",
        "description": "个人用户最全功能版本",
        "monthly_price": 99,
        "quarterly_price": 267,
        "yearly_price": 950,
        "currency": "CNY",
        "max_wps_files": 100,
        "max_pqr_files": 100,
        "max_ppqr_files": 100,
        "max_materials": 200,
        "max_welders": 100,
        "max_equipment": 50,
        "max_factories": 0,
        "max_employees": 0,
        "features": "WPS管理模块（100个）,PQR管理模块（100个）,pPQR管理模块（100个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块,报表统计模块",
        "sort_order": 4,
        "is_recommended": False,
        "is_active": True,
    },
    {
        "id": "enterprise",
        "name": "企业版",
        "description": "适合小型企业，包含员工管理功能",
        "monthly_price": 199,
        "quarterly_price": 537,
        "yearly_price": 1910,
        "currency": "CNY",
        "max_wps_files": 200,
        "max_pqr_files": 200,
        "max_ppqr_files": 200,
        "max_materials": 500,
        "max_welders": 200,
        "max_equipment": 100,
        "max_factories": 1,
        "max_employees": 10,
        "features": "WPS管理模块（200个）,PQR管理模块（200个）,pPQR管理模块（200个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块,报表统计模块,企业员工管理模块（10人）,多工厂数量：1个",
        "sort_order": 5,
        "is_recommended": False,
        "is_active": True,
    },
    {
        "id": "enterprise_pro",
        "name": "企业版PRO",
        "description": "适合中型企业，更多员工和工厂",
        "monthly_price": 399,
        "quarterly_price": 1077,
        "yearly_price": 3830,
        "currency": "CNY",
        "max_wps_files": 400,
        "max_pqr_files": 400,
        "max_ppqr_files": 400,
        "max_materials": 1000,
        "max_welders": 500,
        "max_equipment": 200,
        "max_factories": 3,
        "max_employees": 20,
        "features": "WPS管理模块（400个）,PQR管理模块（400个）,pPQR管理模块（400个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块,报表统计模块,企业员工管理模块（20人）,多工厂数量：3个",
        "sort_order": 6,
        "is_recommended": False,
        "is_active": True,
    },
    {
        "id": "enterprise_pro_max",
        "name": "企业版PRO MAX",
        "description": "适合大型企业，最全功能和最高配额",
        "monthly_price": 899,
        "quarterly_price": 2427,
        "yearly_price": 8630,
        "currency": "CNY",
        "max_wps_files": 500,
        "max_pqr_files": 500,
        "max_ppqr_files": 500,
        "max_materials": 2000,
        "max_welders": 1000,
        "max_equipment": 500,
        "max_factories": 5,
        "max_employees": 50,
        "features": "WPS管理模块（500个）,PQR管理模块（500个）,pPQR管理模块（500个）,焊材管理模块,焊工管理模块,生产管理模块,设备管理模块,质量管理模块,报表统计模块,企业员工管理模块（50人）,多工厂数量：5个",
        "sort_order": 7,
        "is_recommended": False,
        "is_active": True,
    },
]


def parse_plan_features(raw: Any) -> List[str]:
    """Normalize plan.features stored as CSV or JSON list."""
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    text = str(raw).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [str(x).strip() for x in data if str(x).strip()]
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    return [part.strip() for part in text.split(",") if part.strip()]


def ensure_subscription_plans(db: Session) -> int:
    """
    Seed default subscription plans when the table is empty.
    Returns number of plans created.
    """
    existing = db.query(SubscriptionPlan).count()
    if existing > 0:
        return 0

    for plan_data in DEFAULT_SUBSCRIPTION_PLANS:
        db.add(SubscriptionPlan(**plan_data))
    db.commit()
    created = len(DEFAULT_SUBSCRIPTION_PLANS)
    logger.info("Seeded %s default subscription plans", created)
    return created

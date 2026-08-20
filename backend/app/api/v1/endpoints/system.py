"""
System management endpoints for the welding system backend.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps
from app.core.config import settings
from app.core.health import readiness
from app.services.branding_service import get_branding

router = APIRouter()


@router.get("/health")
def system_health(
    current_user: dict = Depends(deps.get_current_admin_user)
) -> Any:
    """管理员查看依赖健康状态."""
    del current_user
    return readiness()


@router.get("/info")
def system_info(
    current_user: dict = Depends(deps.get_current_admin_user)
) -> Any:
    """系统信息."""
    del current_user
    return {
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEVELOPMENT else "production",
        "app_name": settings.APP_NAME,
    }


@router.get("/branding")
def system_branding() -> Any:
    """公开品牌信息（侧栏产品名/企业名），无需登录."""
    return {
        "success": True,
        "data": get_branding(),
    }


@router.get("/public-config")
def system_public_config() -> Any:
    """公开运行时开关（维护模式/注册开关），无需登录."""
    from app.services.system_config_service import get_public_system_config

    return {
        "success": True,
        "data": get_public_system_config(),
    }


@router.put("/branding")
def update_system_branding(
    payload: dict,
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    """用户端更新品牌/企业显示名（不经由管理门户）."""
    from app.services.branding_service import BRANDING_KEYS, update_branding

    del current_user
    data = {k: payload[k] for k in BRANDING_KEYS if k in payload}
    if not data:
        return {"success": False, "message": "无有效字段"}
    return {"success": True, "data": update_branding(data), "message": "品牌信息已更新"}

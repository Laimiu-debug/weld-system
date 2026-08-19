"""
System management endpoints for the welding system backend.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps
from app.core.config import settings
from app.core.health import readiness

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

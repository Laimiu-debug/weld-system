"""
System management endpoints for the welding system backend.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps
from app.core.database import db_manager

router = APIRouter()


@router.get("/health")
async def system_health(
    current_user: dict = Depends(deps.get_current_admin_user)
) -> Any:
    """系统健康检查."""
    health_status = await db_manager.health_check()
    return health_status


@router.get("/info")
async def system_info(
    current_user: dict = Depends(deps.get_current_admin_user)
) -> Any:
    """系统信息."""
    return {
        "message": "系统信息功能开发中...",
        "version": "1.0.0",
        "environment": "development"
    }
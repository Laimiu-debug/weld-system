"""
WPS management endpoints for the welding system backend.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps

router = APIRouter()


@router.get("/")
async def get_wps_list(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """获取WPS列表."""
    return {"message": "WPS管理功能开发中..."}


@router.post("/")
async def create_wps(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """创建WPS."""
    return {"message": "WPS创建功能开发中..."}
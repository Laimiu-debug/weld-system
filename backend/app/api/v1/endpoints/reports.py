"""
Reports endpoints for the welding system backend.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps

router = APIRouter()


@router.get("/")
async def get_reports(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """获取报表列表."""
    return {"message": "报表功能开发中..."}


@router.get("/statistics")
async def get_statistics(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """获取统计数据."""
    return {"message": "统计功能开发中..."}
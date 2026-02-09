"""
PQR management endpoints for the welding system backend.
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps

router = APIRouter()


@router.get("/")
async def get_pqr_list(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """获取PQR列表."""
    return {"message": "PQR管理功能开发中..."}


@router.post("/")
async def create_pqr(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """创建PQR."""
    return {"message": "PQR创建功能开发中..."}
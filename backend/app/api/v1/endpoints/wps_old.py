"""Legacy WPS stubs. Real WPS APIs live in wps.py."""
from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps
from app.core.errors import not_implemented

router = APIRouter()


@router.get("/")
async def get_wps_list(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    del current_user
    not_implemented("旧版 WPS 列表")


@router.post("/")
async def create_wps(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    del current_user
    not_implemented("旧版 WPS 创建")

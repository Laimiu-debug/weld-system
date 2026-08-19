"""Legacy PQR stubs. Real PQR APIs live in pqr.py."""
from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps
from app.core.errors import not_implemented

router = APIRouter()


@router.get("/")
async def get_pqr_list(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    del current_user
    not_implemented("旧版 PQR 列表")


@router.post("/")
async def create_pqr(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    del current_user
    not_implemented("旧版 PQR 创建")

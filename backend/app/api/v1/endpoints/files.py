"""
File management endpoints for the welding system backend.
"""
from typing import Any

from fastapi import APIRouter, Depends, UploadFile, File

from app.api import deps
from app.core.errors import not_implemented

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """上传文件. 实际上传请使用 /upload 模块."""
    del file, current_user
    not_implemented("files 上传（请使用 /api/v1/upload）")


@router.get("/{file_id}")
async def download_file(
    file_id: int,
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """下载文件."""
    del file_id, current_user
    not_implemented("files 下载")

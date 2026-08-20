"""
File management endpoints for the welding system backend.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api import deps
from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit
from app.services.system_config_service import get_max_upload_bytes

router = APIRouter()


def _allowed_suffix(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    allowed = {item.lower() if item.startswith(".") else f".{item.lower()}" for item in settings.ALLOWED_EXTENSIONS}
    if suffix not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，允许: {', '.join(sorted(allowed))}",
        )
    return suffix


def _storage_dir() -> Path:
    root = Path(settings.UPLOAD_DIR).resolve()
    target = root / "files"
    target.mkdir(parents=True, exist_ok=True)
    return target


@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(deps.get_current_user),
) -> Any:
    """上传通用附件到本地存储。"""
    enforce_rate_limit(f"upload-user:{getattr(current_user, 'id', 'anon')}", limit=20, window_seconds=60)
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有选择文件")
    suffix = _allowed_suffix(file.filename)
    content = file.file.read()
    max_bytes = get_max_upload_bytes()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大，最大允许 {max(1, max_bytes // (1024 * 1024))}MB",
        )
    stored_name = f"{uuid.uuid4().hex}_{int(datetime.utcnow().timestamp())}{suffix}"
    dest = _storage_dir() / stored_name
    dest.write_bytes(content)
    return {
        "success": True,
        "data": {
            "file_id": stored_name,
            "filename": os.path.basename(file.filename),
            "size": len(content),
            "url": f"/api/v1/files/{stored_name}",
        },
    }


@router.get("/{file_id}")
def download_file(
    file_id: str,
    current_user=Depends(deps.get_current_user),
) -> Any:
    """下载已上传的附件。"""
    del current_user
    if "/" in file_id or "\\" in file_id or ".." in file_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的文件编号")
    path = _storage_dir() / file_id
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    return FileResponse(path, filename=file_id)

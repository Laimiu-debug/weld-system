"""
File management endpoints for the welding system backend.
"""
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.api import deps
from app.core.data_access import DataAccessMiddleware
from app.models.attachment import Attachment
from app.schemas.api_response import SuccessResponse, AttachmentUploadResponse
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


def _business_record(db, user, resource_type, resource_id, action):
    from app.models.quality import QualityInspection
    from app.models.wps import WPS
    from app.models.pqr import PQR
    from app.models.ppqr import PPQR
    from app.models.production import ProductionTask
    from app.models.welder import Welder
    from app.models.equipment import Equipment
    from app.models.material import WeldingMaterial

    models = {"quality": QualityInspection, "wps": WPS, "pqr": PQR, "ppqr": PPQR,
              "production": ProductionTask, "welder": Welder, "equipment": Equipment,
              "material": WeldingMaterial}
    model = models.get(resource_type)
    if model is None:
        raise HTTPException(422, "不支持的附件业务类型")
    record = db.query(model).filter(model.id == resource_id).first()
    if record is None or getattr(record, "is_active", True) is False or getattr(record, "is_deleted", False) is True:
        raise HTTPException(404, "附件关联记录不存在")
    DataAccessMiddleware(db).check_access(user, record, action)
    return record


def _get_attachment(db, user, file_id, action="view"):
    if "/" in file_id or "\\" in file_id or ".." in file_id:
        raise HTTPException(400, "无效的文件编号")
    attachment = db.query(Attachment).filter(Attachment.id == file_id).first()
    # Old files have no trustworthy ownership metadata: never infer from a filename.
    if attachment is None:
        raise HTTPException(404, "附件不存在或尚未登记归属")
    record = _business_record(db, user, attachment.resource_type, attachment.resource_id, action)
    if (attachment.workspace_type, attachment.company_id, attachment.factory_id) != (
        record.workspace_type, record.company_id, record.factory_id
    ):
        raise HTTPException(403, "附件与业务记录的工作区归属不一致")
    return attachment


@router.post("/upload", response_model=SuccessResponse[AttachmentUploadResponse], response_model_exclude_none=True)
def upload_file(
    file: UploadFile = File(...),
    resource_type: str = Form(...),
    resource_id: int = Form(..., gt=0),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    """Stream a bounded attachment after checking write access to its parent."""
    enforce_rate_limit(f"upload-user:{current_user.id}", limit=20, window_seconds=60)
    if not file.filename:
        raise HTTPException(400, "没有选择文件")
    suffix = _allowed_suffix(file.filename)
    record = _business_record(db, current_user, resource_type, resource_id, "edit")
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = _storage_dir() / stored_name
    size = 0
    max_bytes = get_max_upload_bytes()
    filename = file.filename.replace("\\", "/").rsplit("/", 1)[-1][:255]
    try:
        with dest.open("xb") as output:
            while True:
                chunk = file.file.read(min(64 * 1024, max_bytes - size + 1))
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(400, "文件超过上传大小限制")
                output.write(chunk)
        if not size:
            raise HTTPException(400, "不能上传空文件")
        attachment = Attachment(
            id=stored_name, filename=filename, size_bytes=size, user_id=current_user.id,
            workspace_type=record.workspace_type, company_id=record.company_id,
            factory_id=record.factory_id, resource_type=resource_type, resource_id=resource_id,
        )
        db.add(attachment)
        db.commit()
    except Exception:
        db.rollback()
        dest.unlink(missing_ok=True)
        raise
    return {"success": True, "data": {"file_id": stored_name, "filename": filename,
            "size": size, "url": f"/api/v1/files/{stored_name}"}}


@router.get("/{file_id}")
def download_file(
    file_id: str,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    attachment = _get_attachment(db, current_user, file_id)
    root = _storage_dir().resolve()
    path = (root / file_id).resolve()
    if path.parent != root or not path.is_file():
        raise HTTPException(404, "文件不存在")
    return FileResponse(path, filename=attachment.filename, media_type="application/octet-stream",
                        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.delete("/{file_id}", response_model=SuccessResponse[None], response_model_exclude_none=True)
def delete_file(
    file_id: str,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_active_user),
) -> Any:
    attachment = _get_attachment(db, current_user, file_id, "edit")
    if attachment.user_id != current_user.id:
        raise HTTPException(403, "仅上传者可以清理附件")
    record = _business_record(db, current_user, attachment.resource_type, attachment.resource_id, "edit")
    if attachment.resource_type == "quality":
        try:
            photos = json.loads(record.photos or "[]")
        except (ValueError, TypeError):
            raise HTTPException(409, "请先核对业务记录中的附件引用")
        if any((photo.get("file_id") if isinstance(photo, dict) else photo) == file_id for photo in photos):
            raise HTTPException(409, "附件仍被检验记录引用，请先移除引用")
    # Commit metadata removal first; any interrupted physical cleanup leaves an inaccessible file.
    db.delete(attachment)
    db.commit()
    (_storage_dir() / file_id).unlink(missing_ok=True)
    return {"success": True}

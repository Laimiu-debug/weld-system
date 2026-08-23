"""Private document storage abstraction used by smart import."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol
from uuid import uuid4

from app.core.config import settings


DOCUMENT_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


class DocumentUploadError(ValueError):
    pass


@dataclass(frozen=True)
class StoredDocument:
    original_filename: str
    storage_key: str
    sha256: str
    size_bytes: int
    mime_type: str


class DocumentStorage(Protocol):
    def save_stream(
        self, stream: BinaryIO, original_filename: str, max_bytes: int
    ) -> StoredDocument:
        ...

    def delete(self, storage_key: str) -> None:
        ...

    def open_stream(self, storage_key: str) -> BinaryIO:
        ...


class LocalDocumentStorage:
    """Local private storage; storage keys are opaque and never public URLs."""

    def __init__(self, root: Path | None = None):
        self.root = (root or Path(settings.UPLOAD_DIR)).resolve()
        self.document_root = (self.root / "private_documents").resolve()
        self.staging_root = (self.root / ".smart_import_staging").resolve()
        self.document_root.mkdir(parents=True, exist_ok=True)
        self.staging_root.mkdir(parents=True, exist_ok=True)

    def save_stream(
        self, stream: BinaryIO, original_filename: str, max_bytes: int
    ) -> StoredDocument:
        if not original_filename or Path(original_filename).name != original_filename:
            raise DocumentUploadError("文件名无效")
        suffix = Path(original_filename).suffix.lower()
        if suffix not in DOCUMENT_TYPES:
            raise DocumentUploadError("仅支持 PDF、Word 和常见扫描图片")
        if max_bytes <= 0:
            raise DocumentUploadError("上传大小限制配置无效")

        staging_path = self.staging_root / f"{uuid4().hex}.part"
        digest = hashlib.sha256()
        size = 0
        header = b""
        try:
            with staging_path.open("xb") as destination:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    if not isinstance(chunk, bytes):
                        raise DocumentUploadError("上传内容无效")
                    size += len(chunk)
                    if size > max_bytes:
                        raise DocumentUploadError("文件超过系统允许的最大大小")
                    if len(header) < 16:
                        header += chunk[: 16 - len(header)]
                    digest.update(chunk)
                    destination.write(chunk)
            if size == 0:
                raise DocumentUploadError("不能上传空文件")
            self._validate_signature(suffix, header)

            sha256 = digest.hexdigest()
            target_dir = (self.document_root / sha256[:2]).resolve()
            target_dir.mkdir(parents=True, exist_ok=True)
            target = (target_dir / f"{uuid4().hex}{suffix}").resolve()
            if not target.is_relative_to(self.document_root):
                raise DocumentUploadError("存储路径无效")
            staging_path.replace(target)
            return StoredDocument(
                original_filename=original_filename,
                storage_key=target.relative_to(self.root).as_posix(),
                sha256=sha256,
                size_bytes=size,
                mime_type=DOCUMENT_TYPES[suffix],
            )
        except Exception:
            staging_path.unlink(missing_ok=True)
            raise

    def delete(self, storage_key: str) -> None:
        candidate = self._private_path(storage_key)
        candidate.unlink(missing_ok=True)

    def open_stream(self, storage_key: str) -> BinaryIO:
        candidate = self._private_path(storage_key)
        if not candidate.is_file():
            raise DocumentUploadError("私有原件不存在")
        return candidate.open("rb")

    def _private_path(self, storage_key: str) -> Path:
        candidate = (self.root / storage_key).resolve()
        if not candidate.is_relative_to(self.document_root):
            raise DocumentUploadError("拒绝访问私有文档目录之外的文件")
        return candidate

    @staticmethod
    def _validate_signature(suffix: str, header: bytes) -> None:
        valid = False
        if suffix == ".pdf":
            valid = header.startswith(b"%PDF-")
        elif suffix == ".doc":
            valid = header.startswith(bytes.fromhex("D0CF11E0A1B11AE1"))
        elif suffix == ".docx":
            valid = header.startswith(b"PK\x03\x04")
        elif suffix == ".png":
            valid = header.startswith(b"\x89PNG\r\n\x1a\n")
        elif suffix in {".jpg", ".jpeg"}:
            valid = header.startswith(b"\xff\xd8\xff")
        elif suffix in {".tif", ".tiff"}:
            valid = header.startswith((b"II*\x00", b"MM\x00*"))
        if not valid:
            raise DocumentUploadError("文件内容与扩展名不匹配")


def get_document_storage() -> DocumentStorage:
    return LocalDocumentStorage()

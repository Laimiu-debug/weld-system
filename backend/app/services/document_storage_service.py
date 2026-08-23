"""Private document storage abstraction used by smart import."""
from __future__ import annotations

import hashlib
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Protocol
from uuid import uuid4

from app.core.config import settings


DOCUMENT_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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


def _validate_filename(original_filename: str, max_bytes: int) -> str:
    if not original_filename or Path(original_filename).name != original_filename:
        raise DocumentUploadError("文件名无效")
    suffix = Path(original_filename).suffix.lower()
    if suffix not in DOCUMENT_TYPES:
        raise DocumentUploadError("仅支持 PDF、Word、Excel 和常见扫描图片")
    if max_bytes <= 0:
        raise DocumentUploadError("上传大小限制配置无效")
    return suffix


def _validate_payload(suffix: str, payload: BinaryIO) -> None:
    payload.seek(0)
    header = payload.read(16)
    LocalDocumentStorage._validate_signature(suffix, header)
    payload.seek(0)
    if suffix == ".pdf":
        dangerous = (b"/JavaScript", b"/JS ", b"/EmbeddedFile", b"/Launch")
        overlap = b""
        while True:
            chunk = payload.read(1024 * 1024)
            if not chunk:
                break
            searchable = overlap + chunk
            if any(marker in searchable for marker in dangerous):
                raise DocumentUploadError("PDF 包含脚本、附件或启动动作，已拒绝上传")
            overlap = searchable[-32:]
    elif suffix in {".docx", ".xlsx"}:
        try:
            with zipfile.ZipFile(payload) as archive:
                names = set(archive.namelist())
                required = (
                    {"[Content_Types].xml", "word/document.xml"}
                    if suffix == ".docx"
                    else {"[Content_Types].xml", "xl/workbook.xml"}
                )
                if not required.issubset(names):
                    raise DocumentUploadError("DOCX 文件结构无效")
                lowered = {name.lower() for name in names}
                if any(name.endswith("vbaproject.bin") for name in lowered):
                    raise DocumentUploadError("文件包含宏代码，已拒绝上传")
        except zipfile.BadZipFile as exc:
            raise DocumentUploadError("DOCX 文件结构无效") from exc
    payload.seek(0)


def _copy_and_validate(
    stream: BinaryIO, destination: BinaryIO, suffix: str, max_bytes: int
) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        if not isinstance(chunk, bytes):
            raise DocumentUploadError("上传内容无效")
        size += len(chunk)
        if size > max_bytes:
            raise DocumentUploadError("文件超过系统允许的最大大小")
        digest.update(chunk)
        destination.write(chunk)
    if size == 0:
        raise DocumentUploadError("不能上传空文件")
    destination.seek(0)
    _validate_payload(suffix, destination)
    return digest.hexdigest(), size


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
        suffix = _validate_filename(original_filename, max_bytes)

        staging_path = self.staging_root / f"{uuid4().hex}.part"
        try:
            with staging_path.open("x+b") as destination:
                sha256, size = _copy_and_validate(
                    stream, destination, suffix, max_bytes
                )

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
        elif suffix in {".docx", ".xlsx"}:
            valid = header.startswith(b"PK\x03\x04")
        elif suffix == ".png":
            valid = header.startswith(b"\x89PNG\r\n\x1a\n")
        elif suffix in {".jpg", ".jpeg"}:
            valid = header.startswith(b"\xff\xd8\xff")
        elif suffix in {".tif", ".tiff"}:
            valid = header.startswith((b"II*\x00", b"MM\x00*"))
        if not valid:
            raise DocumentUploadError("文件内容与扩展名不匹配")


class S3DocumentStorage:
    """S3-compatible private object storage, including self-hosted MinIO."""

    def __init__(
        self,
        client: Any | None = None,
        bucket: str | None = None,
        prefix: str | None = None,
    ):
        self.bucket = bucket or settings.DOCUMENT_STORAGE_S3_BUCKET
        if not self.bucket:
            raise RuntimeError("S3/MinIO 存储未配置 bucket")
        self.prefix = (prefix or settings.DOCUMENT_STORAGE_S3_PREFIX).strip("/")
        if not self.prefix or ".." in self.prefix.split("/"):
            raise RuntimeError("S3/MinIO 存储前缀无效")
        if client is None:
            import boto3

            client = boto3.client(
                "s3",
                endpoint_url=settings.DOCUMENT_STORAGE_S3_ENDPOINT_URL,
                region_name=settings.DOCUMENT_STORAGE_S3_REGION,
                aws_access_key_id=settings.DOCUMENT_STORAGE_S3_ACCESS_KEY_ID,
                aws_secret_access_key=settings.DOCUMENT_STORAGE_S3_SECRET_ACCESS_KEY,
            )
        self.client = client

    def save_stream(
        self, stream: BinaryIO, original_filename: str, max_bytes: int
    ) -> StoredDocument:
        suffix = _validate_filename(original_filename, max_bytes)
        with tempfile.SpooledTemporaryFile(
            max_size=min(max_bytes, 8 * 1024 * 1024)
        ) as staged:
            sha256, size = _copy_and_validate(stream, staged, suffix, max_bytes)
            storage_key = f"{self.prefix}/{sha256[:2]}/{uuid4().hex}{suffix}"
            staged.seek(0)
            self.client.upload_fileobj(
                staged,
                self.bucket,
                storage_key,
                ExtraArgs={"ContentType": DOCUMENT_TYPES[suffix]},
            )
        return StoredDocument(
            original_filename=original_filename,
            storage_key=storage_key,
            sha256=sha256,
            size_bytes=size,
            mime_type=DOCUMENT_TYPES[suffix],
        )

    def delete(self, storage_key: str) -> None:
        self._validate_key(storage_key)
        self.client.delete_object(Bucket=self.bucket, Key=storage_key)

    def open_stream(self, storage_key: str) -> BinaryIO:
        self._validate_key(storage_key)
        destination = tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024)
        try:
            self.client.download_fileobj(self.bucket, storage_key, destination)
            destination.seek(0)
            return destination
        except Exception:
            destination.close()
            raise

    def _validate_key(self, storage_key: str) -> None:
        expected = f"{self.prefix}/"
        if not storage_key.startswith(expected) or ".." in storage_key.split("/"):
            raise DocumentUploadError("拒绝访问私有文档前缀之外的对象")


def get_document_storage() -> DocumentStorage:
    backend = settings.DOCUMENT_STORAGE_BACKEND.strip().lower()
    if backend == "local":
        return LocalDocumentStorage()
    if backend in {"s3", "minio"}:
        return S3DocumentStorage()
    raise RuntimeError(f"不支持的文档存储后端: {backend}")

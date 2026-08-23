import hashlib
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from types import SimpleNamespace

from app.api.v1.endpoints import smart_import as smart_import_endpoint

from app.services.document_storage_service import (
    DocumentUploadError,
    LocalDocumentStorage,
)


def test_private_storage_streams_hashes_and_deletes_document(tmp_path) -> None:
    content = b"%PDF-1.7\nexample welding procedure"
    storage = LocalDocumentStorage(tmp_path)

    result = storage.save_stream(BytesIO(content), "PQR-001.pdf", max_bytes=1024)

    assert result.sha256 == hashlib.sha256(content).hexdigest()
    assert result.size_bytes == len(content)
    assert result.mime_type == "application/pdf"
    stored_path = tmp_path / result.storage_key
    assert stored_path.read_bytes() == content
    assert stored_path.is_relative_to(tmp_path / "private_documents")

    with storage.open_stream(result.storage_key) as stream:
        assert stream.read() == content

    storage.delete(result.storage_key)
    assert not stored_path.exists()


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("fake.pdf", b"not a pdf"),
        ("fake.docx", b"not a zip"),
        ("fake.png", b"not a png"),
    ],
)
def test_signature_mismatch_is_rejected_and_staging_is_cleaned(
    tmp_path, filename: str, content: bytes
) -> None:
    storage = LocalDocumentStorage(tmp_path)

    with pytest.raises(DocumentUploadError, match="内容与扩展名不匹配"):
        storage.save_stream(BytesIO(content), filename, max_bytes=1024)

    assert list((tmp_path / ".smart_import_staging").glob("*.part")) == []
    assert list((tmp_path / "private_documents").rglob("*.*")) == []


def test_oversized_and_path_filenames_are_rejected(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path)

    with pytest.raises(DocumentUploadError, match="最大大小"):
        storage.save_stream(BytesIO(b"%PDF-" + b"x" * 20), "big.pdf", max_bytes=10)
    with pytest.raises(DocumentUploadError, match="文件名无效"):
        storage.save_stream(BytesIO(b"%PDF-1.7"), "../escape.pdf", max_bytes=100)


def test_delete_cannot_escape_private_document_root(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path / "uploads")
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"keep")

    with pytest.raises(DocumentUploadError, match="拒绝访问"):
        storage.delete("../outside.pdf")
    with pytest.raises(DocumentUploadError, match="拒绝访问"):
        storage.open_stream("../outside.pdf")

    assert outside.read_bytes() == b"keep"


def test_upload_endpoint_removes_file_when_database_registration_fails(
    tmp_path, monkeypatch
) -> None:
    storage = LocalDocumentStorage(tmp_path)

    class FailingService:
        def __init__(self, db):
            del db

        def get_batch(self, batch_id, user, context):
            del batch_id, user, context
            return SimpleNamespace(id="batch-1", target_entity_type="pqr")

        def register_document(self, batch_id, data, user, context):
            del batch_id, data, user, context
            raise HTTPException(status_code=409, detail="duplicate")

    monkeypatch.setattr(smart_import_endpoint, "SmartImportService", FailingService)
    monkeypatch.setattr(
        smart_import_endpoint,
        "resolve_workspace",
        lambda db, user, workspace_id: SimpleNamespace(),
    )
    monkeypatch.setattr(
        smart_import_endpoint, "enforce_rate_limit", lambda *a, **k: None
    )
    monkeypatch.setattr(smart_import_endpoint, "get_max_upload_bytes", lambda: 1024)

    upload = UploadFile(filename="PQR.pdf", file=BytesIO(b"%PDF-1.7\ncontent"))
    with pytest.raises(HTTPException) as exc_info:
        smart_import_endpoint.upload_document(
            batch_id="batch-1",
            file=upload,
            document_type=None,
            document_version=None,
            db=object(),
            current_user=SimpleNamespace(id=1),
            workspace_id=None,
            storage=storage,
        )

    assert exc_info.value.detail == "duplicate"
    assert list((tmp_path / "private_documents").rglob("*.*")) == []

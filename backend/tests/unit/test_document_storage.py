import hashlib
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from fastapi import HTTPException, UploadFile
from types import SimpleNamespace

from app.api.v1.endpoints import smart_import as smart_import_endpoint

from app.services.document_storage_service import (
    DocumentUploadError,
    LocalDocumentStorage,
    S3DocumentStorage,
)
from app.services.document_artifact_service import (
    DocumentArtifactRetentionService,
    artifact_expiry,
)


def _docx(extra_files: dict[str, bytes] | None = None) -> bytes:
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr("[Content_Types].xml", b"<Types />")
        archive.writestr("word/document.xml", b"<document />")
        for name, content in (extra_files or {}).items():
            archive.writestr(name, content)
    return payload.getvalue()


def _xlsx(extra_files: dict[str, bytes] | None = None) -> bytes:
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr("[Content_Types].xml", b"<Types />")
        archive.writestr("xl/workbook.xml", b"<workbook />")
        for name, content in (extra_files or {}).items():
            archive.writestr(name, content)
    return payload.getvalue()


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


def test_active_pdf_and_macro_docx_are_rejected(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path)

    with pytest.raises(DocumentUploadError, match="脚本、附件或启动动作"):
        storage.save_stream(
            BytesIO(b"%PDF-1.7\n1 0 obj <</JavaScript 2 0 R>>"),
            "active.pdf",
            max_bytes=1024,
        )


def test_xlsx_roster_is_accepted_and_macro_workbook_is_rejected(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path)
    result = storage.save_stream(BytesIO(_xlsx()), "welders.xlsx", max_bytes=4096)
    assert result.mime_type.endswith("spreadsheetml.sheet")
    with pytest.raises(DocumentUploadError, match="宏代码"):
        storage.save_stream(
            BytesIO(_xlsx({"xl/vbaProject.bin": b"macro"})),
            "macro.xlsx",
            max_bytes=4096,
        )
    with pytest.raises(DocumentUploadError, match="宏代码"):
        storage.save_stream(
            BytesIO(_docx({"word/vbaProject.bin": b"macro"})),
            "macro.docx",
            max_bytes=4096,
        )


def test_s3_compatible_storage_roundtrip_and_key_isolation() -> None:
    class FakeS3:
        def __init__(self):
            self.objects = {}

        def upload_fileobj(self, stream, bucket, key, ExtraArgs=None):
            self.objects[(bucket, key)] = (stream.read(), ExtraArgs)

        def download_fileobj(self, bucket, key, destination):
            destination.write(self.objects[(bucket, key)][0])

        def delete_object(self, Bucket, Key):
            self.objects.pop((Bucket, Key), None)

    client = FakeS3()
    storage = S3DocumentStorage(
        client=client, bucket="weld-private", prefix="tenant-documents"
    )
    content = _docx()

    result = storage.save_stream(BytesIO(content), "WPS.docx", max_bytes=4096)

    assert result.storage_key.startswith("tenant-documents/")
    assert result.sha256 == hashlib.sha256(content).hexdigest()
    with storage.open_stream(result.storage_key) as stream:
        assert stream.read() == content
    with pytest.raises(DocumentUploadError, match="私有文档前缀"):
        storage.open_stream("other-bucket/document.docx")
    storage.delete(result.storage_key)
    assert client.objects == {}


def test_artifact_retention_defaults_keep_originals_and_expire_derivatives() -> None:
    assert artifact_expiry("original") is None
    assert artifact_expiry("temporary") is not None
    assert artifact_expiry("evidence") is not None
    assert artifact_expiry("export") is not None


def test_retention_cleanup_deletes_payload_and_keeps_audit_tombstone() -> None:
    artifact = SimpleNamespace(
        storage_key="private_documents/a/file.pdf",
        status="active",
        metadata_json={"page_number": 1},
    )
    db = Mock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        artifact
    ]
    storage = Mock()

    count = DocumentArtifactRetentionService(db, storage).purge_expired()

    assert count == 1
    storage.delete.assert_called_once_with("private_documents/a/file.pdf")
    assert artifact.status == "deleted"
    assert artifact.storage_key is None
    assert artifact.metadata_json["deletion_reason"] == "retention_expired"
    db.commit.assert_called_once()


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

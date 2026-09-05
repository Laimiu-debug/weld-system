from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, UploadFile
from app.api.v1.endpoints import files


class BoundedInput(BytesIO):
    def read(self, size=-1):
        assert 0 < size <= 65536, "upload must never use an unbounded read"
        return super().read(size)


@pytest.mark.parametrize("failure", ["oversize", "empty", "commit", "read"])
def test_failed_upload_leaves_no_attachment_or_partial_file(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(files.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(files, "get_max_upload_bytes", lambda: 10)
    monkeypatch.setattr(files, "enforce_rate_limit", lambda *a, **k: None)
    monkeypatch.setattr(files, "_business_record", lambda *a: SimpleNamespace(workspace_type="personal", company_id=None, factory_id=None))
    db = MagicMock()
    stream = BoundedInput(b"12345678901" if failure == "oversize" else b"" if failure == "empty" else b"png")
    if failure == "commit":
        db.commit.side_effect = RuntimeError("database unavailable")
    if failure == "read":
        stream.read = MagicMock(side_effect=OSError("read failed"))
    with pytest.raises((HTTPException, RuntimeError, OSError)):
        files.upload_file(UploadFile(filename="x.png", file=stream), "quality", 1, db, SimpleNamespace(id=1))
    db.rollback.assert_called_once()
    assert list((tmp_path/"files").iterdir()) == []


def test_permission_denied_before_read_or_creating_file(tmp_path, monkeypatch):
    monkeypatch.setattr(files.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(files, "enforce_rate_limit", lambda *a, **k: None)
    monkeypatch.setattr(files, "_business_record", MagicMock(side_effect=HTTPException(403, "denied")))
    stream = MagicMock()
    with pytest.raises(HTTPException) as exc:
        files.upload_file(UploadFile(filename="x.png", file=stream), "quality", 1, MagicMock(), SimpleNamespace(id=1))
    assert exc.value.status_code == 403
    stream.read.assert_not_called()
    assert not (tmp_path/"files").exists()


def test_cannot_delete_attachment_after_uncertain_successful_photo_save(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(files, "_get_attachment", lambda *a: SimpleNamespace(user_id=1, resource_type="quality", resource_id=1))
    monkeypatch.setattr(files, "_business_record", lambda *a: SimpleNamespace(photos='[{"file_id":"saved.png"}]'))
    with pytest.raises(HTTPException) as exc:
        files.delete_file("saved.png", db, SimpleNamespace(id=1))
    assert exc.value.status_code == 409
    db.delete.assert_not_called()

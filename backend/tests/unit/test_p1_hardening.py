"""P1 hardening: health, auth body params, placeholders, rate limit, redaction."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api import deps
from app.api.v1.endpoints import auth, reports
from app.core.errors import error_body, redact_headers, redact_value
from app.core.health import liveness, readiness
from app.core.rate_limit import enforce_rate_limit


def test_liveness_does_not_check_dependencies():
    result = liveness()
    assert result["status"] == "ok"
    assert "version" in result


def test_readiness_not_ready_when_postgres_down(monkeypatch):
    monkeypatch.setattr("app.core.health._postgres_ok", lambda: (False, "unreachable"))
    monkeypatch.setattr("app.core.health._redis_ok", lambda: (True, "ok"))
    monkeypatch.setattr("app.core.health._alembic_revision", lambda: None)
    report = readiness()
    assert report["status"] == "not_ready"
    assert report["checks"]["postgres"]["ok"] is False


def test_redact_authorization_header():
    redacted = redact_headers(
        {"Authorization": "Bearer super-secret", "X-Request-ID": "abc"}
    )
    assert redacted["Authorization"] == "[redacted]"
    assert redacted["X-Request-ID"] == "abc"


def test_redact_value_hides_password_text():
    assert redact_value("password=hunter2") == "[redacted]"


def test_error_body_shape():
    body = error_body("NOT_IMPLEMENTED", "报表尚未开放")
    assert body["detail"]["code"] == "NOT_IMPLEMENTED"
    assert "request_id" in body


def test_memory_rate_limit_trips():
    key = "unit-test-rate-limit"
    with patch(
        "app.core.rate_limit.redis_client.incr",
        side_effect=RuntimeError("force memory fallback"),
    ):
        for _ in range(3):
            enforce_rate_limit(key, limit=3, window_seconds=60)
        with pytest.raises(HTTPException) as exc:
            enforce_rate_limit(key, limit=3, window_seconds=60)
    assert exc.value.status_code == 429


def _auth_client() -> TestClient:
    app = FastAPI()
    app.include_router(auth.router, prefix="/auth")
    app.dependency_overrides[deps.get_db] = lambda: MagicMock()
    return TestClient(app)


def test_forgot_password_rejects_query_string():
    client = _auth_client()
    response = client.post("/auth/forgot-password?email=a@example.com")
    assert response.status_code == 422


def test_forgot_password_json_body_does_not_enumerate_or_leak_token():
    client = _auth_client()
    with patch("app.api.v1.endpoints.auth.user_service") as users:
        users.get_by_email.return_value = None
        response = client.post(
            "/auth/forgot-password",
            json={"email": "missing@example.com"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert "reset_token" not in payload
    assert "未注册" not in payload.get("message", "")


def test_change_password_requires_json_body():
    client = _auth_client()
    app = client.app
    app.dependency_overrides[deps.get_current_user] = lambda: {"id": 1}
    response = client.post(
        "/auth/change-password?current_password=old&new_password=newpass",
    )
    assert response.status_code == 422


def test_reports_catalog_is_available():
    app = FastAPI()
    app.include_router(reports.router, prefix="/reports")
    app.dependency_overrides[deps.get_current_active_user] = lambda: SimpleNamespace(
        id=1
    )
    client = TestClient(app)
    response = client.get("/reports/")
    assert response.status_code == 200
    assert response.json()["data"]["items"]


def test_email_verify_token_cannot_reset_password():
    from app.core.security import (
        generate_email_verification_token,
        verify_email_verification_token,
        verify_password_reset_token,
    )

    token = generate_email_verification_token("user@example.com")
    assert verify_email_verification_token(token) == "user@example.com"
    assert verify_password_reset_token(token) is None


def test_verify_email_requires_json_body():
    client = _auth_client()
    response = client.post("/auth/verify-email?token=abc")
    assert response.status_code == 422


def test_verify_email_rejects_invalid_token():
    client = _auth_client()
    response = client.post("/auth/verify-email", json={"token": "not-a-jwt"})
    assert response.status_code == 400


def test_resend_verification_does_not_enumerate():
    client = _auth_client()
    with patch("app.api.v1.endpoints.auth.user_service") as users:
        users.get_by_email.return_value = None
        response = client.post(
            "/auth/resend-verification",
            json={"email": "missing@example.com"},
        )
    assert response.status_code == 200
    assert "如果该邮箱" in response.json()["message"]


def test_export_limit_trips_after_window():
    from app.core.rate_limit import enforce_export_limit

    user_id = 880017
    with patch(
        "app.core.rate_limit.redis_client.incr",
        side_effect=RuntimeError("force memory fallback"),
    ):
        for _ in range(20):
            enforce_export_limit(user_id)
        with pytest.raises(HTTPException) as exc:
            enforce_export_limit(user_id)
    assert exc.value.status_code == 429


def test_file_upload_rejects_disallowed_type(tmp_path, monkeypatch):
    from app.api.v1.endpoints import files

    monkeypatch.setattr(files.settings, "UPLOAD_DIR", str(tmp_path))
    app = FastAPI()
    app.include_router(files.router, prefix="/files")
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=1)
    client = TestClient(app)
    response = client.post(
        "/files/upload",
        files={"file": ("payload.exe", b"binary", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_file_upload_and_download_roundtrip(tmp_path, monkeypatch):
    from app.api.v1.endpoints import files

    monkeypatch.setattr(files.settings, "UPLOAD_DIR", str(tmp_path))
    app = FastAPI()
    app.include_router(files.router, prefix="/files")
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=1)
    client = TestClient(app)
    uploaded = client.post(
        "/files/upload",
        files={"file": ("note.png", b"png-bytes", "image/png")},
    )
    assert uploaded.status_code == 200
    file_id = uploaded.json()["data"]["file_id"]
    downloaded = client.get(f"/files/{file_id}")
    assert downloaded.status_code == 200
    assert downloaded.content == b"png-bytes"
    blocked = client.get("/files/..%2Fsecret.png")
    assert blocked.status_code in (400, 404)


def test_request_id_header_roundtrip():
    from app.core.observability import RequestContextMiddleware, get_request_id

    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/ping")
    def ping():
        return {"id": get_request_id()}

    client = TestClient(app)
    response = client.get("/ping", headers={"X-Request-ID": "req-1"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-1"
    assert response.json()["id"] == "req-1"
    assert "X-Process-Time" in response.headers


def test_load_latest_approvals_skips_empty():
    from app.services.approval_lookup import load_latest_approvals

    db = MagicMock()
    latest, workflows = load_latest_approvals(db, "wps", [])
    assert latest == {}
    assert workflows == {}
    db.query.assert_not_called()

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
    redacted = redact_headers({"Authorization": "Bearer super-secret", "X-Request-ID": "abc"})
    assert redacted["Authorization"] == "[redacted]"
    assert redacted["X-Request-ID"] == "abc"


def test_redact_value_hides_password_text():
    assert redact_value("password=hunter2") == "[redacted]"


def test_error_body_shape():
    body = error_body("NOT_IMPLEMENTED", "报表尚未开放")
    assert body["detail"]["code"] == "NOT_IMPLEMENTED"


def test_memory_rate_limit_trips():
    key = "unit-test-rate-limit"
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
    app.dependency_overrides[deps.get_current_active_user] = lambda: SimpleNamespace(id=1)
    client = TestClient(app)
    response = client.get("/reports/")
    assert response.status_code == 200
    assert response.json()["data"]["items"]

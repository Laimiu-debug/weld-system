"""Public error responses must not expose infrastructure details."""

from app.core.errors import (
    public_http_detail,
    redact_sensitive_data,
    sanitize_validation_errors,
)


def test_server_errors_are_always_stable() -> None:
    detail = public_http_detail(500, "psycopg2 connection failed password=secret")
    assert detail == {"code": "INTERNAL_ERROR", "message": "服务器内部错误"}


def test_technical_client_error_is_sanitized() -> None:
    detail = public_http_detail(
        400,
        "ProgrammingError: column users.preferences does not exist [SQL: SELECT ...]",
    )
    assert detail == {"code": "REQUEST_FAILED", "message": "请求处理失败"}


def test_business_client_error_is_preserved() -> None:
    assert public_http_detail(400, "设备编号已存在") == "设备编号已存在"


def test_validation_error_never_echoes_api_key_input() -> None:
    errors = [
        {
            "type": "string_too_long",
            "loc": ("body", "api_key"),
            "msg": "String should have at most 500 characters",
            "input": "sk-super-secret-value-123456789",
            "ctx": {"authorization": "Bearer another-secret-value"},
        }
    ]

    sanitized = sanitize_validation_errors(errors)

    assert sanitized[0]["input"] == "[redacted]"
    assert sanitized[0]["ctx"] == "[redacted]"
    assert "super-secret" not in str(sanitized)


def test_nested_task_or_audit_payload_redacts_secret_keys_and_bearer_values() -> None:
    payload = {
        "job_id": "job-1",
        "provider": {"api-key": "custom-unstructured-secret"},
        "headers": {"Authorization": "Bearer abcdefghijklmnop"},
    }

    sanitized = redact_sensitive_data(payload)

    assert sanitized["job_id"] == "job-1"
    assert sanitized["provider"]["api-key"] == "[redacted]"
    assert sanitized["headers"]["Authorization"] == "[redacted]"

"""Public error responses must not expose infrastructure details."""

from app.core.errors import public_http_detail


def test_server_errors_are_always_stable() -> None:
    detail = public_http_detail(500, "psycopg2 connection failed password=secret")
    assert detail == {"code": "INTERNAL_ERROR", "message": "服务器内部错误"}


def test_technical_client_error_is_sanitized() -> None:
    detail = public_http_detail(
        400,
        'ProgrammingError: column users.preferences does not exist [SQL: SELECT ...]',
    )
    assert detail == {"code": "REQUEST_FAILED", "message": "请求处理失败"}


def test_business_client_error_is_preserved() -> None:
    assert public_http_detail(400, "设备编号已存在") == "设备编号已存在"

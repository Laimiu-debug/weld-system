import socket

import pytest

from app.core.html_security import sanitize_document_html
from app.core.remote_content import fetch_public_image, safe_weasyprint_url_fetcher
from app.schemas.wps import WPSUpdate


def test_document_html_removes_active_content() -> None:
    cleaned = sanitize_document_html(
        '<table onclick="alert(1)"><tr><td>ok</td></tr></table>'
        '<script>alert(1)</script><img src="javascript:alert(1)">'
    )

    assert cleaned is not None
    assert "<table" in cleaned
    assert "onclick" not in cleaned
    assert "script" not in cleaned
    assert "javascript:" not in cleaned


def test_wps_update_sanitizes_document_html() -> None:
    payload = WPSUpdate(document_html='<p onmouseover="alert(1)">safe</p>')

    assert payload.document_html == "<p>safe</p>"


def test_remote_image_fetch_blocks_private_addresses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))],
    )

    with pytest.raises(ValueError, match="Private"):
        fetch_public_image("http://example.test/image.png")


def test_weasyprint_fetcher_rejects_file_urls() -> None:
    with pytest.raises(ValueError, match="HTTP"):
        safe_weasyprint_url_fetcher("file:///etc/passwd")

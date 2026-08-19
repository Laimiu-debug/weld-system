"""Restricted remote image fetching for document exports."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import requests

MAX_REMOTE_IMAGE_BYTES = 10 * 1024 * 1024
MAX_REDIRECTS = 3


def _validate_public_http_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only public HTTP(S) image URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in image URLs are not allowed")

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                parsed.hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
            )
        }
    except socket.gaierror as exc:
        raise ValueError("Image host could not be resolved") from exc
    if not addresses:
        raise ValueError("Image host did not resolve")

    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError("Private, local, reserved, or multicast image hosts are blocked")


def fetch_public_image(url: str) -> tuple[bytes, str, str]:
    current_url = url
    with requests.Session() as session:
        session.trust_env = False
        for _ in range(MAX_REDIRECTS + 1):
            _validate_public_http_url(current_url)
            with session.get(
                current_url,
                allow_redirects=False,
                stream=True,
                timeout=(3, 10),
                headers={"User-Agent": "weldsystem-document-export/1.0"},
            ) as response:
                if response.is_redirect or response.is_permanent_redirect:
                    location = response.headers.get("Location")
                    if not location:
                        raise ValueError("Image redirect has no location")
                    current_url = urljoin(current_url, location)
                    continue
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
                if not content_type.startswith("image/"):
                    raise ValueError("Remote document asset is not an image")
                declared_size = int(response.headers.get("Content-Length", "0") or 0)
                if declared_size > MAX_REMOTE_IMAGE_BYTES:
                    raise ValueError("Remote image exceeds the 10 MiB limit")
                chunks: list[bytes] = []
                total = 0
                for chunk in response.iter_content(64 * 1024):
                    total += len(chunk)
                    if total > MAX_REMOTE_IMAGE_BYTES:
                        raise ValueError("Remote image exceeds the 10 MiB limit")
                    chunks.append(chunk)
                return b"".join(chunks), content_type, current_url
    raise ValueError("Remote image redirected too many times")


def safe_weasyprint_url_fetcher(url: str) -> dict[str, object]:
    if url.startswith("data:image/"):
        from weasyprint import default_url_fetcher

        return default_url_fetcher(url)
    content, content_type, final_url = fetch_public_image(url)
    return {"string": content, "mime_type": content_type, "redirected_url": final_url}

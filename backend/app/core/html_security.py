"""Sanitization primitives for user-editable document HTML."""
from __future__ import annotations

from typing import Annotated, Optional

import bleach
from bleach.css_sanitizer import CSSSanitizer
from pydantic import BeforeValidator

MAX_DOCUMENT_HTML_BYTES = 2 * 1024 * 1024

_ALLOWED_TAGS = {
    "a", "b", "blockquote", "br", "caption", "code", "col", "colgroup",
    "div", "em", "figcaption", "figure", "h1", "h2", "h3", "h4", "h5",
    "h6", "hr", "i", "img", "li", "ol", "p", "pre", "s", "span", "strong",
    "sub", "sup", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "u",
    "ul",
}
_ALLOWED_ATTRIBUTES = {
    "*": ["class", "style", "title"],
    "a": ["href", "target", "rel"],
    "img": ["src", "alt", "width", "height"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan", "scope"],
    "col": ["span", "width"],
}
_CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties=[
        "background-color", "border", "border-bottom", "border-collapse",
        "border-color", "border-left", "border-right", "border-style", "border-top",
        "border-width", "color", "display", "font-family", "font-size", "font-style",
        "font-weight", "height", "line-height", "margin", "margin-bottom", "margin-left",
        "margin-right", "margin-top", "max-width", "min-width", "padding",
        "padding-bottom", "padding-left", "padding-right", "padding-top", "text-align",
        "text-decoration", "vertical-align", "white-space", "width",
    ]
)


def sanitize_document_html(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("document_html must be a string")
    if len(value.encode("utf-8")) > MAX_DOCUMENT_HTML_BYTES:
        raise ValueError("document_html exceeds the 2 MiB limit")
    return bleach.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "data", "mailto"},
        css_sanitizer=_CSS_SANITIZER,
        strip=True,
        strip_comments=True,
    )


SanitizedDocumentHTML = Annotated[Optional[str], BeforeValidator(sanitize_document_html)]

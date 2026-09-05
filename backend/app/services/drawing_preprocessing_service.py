"""Orientation and region preparation for dense engineering drawings."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from math import atan2, degrees, isfinite
from typing import Any

from PIL import Image
from pypdf import PdfReader


MAX_AI_DRAWING_EDGE = 4096


@dataclass(frozen=True)
class PreparedDrawingPage:
    page_number: int
    rotation_degrees: int
    full_png: bytes
    title_png: bytes
    original_size: tuple[int, int]
    oriented_size: tuple[int, int]
    title_box: tuple[int, int, int, int]
    source_region: tuple[float, float, float, float] = (0, 0, 1, 1)


def pdf_text_rotation(stream, page_number: int) -> int:
    """Rotate only when embedded text gives a strong, explicit reading direction."""
    try:
        page = PdfReader(stream).pages[page_number - 1]
        weights = Counter()
        page_rotation = int(page.get("/Rotate", 0))

        def visit(value, cm, tm, font, size):
            count = len("".join(value.split()))
            a = tm[0] * cm[0] + tm[1] * cm[2]
            b = tm[0] * cm[1] + tm[1] * cm[3]
            angle = (degrees(atan2(b, a)) - page_rotation) % 360
            nearest = round(angle / 90) * 90 % 360
            if min(abs(angle - nearest), 360 - abs(angle - nearest)) <= 3:
                weights[nearest] += count

        page.extract_text(visitor_text=visit)
        angle, count = weights.most_common(1)[0]
        return (
            (-angle) % 360
            if count >= 40 and count / sum(weights.values()) >= 0.85
            else 0
        )
    except Exception:
        return 0


def prepare_drawing_page(
    png: bytes,
    page_number: int,
    *,
    rotation_degrees: int = 0,
    region: list[float] | None = None,
) -> PreparedDrawingPage:
    """Orient a drawing and isolate the conventional bottom-right title region."""
    with Image.open(BytesIO(png)) as source:
        original = source.convert("RGB")
    # Ink density is not evidence of reading direction: a dense upper-left
    # assembly used to turn a correctly oriented sheet upside down.
    if rotation_degrees not in {0, 90, 180, 270}:
        raise ValueError("Invalid drawing rotation")
    rotation = rotation_degrees
    source_region = (0, 0, 1, 1)
    working = original
    if region is not None:
        if not _valid_bbox(region):
            raise ValueError("Invalid drawing region")
        width, height = original.size
        box = (
            int(region[0] * width),
            int(region[1] * height),
            int(region[2] * width),
            int(region[3] * height),
        )
        if box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError("Drawing region is smaller than one pixel")
        working = original.crop(box)
        source_region = (
            box[0] / width,
            box[1] / height,
            box[2] / width,
            box[3] / height,
        )
    oriented = working.rotate(rotation, expand=True)
    if max(oriented.size) > MAX_AI_DRAWING_EDGE:
        oriented.thumbnail(
            (MAX_AI_DRAWING_EDGE, MAX_AI_DRAWING_EDGE), Image.Resampling.LANCZOS
        )
    width, height = oriented.size
    title_box = (
        int(width * 0.56),
        int(height * 0.46),
        width,
        height,
    )
    title = oriented.crop(title_box)
    return PreparedDrawingPage(
        page_number=page_number,
        rotation_degrees=rotation,
        full_png=_png_bytes(oriented),
        title_png=_png_bytes(title),
        original_size=original.size,
        oriented_size=oriented.size,
        title_box=title_box,
        source_region=source_region,
    )


def restore_payload_evidence(
    payload: dict[str, Any],
    pages: list[PreparedDrawingPage],
    *,
    title_crop_sections: frozenset[str] = frozenset({"product"}),
) -> dict[str, Any]:
    """Map model boxes from oriented/cropped images back to source-page space."""
    by_page = {page.page_number: page for page in pages}
    product = payload.get("product") or {}
    for evidence in (product.get("evidence") or {}).values():
        _restore_evidence(
            evidence, by_page, title_crop="product" in title_crop_sections
        )
    for section in ("parts", "weld_joints", "unresolved_regions"):
        for item in payload.get(section) or []:
            _restore_evidence(
                item.get("evidence"),
                by_page,
                title_crop=section in title_crop_sections,
            )
    return payload


def _restore_evidence(
    evidence: Any,
    pages: dict[int, PreparedDrawingPage],
    *,
    title_crop: bool,
) -> None:
    if not isinstance(evidence, dict):
        return
    page = pages.get(evidence.get("page"))
    bbox = evidence.get("bbox")
    if page is None:
        evidence["page"], evidence["bbox"] = None, None
        return
    if not _valid_bbox(bbox):
        evidence["bbox"] = None
        return
    x1, y1, x2, y2 = (float(value) for value in bbox)
    if title_crop:
        left, top, right, bottom = page.title_box
        width, height = page.oriented_size
        x1, x2 = (
            (left + x1 * (right - left)) / width,
            (left + x2 * (right - left)) / width,
        )
        y1, y2 = (
            (top + y1 * (bottom - top)) / height,
            (top + y2 * (bottom - top)) / height,
        )
    restored = _inverse_rotation_bbox([x1, y1, x2, y2], page.rotation_degrees)
    left, top, right, bottom = page.source_region
    evidence["bbox"] = [
        left + restored[0] * (right - left),
        top + restored[1] * (bottom - top),
        left + restored[2] * (right - left),
        top + restored[3] * (bottom - top),
    ]


def _inverse_rotation_bbox(bbox: list[float], degrees: int) -> list[float]:
    x1, y1, x2, y2 = bbox
    corners = [(x1, y1), (x1, y2), (x2, y1), (x2, y2)]
    if degrees == 90:
        restored = [(1 - y, x) for x, y in corners]
    elif degrees == 180:
        restored = [(1 - x, 1 - y) for x, y in corners]
    elif degrees == 270:
        restored = [(y, 1 - x) for x, y in corners]
    else:
        restored = corners
    xs = [point[0] for point in restored]
    ys = [point[1] for point in restored]
    return [min(xs), min(ys), max(xs), max(ys)]


def _valid_bbox(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(
            isinstance(item, (int, float))
            and not isinstance(item, bool)
            and isfinite(item)
            for item in value
        )
        and 0 <= value[0] < value[2] <= 1
        and 0 <= value[1] < value[3] <= 1
    )


def _png_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()

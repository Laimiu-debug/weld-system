"""Render private source-document pages for OCR without creating public previews."""
from __future__ import annotations

from io import BytesIO
import math
from pathlib import Path
from typing import BinaryIO

from PIL import Image

from app.services.document_parser_service import DocumentParseError, MAX_IMAGE_PIXELS


VISUAL_RENDER_SUFFIXES = {".pdf", ".dxf", ".dwg", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
MAX_RENDER_EDGE = 6000


def supports_visual_render(original_filename: str) -> bool:
    """Return whether a source file can be rasterized for vision OCR/preview."""
    return Path(original_filename).suffix.lower() in VISUAL_RENDER_SUFFIXES


class DocumentPageRenderer:
    def render_png(
        self,
        stream: BinaryIO,
        original_filename: str,
        page_number: int,
        *,
        scale: float = 2.0,
    ) -> bytes:
        if type(page_number) is not int or page_number < 1:
            raise DocumentParseError("页码无效")
        if type(scale) not in (int, float) or not 1.0 <= scale <= 4.0:
            raise DocumentParseError("页面渲染倍率无效")
        suffix = Path(original_filename).suffix.lower()
        if not supports_visual_render(original_filename):
            raise DocumentParseError("该文档页面不支持视觉 OCR")
        if suffix == ".pdf":
            return self._render_pdf(stream, page_number, scale)
        if suffix in {".dxf", ".dwg"}:
            from app.services.cad_conversion_service import cad_to_pdf
            return self._render_pdf(BytesIO(cad_to_pdf(stream, original_filename)), page_number, scale)
        if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
            return self._render_image(stream, page_number)
        raise DocumentParseError("该文档页面不支持视觉 OCR")

    def _render_pdf(
        self, stream: BinaryIO, page_number: int, scale: float
    ) -> bytes:
        try:
            import pypdfium2 as pdfium
        except ImportError as exc:
            raise DocumentParseError("服务器缺少 PDF 页面渲染组件") from exc
        data = stream.read()
        try:
            document = pdfium.PdfDocument(data)
            try:
                if page_number > len(document):
                    raise DocumentParseError("PDF 页码超出范围")
                page = document[page_number - 1]
                try:
                    width, height = page.get_size()
                    if any(not math.isfinite(value) or value <= 0 for value in (width, height)):
                        raise DocumentParseError("PDF 页面尺寸无效")
                    # Bound raster allocation BEFORE rendering large CAD sheets.
                    effective_scale = min(
                        scale, MAX_RENDER_EDGE / max(width, height),
                    )
                    pixel_width = math.ceil(width * effective_scale)
                    pixel_height = math.ceil(height * effective_scale)
                    if pixel_width * pixel_height > MAX_IMAGE_PIXELS:
                        raise DocumentParseError("页面像素尺寸超过系统安全限制")
                    bitmap = page.render(scale=effective_scale)
                    try:
                        with bitmap.to_pil() as image:
                            return _image_to_png(image)
                    finally:
                        bitmap.close()
                finally:
                    page.close()
            finally:
                document.close()
        except DocumentParseError:
            raise
        except Exception as exc:
            raise DocumentParseError("PDF 页面渲染失败") from exc

    def _render_image(self, stream: BinaryIO, page_number: int) -> bytes:
        try:
            with Image.open(stream) as image:
                frame_count = getattr(image, "n_frames", 1)
                if page_number > frame_count:
                    raise DocumentParseError("图片页码超出范围")
                image.seek(page_number - 1)
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise DocumentParseError("页面像素尺寸超过系统安全限制")
                with image.convert("RGB") as converted:
                    return _image_to_png(converted)
        except DocumentParseError:
            raise
        except Exception as exc:
            raise DocumentParseError("扫描图片无法读取") from exc


def _image_to_png(image: Image.Image) -> bytes:
    if image.width * image.height > MAX_IMAGE_PIXELS:
        raise DocumentParseError("页面像素尺寸超过系统安全限制")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()

"""Render private source-document pages for OCR without creating public previews."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from PIL import Image

from app.services.document_parser_service import DocumentParseError, MAX_IMAGE_PIXELS


class DocumentPageRenderer:
    def render_png(
        self, stream: BinaryIO, original_filename: str, page_number: int
    ) -> bytes:
        if page_number < 1:
            raise DocumentParseError("页码无效")
        suffix = Path(original_filename).suffix.lower()
        if suffix == ".pdf":
            return self._render_pdf(stream, page_number)
        if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
            return self._render_image(stream, page_number)
        raise DocumentParseError("该文档页面不支持视觉 OCR")

    def _render_pdf(self, stream: BinaryIO, page_number: int) -> bytes:
        try:
            import pypdfium2 as pdfium
        except ImportError as exc:
            raise DocumentParseError("服务器缺少 PDF 页面渲染组件") from exc
        data = stream.read()
        try:
            document = pdfium.PdfDocument(data)
            if page_number > len(document):
                raise DocumentParseError("PDF 页码超出范围")
            page = document[page_number - 1]
            bitmap = page.render(scale=2.0)
            image = bitmap.to_pil()
            return _image_to_png(image)
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
                return _image_to_png(image.convert("RGB"))
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

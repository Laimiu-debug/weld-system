from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from PIL import Image
from reportlab.pdfgen import canvas

from app.services.document_page_renderer import DocumentPageRenderer
from app.services.document_parser_service import DocumentParseError


def test_a0_drawing_is_bounded_before_raster_allocation() -> None:
    source = BytesIO()
    pdf = canvas.Canvas(source, pagesize=(2384, 3370))
    pdf.drawString(100, 3000, "W1: A0 welding layout")
    pdf.save()
    source.seek(0)
    rendered = DocumentPageRenderer().render_png(source, "A0.pdf", 1, scale=3)
    with Image.open(BytesIO(rendered)) as image:
        assert max(image.size) <= 6001
        assert image.width * image.height < 50_000_000


def test_pdf_page_renders_to_private_png_bytes() -> None:
    source = BytesIO()
    pdf = canvas.Canvas(source)
    pdf.drawString(72, 720, "PQR-001")
    pdf.save()
    source.seek(0)

    rendered = DocumentPageRenderer().render_png(source, "PQR.pdf", 1)

    assert rendered.startswith(b"\x89PNG\r\n\x1a\n")
    with Image.open(BytesIO(rendered)) as image:
        assert image.width > 500
        assert image.height > 500


def test_pdf_page_supports_higher_resolution_for_dense_drawings() -> None:
    source = BytesIO()
    pdf = canvas.Canvas(source)
    pdf.drawString(72, 720, "DRAWING-001")
    pdf.save()
    source.seek(0)

    normal = DocumentPageRenderer().render_png(source, "drawing.pdf", 1)
    source.seek(0)
    detailed = DocumentPageRenderer().render_png(
        source, "drawing.pdf", 1, scale=3.0
    )

    with Image.open(BytesIO(normal)) as normal_image:
        with Image.open(BytesIO(detailed)) as detailed_image:
            assert detailed_image.width > normal_image.width
            assert detailed_image.height > normal_image.height


def test_tiff_frame_selection_renders_requested_page() -> None:
    source = BytesIO()
    first = Image.new("RGB", (20, 20), "white")
    second = Image.new("RGB", (30, 40), "black")
    first.save(source, format="TIFF", save_all=True, append_images=[second])
    source.seek(0)

    rendered = DocumentPageRenderer().render_png(source, "scan.tiff", 2)

    with Image.open(BytesIO(rendered)) as image:
        assert image.size == (30, 40)


@pytest.mark.parametrize("page_number", [0, -1, True, 1.5, "1"])
def test_invalid_page_number_is_rejected_before_opening_document(page_number):
    with pytest.raises(DocumentParseError, match="页码无效"):
        DocumentPageRenderer().render_png(BytesIO(b"invalid"), "drawing.pdf", page_number)


@pytest.mark.parametrize("scale", [True, None, "2", float("nan"), float("inf"), 0.5, 5])
def test_invalid_scale_is_reported_as_input_error(scale):
    with pytest.raises(DocumentParseError, match="倍率无效"):
        DocumentPageRenderer().render_png(BytesIO(b"invalid"), "drawing.pdf", 1, scale=scale)


def _pdf_document(page_size):
    page = Mock()
    page.get_size.return_value = page_size
    document = Mock()
    document.__len__ = Mock(return_value=1)
    document.__getitem__ = Mock(return_value=page)
    return document, page


@pytest.mark.parametrize("size", [(0, 100), (100, -1), (float("nan"), 100), (100, float("inf"))])
def test_invalid_pdf_dimensions_fail_before_allocating_bitmap(size):
    document, page = _pdf_document(size)
    with patch("pypdfium2.PdfDocument", return_value=document):
        with pytest.raises(DocumentParseError, match="页面尺寸无效"):
            DocumentPageRenderer().render_png(BytesIO(b"pdf"), "drawing.pdf", 1)
    page.render.assert_not_called()
    page.close.assert_called_once()
    document.close.assert_called_once()


def test_out_of_range_pdf_page_releases_document():
    document, page = _pdf_document((100, 100))
    with patch("pypdfium2.PdfDocument", return_value=document):
        with pytest.raises(DocumentParseError, match="页码超出范围"):
            DocumentPageRenderer().render_png(BytesIO(b"pdf"), "drawing.pdf", 2)
    page.render.assert_not_called()
    document.close.assert_called_once()


def test_png_encoding_failure_releases_native_pdf_resources():
    document, page = _pdf_document((100, 100))
    bitmap = page.render.return_value
    bitmap.to_pil.return_value = Image.new("RGB", (100, 100))
    with patch("pypdfium2.PdfDocument", return_value=document):
        with patch("app.services.document_page_renderer._image_to_png", side_effect=ValueError("encoding failed")):
            with pytest.raises(DocumentParseError, match="页面渲染失败"):
                DocumentPageRenderer().render_png(BytesIO(b"pdf"), "drawing.pdf", 1)
    bitmap.close.assert_called_once()
    page.close.assert_called_once()
    document.close.assert_called_once()


def test_requested_image_frame_is_size_checked_before_rgb_decode():
    source = BytesIO()
    Image.new("RGB", (10, 10)).save(source, "TIFF", save_all=True, append_images=[Image.new("RGB", (30, 40))])
    source.seek(0)
    with patch("app.services.document_page_renderer.MAX_IMAGE_PIXELS", 1000):
        with patch.object(Image.Image, "convert", side_effect=AssertionError("decoded oversized frame")):
            with pytest.raises(DocumentParseError, match="页面像素尺寸"):
                DocumentPageRenderer().render_png(source, "scan.tiff", 2)


def test_mixed_a1_and_extreme_aspect_pdf_pages_remain_bounded():
    source = BytesIO()
    pdf = canvas.Canvas(source, pagesize=(1684, 2384))
    pdf.drawString(10, 100, "A1")
    pdf.showPage()
    pdf.setPageSize((100000, 100))
    pdf.drawString(10, 50, "Wide drawing")
    pdf.save()
    for page_number in (1, 2):
        source.seek(0)
        rendered = DocumentPageRenderer().render_png(source, "mixed.pdf", page_number, scale=4)
        with Image.open(BytesIO(rendered)) as image:
            assert 0 < image.width <= 6001
            assert 0 < image.height <= 6001
            assert image.width * image.height <= 50_000_000

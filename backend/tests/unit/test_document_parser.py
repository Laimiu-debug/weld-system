from io import BytesIO

import pytest
from docx import Document
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.services.document_parser_service import (
    DefaultDocumentParser,
    DocumentParseError,
)
from app.services import document_parser_service


def _text_pdf() -> BytesIO:
    stream = BytesIO()
    pdf = canvas.Canvas(stream)
    pdf.drawString(72, 760, "WPS No. WPS-001 welding procedure")
    pdf.showPage()
    pdf.drawString(72, 760, "PQR No. PQR-001 qualification record")
    pdf.save()
    stream.seek(0)
    return stream


def _scanned_pdf() -> BytesIO:
    stream = BytesIO()
    pdf = canvas.Canvas(stream)
    pdf.drawInlineImage(Image.new("RGB", (120, 80), "white"), 72, 650)
    pdf.save()
    stream.seek(0)
    return stream


def test_pdf_embedded_text_is_split_by_physical_page() -> None:
    parsed = DefaultDocumentParser().parse(_text_pdf(), "WPS.pdf")

    assert parsed.parser == "pypdf"
    assert parsed.page_numbering == "physical"
    assert [page.page_number for page in parsed.pages] == [1, 2]
    assert "WPS-001" in parsed.pages[0].text_content
    assert "PQR-001" in parsed.pages[1].text_content
    assert all(page.ocr_status == "not_required" for page in parsed.pages)


def test_image_only_pdf_is_marked_for_later_ocr() -> None:
    parsed = DefaultDocumentParser().parse(_scanned_pdf(), "scan.pdf")

    assert len(parsed.pages) == 1
    assert parsed.pages[0].ocr_status == "pending"
    assert parsed.pages[0].metadata["has_images"] is True
    assert parsed.pages[0].metadata["is_scanned_candidate"] is True


def test_xobject_image_pdf_is_also_marked_for_later_ocr() -> None:
    image_stream = BytesIO()
    Image.new("RGB", (120, 80), "white").save(image_stream, format="PNG")
    image_stream.seek(0)
    stream = BytesIO()
    pdf = canvas.Canvas(stream)
    pdf.drawImage(ImageReader(image_stream), 72, 650, width=120, height=80)
    pdf.save()
    stream.seek(0)

    parsed = DefaultDocumentParser().parse(stream, "xobject-scan.pdf")

    assert parsed.pages[0].ocr_status == "pending"


def test_docx_uses_explicit_page_breaks_and_keeps_table_text() -> None:
    stream = BytesIO()
    document = Document()
    document.add_paragraph("WPS No. WPS-002")
    document.add_page_break()
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Base metal"
    table.cell(0, 1).text = "Q345R"
    document.save(stream)
    stream.seek(0)

    parsed = DefaultDocumentParser().parse(stream, "WPS.docx")

    assert parsed.page_numbering == "logical"
    assert len(parsed.pages) == 2
    assert "WPS-002" in parsed.pages[0].text_content
    assert "Base metal\tQ345R" in parsed.pages[1].text_content
    assert all(page.ocr_status == "not_required" for page in parsed.pages)


def test_multipage_tiff_creates_one_ocr_page_per_frame() -> None:
    stream = BytesIO()
    first = Image.new("RGB", (20, 30), "white")
    second = Image.new("RGB", (40, 50), "white")
    first.save(stream, format="TIFF", save_all=True, append_images=[second])
    stream.seek(0)

    parsed = DefaultDocumentParser().parse(stream, "welder-card.tiff")

    assert len(parsed.pages) == 2
    assert [page.ocr_status for page in parsed.pages] == ["pending", "pending"]
    assert parsed.pages[1].metadata["width_pixels"] == 40


def test_legacy_doc_requires_conversion() -> None:
    with pytest.raises(DocumentParseError, match="转换为 DOCX 或 PDF"):
        DefaultDocumentParser().parse(BytesIO(b"legacy"), "legacy.doc")


def test_docx_archive_expansion_limit_is_enforced(monkeypatch) -> None:
    stream = BytesIO()
    document = Document()
    document.add_paragraph("PQR")
    document.save(stream)
    stream.seek(0)
    monkeypatch.setattr(document_parser_service, "MAX_DOCX_UNCOMPRESSED_BYTES", 1)

    with pytest.raises(DocumentParseError, match="解压后大小"):
        DefaultDocumentParser().parse(stream, "PQR.docx")

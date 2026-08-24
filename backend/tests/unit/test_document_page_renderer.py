from io import BytesIO

from PIL import Image
from reportlab.pdfgen import canvas

from app.services.document_page_renderer import DocumentPageRenderer


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

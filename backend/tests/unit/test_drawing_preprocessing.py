from io import BytesIO

from PIL import Image, ImageDraw

from app.services.drawing_preprocessing_service import (
    MAX_AI_DRAWING_EDGE,
    prepare_drawing_page,
    restore_payload_evidence,
    pdf_text_rotation,
)
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter


def test_embedded_text_direction_corrects_rotated_cad_but_not_ink_density():
    data = BytesIO()
    pdf = canvas.Canvas(data)
    pdf.translate(100, 400)
    pdf.rotate(-90)
    pdf.drawString(0, 0, "Drawing-2026 " * 8)
    pdf.save()
    assert pdf_text_rotation(BytesIO(data.getvalue()), 1) == 90
    image = Image.new("RGB", (200, 300), "white")
    prepared = prepare_drawing_page(_png(image), 1, rotation_degrees=90)
    assert prepared.oriented_size == (300, 200)
    value = {"parts": [{"evidence": {"page": 1, "bbox": [0.1, 0.2, 0.3, 0.4]}}]}
    restore_payload_evidence(value, [prepared])
    assert value["parts"][0]["evidence"]["bbox"] == [0.6, 0.1, 0.8, 0.3]


def test_pdf_page_rotation_is_included_in_reading_direction():
    data = BytesIO()
    pdf = canvas.Canvas(data)
    pdf.drawString(20, 20, "Drawing-2026 " * 8)
    pdf.save()
    page = PdfReader(BytesIO(data.getvalue())).pages[0]
    page.rotate(90)
    writer = PdfWriter()
    writer.add_page(page)
    rotated = BytesIO()
    writer.write(rotated)
    assert pdf_text_rotation(BytesIO(rotated.getvalue()), 1) == 90


def test_ambiguous_or_missing_text_does_not_guess_rotation():
    assert pdf_text_rotation(BytesIO(b"not a PDF"), 1) == 0
    data = BytesIO()
    pdf = canvas.Canvas(data)
    for angle in [0, 90]:
        pdf.saveState()
        pdf.rotate(angle)
        pdf.drawString(10, 10, "Equal text " * 8)
        pdf.restoreState()
    pdf.save()
    assert pdf_text_rotation(BytesIO(data.getvalue()), 1) == 0


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_ink_density_does_not_override_source_reading_direction() -> None:
    drawing = Image.new("RGB", (1200, 800), "white")
    pen = ImageDraw.Draw(drawing)
    pen.rectangle((10, 10, 1190, 790), outline="black", width=4)
    for x in range(780, 1190, 50):
        pen.line((x, 520, x, 790), fill="black", width=3)
    for y in range(520, 790, 40):
        pen.line((780, y, 1190, y), fill="black", width=3)
    portrait = drawing.rotate(270, expand=True)

    prepared = prepare_drawing_page(_png(portrait), 1)

    assert prepared.oriented_size == portrait.size
    assert prepared.rotation_degrees == 0
    with Image.open(BytesIO(prepared.full_png)) as full:
        assert full.tobytes() == portrait.tobytes()
    with Image.open(BytesIO(prepared.title_png)) as title:
        assert title.width > 300
        assert title.height > 300


def test_title_crop_evidence_is_restored_to_source_coordinates() -> None:
    drawing = Image.new("RGB", (1200, 800), "white")
    prepared = prepare_drawing_page(_png(drawing), 1)
    payload = {
        "product": {
            "evidence": {
                "drawing_number": {
                    "page": 1,
                    "bbox": [0.0, 0.0, 1.0, 1.0],
                    "text": "D-001",
                }
            }
        },
        "parts": [],
        "weld_joints": [],
        "unresolved_regions": [],
    }

    restore_payload_evidence(payload, [prepared])

    bbox = payload["product"]["evidence"]["drawing_number"]["bbox"]
    assert all(0 <= value <= 1 for value in bbox)
    assert bbox[0] < bbox[2]
    assert bbox[1] < bbox[3]


def test_large_drawing_is_bounded_before_it_is_sent_to_ai() -> None:
    drawing = Image.new("RGB", (MAX_AI_DRAWING_EDGE + 1000, 1000), "white")

    prepared = prepare_drawing_page(_png(drawing), 1)

    assert max(prepared.oriented_size) == MAX_AI_DRAWING_EDGE
    with Image.open(BytesIO(prepared.full_png)) as full:
        assert max(full.size) == MAX_AI_DRAWING_EDGE


def test_full_page_title_evidence_is_not_mapped_as_a_crop():
    prepared = prepare_drawing_page(_png(Image.new("RGB", (1200, 800), "white")), 1)
    box = [0.1, 0.2, 0.4, 0.3]
    payload = {
        "product": {"evidence": {"drawing_number": {"page": 1, "bbox": box.copy()}}}
    }
    restore_payload_evidence(payload, [prepared], title_crop_sections=frozenset())
    assert payload["product"]["evidence"]["drawing_number"]["bbox"] == box

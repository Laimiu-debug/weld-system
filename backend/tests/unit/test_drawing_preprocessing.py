from io import BytesIO

from PIL import Image, ImageDraw

from app.services.drawing_preprocessing_service import (
    MAX_AI_DRAWING_EDGE,
    prepare_drawing_page,
    restore_payload_evidence,
)


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
    payload = {"product": {"evidence": {"drawing_number": {"page": 1, "bbox": box.copy()}}}}
    restore_payload_evidence(payload, [prepared], title_crop_sections=frozenset())
    assert payload["product"]["evidence"]["drawing_number"]["bbox"] == box

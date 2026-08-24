from io import BytesIO

from PIL import Image, ImageDraw

from app.services.drawing_preprocessing_service import (
    prepare_drawing_page,
    restore_payload_evidence,
)


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_portrait_raster_is_rotated_to_landscape_title_layout() -> None:
    drawing = Image.new("RGB", (1200, 800), "white")
    pen = ImageDraw.Draw(drawing)
    pen.rectangle((10, 10, 1190, 790), outline="black", width=4)
    for x in range(780, 1190, 50):
        pen.line((x, 520, x, 790), fill="black", width=3)
    for y in range(520, 790, 40):
        pen.line((780, y, 1190, y), fill="black", width=3)
    portrait = drawing.rotate(270, expand=True)

    prepared = prepare_drawing_page(_png(portrait), 1)

    assert prepared.oriented_size[0] > prepared.oriented_size[1]
    assert prepared.rotation_degrees == 90
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

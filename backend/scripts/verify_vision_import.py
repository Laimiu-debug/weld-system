"""Opt-in live smoke test using synthetic drawings/PQR, without database writes.

Run from backend: python scripts/verify_vision_import.py
Set VISION_TEST_BASE_URL, VISION_TEST_MODEL and VISION_TEST_API_KEY in the
process environment. Never put credentials in this file.
"""
from io import BytesIO
import base64
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reportlab.pdfgen import canvas
from app.services.ai_provider_service import AIImageInput, AIProviderConfig, OpenAICompatibleProvider, StructuredAIRequest
from app.services.document_page_renderer import DocumentPageRenderer
from app.services.drawing_preprocessing_service import prepare_drawing_page, restore_payload_evidence
from app.services.engineering_service import (
    DRAWING_TITLE_SCHEMA, DRAWING_PARTS_SCHEMA, DRAWING_WELDS_SCHEMA,
    DRAWING_TITLE_INSTRUCTIONS, DRAWING_PARTS_INSTRUCTIONS, DRAWING_WELDS_INSTRUCTIONS,
    validate_drawing_payload,
)
from app.services.ai_extraction_service import OCR_SCHEMA, OCR_INSTRUCTIONS, validate_extraction_result


def image_input(data):
    return AIImageInput("data:image/png;base64," + base64.b64encode(data).decode(), 1)


def main():
    provider = OpenAICompatibleProvider(AIProviderConfig(
        provider="openai_compatible_chat", base_url=os.environ["VISION_TEST_BASE_URL"],
        model=os.environ["VISION_TEST_MODEL"], api_key=os.environ["VISION_TEST_API_KEY"],
        timeout_seconds=90, max_output_tokens=3000,
    ))
    tokens = 0
    try:
        source = BytesIO()
        pdf = canvas.Canvas(source, pagesize=(1200, 800))
        pdf.setFont("Helvetica", 24)
        pdf.rect(100, 300, 950, 400)
        pdf.line(550, 300, 550, 700)
        pdf.drawString(120, 600, "PART A: Plate, Q345R, 12 mm")
        pdf.drawString(590, 520, "PART B: Plate, Q345R, 12 mm")
        pdf.drawString(350, 735, "W1: BUTT WELD, V groove, 60 deg")
        pdf.drawString(700, 110, "DRAWING: TEST-1001")
        pdf.drawString(700, 70, "PRODUCT: Weld Test Panel")
        pdf.save()
        source.seek(0)
        page = prepare_drawing_page(DocumentPageRenderer().render_png(source, "test.pdf", 1, scale=3), 1)
        output = {}
        for schema, instructions, png in [
            (DRAWING_TITLE_SCHEMA, DRAWING_TITLE_INSTRUCTIONS, page.full_png),
            (DRAWING_PARTS_SCHEMA, DRAWING_PARTS_INSTRUCTIONS, page.full_png),
            (DRAWING_WELDS_SCHEMA, DRAWING_WELDS_INSTRUCTIONS, page.full_png),
        ]:
            result = provider.structured_response(StructuredAIRequest(
                instructions, "Source page 1. Previously identified parts: " + json.dumps(output.get("parts", [])),
                schema, [image_input(png)],
            ))
            tokens += result.total_tokens
            validate_drawing_payload(result.data, schema)
            restore_payload_evidence(result.data, [page], title_crop_sections=frozenset())
            output.update(result.data)
        assert output["product"]["drawing_number"] == "TEST-1001"
        assert len(output["parts"]) == 2
        assert output["weld_joints"][0]["weld_number"] == "W1"
        refs = {part["ref"] for part in output["parts"]}
        assert output["weld_joints"][0]["part_a_ref"] in refs
        assert output["weld_joints"][0]["part_b_ref"] in refs
        print("drawing: title, 2 parts, W1 and part references verified", flush=True)

        source = BytesIO()
        pdf = canvas.Canvas(source)
        pdf.setFont("Helvetica", 22)
        for y, text in [(740, "PQR No: PQR-SMOKE-001"), (690, "Base material: Q345R"),
                        (640, "Thickness: 12 mm"), (590, "Welding process: SMAW")]:
            pdf.drawString(60, y, text)
        pdf.save()
        source.seek(0)
        png = DocumentPageRenderer().render_png(source, "PQR.pdf", 1)
        result = provider.structured_response(StructuredAIRequest(
            OCR_INSTRUCTIONS, "Transcribe source page 1", OCR_SCHEMA, [image_input(png)],
        ))
        tokens += result.total_tokens
        validate_extraction_result(OCR_SCHEMA, result.data)
        evidence_schema = {"type": "array", "items": {"type": "object", "properties": {
            "page": {"type": "integer"}, "text": {"type": "string"}},
            "required": ["page", "text"], "additionalProperties": False}}
        properties = {key: {"type": "object", "properties": {
            "value": {"type": kind}, "confidence": {"type": "number"}, "evidence": evidence_schema},
            "required": ["value", "confidence", "evidence"], "additionalProperties": False}
            for key, kind in [("pqr_number", "string"), ("material", "string"), ("thickness_mm", "number"), ("process", "string")]}
        schema = {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
        extracted = provider.structured_response(StructuredAIRequest(
            "Extract only the stated PQR facts. Include exact source text evidence and page 1. Do not guess.",
            result.data["text"], schema,
        ))
        tokens += extracted.total_tokens
        validate_extraction_result(schema, extracted.data)
        actual = {key: item["value"] for key, item in extracted.data.items()}
        assert actual == {"pqr_number": "PQR-SMOKE-001", "material": "Q345R", "thickness_mm": 12, "process": "SMAW"}, actual
        print("PQR: OCR and 4 structured fields verified")
        print(json.dumps({"total_tokens": tokens, "database_writes": False}))
    finally:
        provider.close()


if __name__ == "__main__":
    main()

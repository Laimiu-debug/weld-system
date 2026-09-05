from io import BytesIO, StringIO

import ezdxf
import pytest
from PIL import Image

from app.services.cad_conversion_service import cad_to_pdf
from app.services.document_parser_service import DefaultDocumentParser, DocumentParseError
from app.services.document_page_renderer import DocumentPageRenderer
from app.services.document_storage_service import LocalDocumentStorage


def drawing_bytes() -> bytes:
    doc = ezdxf.new()
    model = doc.modelspace()
    model.add_line((0, 0), (100, 100))
    model.add_text("W1: Q345R 12 mm", dxfattribs={"height": 5})
    stream = StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")


def test_dxf_upload_parse_and_preview_share_real_rendering(tmp_path):
    data = drawing_bytes()
    storage = LocalDocumentStorage(tmp_path)
    saved = storage.save_stream(BytesIO(data), "layout.dxf", 1024 * 1024)
    with storage.open_stream(saved.storage_key) as source:
        parsed = DefaultDocumentParser().parse(source, saved.original_filename)
    assert parsed.parser == "cad_to_pdf"
    assert len(parsed.pages) == 1
    png = DocumentPageRenderer().render_png(BytesIO(data), "layout.dxf", 1)
    with Image.open(BytesIO(png)) as image:
        assert image.width > 100
        assert image.convert("L").getextrema()[0] < 200


def test_dwg_without_converter_has_actionable_error(monkeypatch):
    monkeypatch.setenv("CAD_DWG_CONVERTER", "")
    monkeypatch.setenv("PATH", "")
    with pytest.raises(DocumentParseError, match="DWG 转换器"):
        cad_to_pdf(BytesIO(b"AC1032"), "drawing.dwg")

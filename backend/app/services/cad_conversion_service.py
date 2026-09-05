"""Convert self-contained 2D CAD layouts to private PDF pages."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile


def cad_to_pdf(stream, filename: str) -> bytes:
    from app.services.document_parser_service import DocumentParseError

    with tempfile.TemporaryDirectory(prefix="weld-cad-") as folder:
        source = Path(folder) / ("source" + Path(filename).suffix.lower())
        output = Path(folder) / "drawing.pdf"
        with source.open("wb") as destination:
            shutil.copyfileobj(stream, destination)
        try:
            result = subprocess.run(
                [sys.executable, "-m", __name__, str(source), str(output)],
                capture_output=True, timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except subprocess.TimeoutExpired as exc:
            raise DocumentParseError("CAD 转换超时，请拆分图纸或导出 PDF 后上传") from exc
        if result.returncode or not output.exists():
            # Only expose our own stable diagnostic, never converter stderr.
            code = result.stdout.decode("utf-8", errors="replace").strip()
            messages = {
                "missing_converter": "服务器尚未安装 DWG 转换器，请安装 ODA File Converter 或先将图纸导出为 DXF / PDF",
                "missing_dependency": "服务器缺少 CAD 渲染组件，请安装后端依赖后重试",
                "external_reference": "CAD 包含外部参照或图片，请绑定参照或导出完整 PDF 后上传",
                "unsupported_3d": "仅支持二维焊缝布置图，请将三维 CAD 导出为二维 PDF",
                "empty_drawing": "CAD 中没有可渲染的二维图形",
            }
            raise DocumentParseError(messages.get(code, "CAD 转换失败，请检查文件或导出 PDF 后上传"))
        if output.stat().st_size > 100 * 1024 * 1024:
            raise DocumentParseError("CAD 转换结果过大，请拆分图纸后上传")
        return output.read_bytes()


def _convert(source: Path, output: Path) -> None:
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import BackgroundPolicy, Configuration
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from matplotlib.figure import Figure
    from pypdf import PdfReader, PdfWriter

    if source.suffix == ".dwg":
        converter = os.environ.get("CAD_DWG_CONVERTER") or shutil.which("ODAFileConverter")
        if not converter:
            raise ValueError("missing_converter")
        converted = source.parent / "converted"
        converted.mkdir()
        subprocess.run(
            [converter, str(source.parent), str(converted), "ACAD2018", "DXF", "0", "1", "*.dwg"],
            check=True, capture_output=True, timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        source = converted / "source.dxf"
    document = ezdxf.readfile(source)
    for entity in document.entitydb.values():
        if entity.dxftype() in {"IMAGE", "PDFUNDERLAY", "DWFUNDERLAY", "DGNUNDERLAY"}:
            raise ValueError("external_reference")
        if entity.dxftype() in {"3DSOLID", "BODY", "SURFACE", "REGION"}:
            raise ValueError("unsupported_3d")
    if any(block.block.dxf.flags & 12 for block in document.blocks):
        raise ValueError("external_reference")
    papers = [
        document.layouts.get(name)
        for name in document.layout_names_in_taborder() if name != "Model"
    ]
    papers = [paper for paper in papers if any(
        entity.dxftype() != "VIEWPORT" or entity.dxf.id > 1 for entity in paper
    )]
    layouts = papers or [document.modelspace()]
    if len(layouts) > 50 or not any(len(item) for item in layouts):
        raise ValueError("empty_drawing")
    writer = PdfWriter()
    for layout in layouts:
        figure = Figure(figsize=(16.5, 11.7))
        axes = figure.add_axes([0, 0, 1, 1])
        backend = MatplotlibBackend(axes)
        Frontend(RenderContext(document), backend, config=Configuration(
            background_policy=BackgroundPolicy.WHITE,
        )).draw_layout(layout, finalize=True)
        data = BytesIO()
        figure.savefig(data, format="pdf")
        data.seek(0)
        writer.append(PdfReader(data))
        figure.clear()
    with output.open("wb") as destination:
        writer.write(destination)


if __name__ == "__main__":
    try:
        _convert(Path(sys.argv[1]), Path(sys.argv[2]))
    except ImportError:
        print("missing_dependency")
        sys.exit(1)
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)
    except Exception:
        print("conversion_failed")
        sys.exit(1)

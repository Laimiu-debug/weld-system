"""Local preflight of user samples; no model calls or database writes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.document_parser_service import (
    DefaultDocumentParser,
    DocumentParseError,
)
from app.services.document_page_renderer import (
    DocumentPageRenderer,
    supports_visual_render,
)


def main():
    args = argparse.ArgumentParser()
    args.add_argument("folder", type=Path)
    args.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Private directory outside the repository",
    )
    opts = args.parse_args()
    opts.output.mkdir(parents=True, exist_ok=True)
    report = []
    for path in sorted(opts.folder.iterdir()):
        if not path.is_file():
            continue
        item = {
            "filename": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        try:
            with path.open("rb") as stream:
                parsed = DefaultDocumentParser().parse(stream, path.name)
            item.update(
                parser=parsed.parser,
                pages=len(parsed.pages),
                ocr_pages=[
                    p.page_number for p in parsed.pages if p.ocr_status == "pending"
                ],
                text_chars=[len(p.text_content) for p in parsed.pages],
            )
            if supports_visual_render(path.name):
                for page in parsed.pages:
                    with path.open("rb") as stream:
                        png = DocumentPageRenderer().render_png(
                            stream, path.name, page.page_number, scale=3
                        )
                    target = opts.output / f"{path.stem}-{page.page_number}.png"
                    target.write_bytes(png)
            item["status"] = "parsed"
        except DocumentParseError as exc:
            item.update(status="failed", error=str(exc))
        report.append(item)
    (opts.output / "preflight.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if any(item["status"] == "failed" for item in report) else 0


if __name__ == "__main__":
    sys.exit(main())

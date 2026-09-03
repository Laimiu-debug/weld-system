"""
焊工履历表 PDF 导出
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Tuple
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.data_access import WorkspaceContext
from app.models.user import User
from app.services.welder_service import WelderService

try:
    from weasyprint import HTML
except Exception:  # WeasyPrint may be installed while native Pango libraries are not.
    HTML = None


def _reportlab_font_name() -> str:
    """Register a CJK font available in the container or on Windows."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = (
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf"),
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    )
    for path in candidates:
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("WeldCJK", str(path), subfontIndex=0))
            return "WeldCJK"
        except Exception:
            continue
    # Built-in CID font keeps Chinese readable without an OS font dependency.
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    return "STSong-Light"


def _build_reportlab_pdf(welder: Any, certs: list[dict], histories: list[dict]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font = _reportlab_font_name()
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ResumeTitle", parent=styles["Title"], fontName=font, fontSize=18, alignment=TA_CENTER)
    heading = ParagraphStyle("ResumeHeading", parent=styles["Heading2"], fontName=font, fontSize=12, spaceBefore=10, spaceAfter=5)
    body = ParagraphStyle("ResumeBody", parent=styles["BodyText"], fontName=font, fontSize=9, leading=12)

    def cell(value: Any) -> Paragraph:
        return Paragraph(_esc(value), body)

    def table(rows: list[list[Any]], widths: list[float]) -> Table:
        rendered = [[cell(value) for value in row] for row in rows]
        result = Table(rendered, colWidths=widths, repeatRows=1)
        result.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f3f3")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return result

    name = getattr(welder, "full_name", None) or "-"
    code = getattr(welder, "welder_code", None) or "-"
    story: list[Any] = [
        Paragraph("焊工履历表", title),
        Paragraph(f"{_esc(name)}（{_esc(code)}） · 导出时间 {datetime.now():%Y-%m-%d %H:%M}", body),
        Spacer(1, 5 * mm),
        Paragraph("一、人员信息", heading),
        table([
            ["姓名", name, "编号", code],
            ["部门", getattr(welder, "department", None), "岗位", getattr(welder, "position", None)],
            ["电话", getattr(welder, "phone", None), "状态", getattr(welder, "status", None)],
        ], [24 * mm, 55 * mm, 24 * mm, 55 * mm]),
        Paragraph("二、持证项目（按体系）", heading),
    ]
    cert_rows: list[list[Any]] = [["体系", "持证项目", "证书编号", "发证日", "到期日", "下次审证"]]
    for cert in certs:
        projects = cert.get("projects") or [None]
        for project in projects:
            project = project or {}
            cert_rows.append([
                cert.get("certification_system"),
                project.get("project_name") or project.get("project_code") or cert.get("project_name") or cert.get("certification_type"),
                cert.get("certification_number"),
                project.get("issue_date") or cert.get("issue_date"),
                project.get("expiry_date") or cert.get("expiry_date"),
                project.get("next_renewal_date") or cert.get("next_renewal_date"),
            ])
    if len(cert_rows) == 1:
        cert_rows.append(["暂无持证", "", "", "", "", ""])
    story.append(table(cert_rows, [20 * mm, 40 * mm, 32 * mm, 23 * mm, 23 * mm, 27 * mm]))
    story.append(Paragraph("三、工作履历", heading))
    history_rows: list[list[Any]] = [["单位", "职位", "开始", "结束", "工作内容"]]
    for item in histories or []:
        history_rows.append([
            item.get("company_name"), item.get("position"), item.get("start_date"),
            item.get("end_date") or "至今", item.get("job_description"),
        ])
    if len(history_rows) == 1:
        history_rows.append(["暂无履历", "", "", "", ""])
    story.append(table(history_rows, [40 * mm, 25 * mm, 24 * mm, 24 * mm, 52 * mm]))
    doc.build(story)
    return output.getvalue()


def _esc(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_welder_resume_pdf(
    db: Session,
    welder_id: int,
    current_user: User,
    workspace: WorkspaceContext,
) -> Tuple[bytes, str]:
    service = WelderService(db)
    welder = service.get_welder_by_id(welder_id, current_user, workspace)
    certs, _ = service.get_certifications(welder_id, current_user, workspace)
    histories, _ = service.get_work_histories(
        welder_id=welder_id,
        current_user=current_user,
        workspace_context=workspace,
    )

    cert_rows = []
    for c in certs:
        projects = c.get("projects") or []
        if not projects:
            cert_rows.append(
                f"<tr><td>{_esc(c.get('certification_system'))}</td>"
                f"<td>{_esc(c.get('project_name') or c.get('certification_type'))}</td>"
                f"<td>{_esc(c.get('certification_number'))}</td>"
                f"<td>{_esc(c.get('issue_date'))}</td>"
                f"<td>{_esc(c.get('expiry_date'))}</td>"
                f"<td>{_esc(c.get('next_renewal_date'))}</td></tr>"
            )
            continue
        for p in projects:
            cert_rows.append(
                f"<tr><td>{_esc(c.get('certification_system'))}</td>"
                f"<td>{_esc(p.get('project_name') or p.get('project_code'))}</td>"
                f"<td>{_esc(c.get('certification_number'))}</td>"
                f"<td>{_esc(p.get('issue_date') or c.get('issue_date'))}</td>"
                f"<td>{_esc(p.get('expiry_date'))}</td>"
                f"<td>{_esc(p.get('next_renewal_date'))}</td></tr>"
            )

    hist_rows = []
    for h in histories or []:
        hist_rows.append(
            f"<tr><td>{_esc(h.get('company_name'))}</td>"
            f"<td>{_esc(h.get('position'))}</td>"
            f"<td>{_esc(h.get('start_date'))}</td>"
            f"<td>{_esc(h.get('end_date') or '至今')}</td>"
            f"<td>{_esc(h.get('job_description'))}</td></tr>"
        )

    full_name = getattr(welder, "full_name", "") or ""
    welder_code = getattr(welder, "welder_code", "") or ""
    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
  @page {{ size: A4; margin: 18mm; }}
  body {{ font-family: "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; color: #222; font-size: 12px; }}
  h1 {{ font-size: 20px; margin: 0 0 6px; }}
  h2 {{ font-size: 14px; margin: 18px 0 8px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
  .meta {{ color: #666; margin-bottom: 14px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ border: 1px solid #bbb; padding: 6px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #f3f3f3; }}
</style></head><body>
  <h1>焊工履历表</h1>
  <div class="meta">{_esc(full_name)}（{_esc(welder_code)}） · 导出时间 {_esc(exported_at)}</div>
  <h2>一、人员信息</h2>
  <table>
    <tr><th>姓名</th><td>{_esc(full_name)}</td><th>编号</th><td>{_esc(welder_code)}</td></tr>
    <tr><th>部门</th><td>{_esc(getattr(welder, "department", None))}</td>
        <th>岗位</th><td>{_esc(getattr(welder, "position", None))}</td></tr>
    <tr><th>电话</th><td>{_esc(getattr(welder, "phone", None))}</td>
        <th>状态</th><td>{_esc(getattr(welder, "status", None))}</td></tr>
  </table>
  <h2>二、持证项目（按体系）</h2>
  <table>
    <thead><tr><th>体系</th><th>持证项目</th><th>证书编号</th><th>发证日</th><th>到期日</th><th>下次审证</th></tr></thead>
    <tbody>{''.join(cert_rows) or '<tr><td colspan="6">暂无持证</td></tr>'}</tbody>
  </table>
  <h2>三、工作履历</h2>
  <table>
    <thead><tr><th>单位</th><th>职位</th><th>开始</th><th>结束</th><th>工作内容</th></tr></thead>
    <tbody>{''.join(hist_rows) or '<tr><td colspan="5">暂无履历</td></tr>'}</tbody>
  </table>
</body></html>"""

    if HTML is not None:
        try:
            pdf_bytes = HTML(string=html).write_pdf()
        except Exception:
            # Native-library and pydyf compatibility problems can surface only
            # when rendering starts, so keep the ReportLab path as a runtime
            # fallback rather than limiting it to import-time failures.
            pdf_bytes = _build_reportlab_pdf(welder, certs, histories)
    else:
        pdf_bytes = _build_reportlab_pdf(welder, certs, histories)
    return pdf_bytes, f"焊工履历表-{full_name or welder_id}.pdf"

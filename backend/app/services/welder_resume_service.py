"""
焊工履历表 PDF 导出
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Tuple
from urllib.parse import quote

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.data_access import WorkspaceContext
from app.models.user import User
from app.services.welder_service import WelderService

try:
    from weasyprint import HTML
except ImportError:  # pragma: no cover
    HTML = None


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
    if HTML is None:
        raise ImportError("weasyprint 未安装")

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

    pdf_bytes = HTML(string=html).write_pdf()
    safe_name = quote(f"焊工履历表-{full_name or welder_id}.pdf")
    return pdf_bytes, safe_name

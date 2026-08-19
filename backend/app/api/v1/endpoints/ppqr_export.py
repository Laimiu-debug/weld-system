"""
pPQR文档导出API端点
支持导出为Word和PDF格式
"""
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.document_access import require_document_access
from app.core.rate_limit import enforce_export_limit
from app.models.user import User
from app.models.ppqr import PPQR
from app.services.document_export_service import DocumentExportService

router = APIRouter()


@router.post("/{ppqr_id}/export/word")
def export_ppqr_to_word(
    ppqr_id: int,
    style: str = "blue_white",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出pPQR为Word文档

    Args:
        ppqr_id: pPQR ID
        style: 表格风格，可选值：
            - "blue_white": 蓝白相间风格（默认）
            - "plain": 纯白风格
            - "classic": 经典风格（深蓝标题）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        Word文档文件流
    """
    enforce_export_limit(current_user.id)
    ppqr = require_document_access(db, PPQR, ppqr_id, current_user, "pPQR不存在")

    try:
        export_service = DocumentExportService(db)
        word_stream = export_service.export_ppqr_to_word(ppqr, style=style)

        filename = f"pPQR_{ppqr.ppqr_number}_{datetime.now().strftime('%Y%m%d')}.docx"
        encoded_filename = quote(filename)

        return StreamingResponse(
            word_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="导出Word失败")


@router.post("/{ppqr_id}/export/pdf")
def export_ppqr_to_pdf(
    ppqr_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出pPQR为PDF文档

    Args:
        ppqr_id: pPQR ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        PDF文档文件流
    """
    enforce_export_limit(current_user.id)
    ppqr = require_document_access(db, PPQR, ppqr_id, current_user, "pPQR不存在")

    try:
        export_service = DocumentExportService(db)
        pdf_stream = export_service.export_ppqr_to_pdf(ppqr)

        filename = f"pPQR_{ppqr.ppqr_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
        encoded_filename = quote(filename)

        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="导出PDF失败")

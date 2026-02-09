"""
pPQR文档导出API端点
支持导出为Word和PDF格式
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io
from datetime import datetime
from urllib.parse import quote

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.ppqr import PPQR
from app.services.document_export_service import DocumentExportService

router = APIRouter()


@router.post("/{ppqr_id}/export/word")
async def export_ppqr_to_word(
    ppqr_id: int,
    style: str = "blue_white",  # 默认蓝白相间风格
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
    # 获取pPQR数据
    ppqr = db.query(PPQR).filter(PPQR.id == ppqr_id).first()
    if not ppqr:
        raise HTTPException(status_code=404, detail="pPQR不存在")

    # 检查权限（简化版，实际应该检查用户是否有权限访问此pPQR）
    # TODO: 添加权限检查

    try:
        print(f"[pPQR导出API] 开始导出pPQR ID: {ppqr_id}")
        print(f"[pPQR导出API] pPQR编号: {ppqr.ppqr_number}")
        print(f"[pPQR导出API] pPQR标题: {ppqr.title}")
        print(f"[pPQR导出API] 导出风格: {style}")

        # 使用导出服务生成Word文档
        export_service = DocumentExportService(db)
        word_stream = export_service.export_ppqr_to_word(ppqr, style=style)

        print(f"[pPQR导出API] Word文档生成成功")

        # 生成文件名，使用URL编码处理中文字符
        filename = f"pPQR_{ppqr.ppqr_number}_{datetime.now().strftime('%Y%m%d')}.docx"
        encoded_filename = quote(filename)

        return StreamingResponse(
            word_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        print(f"[pPQR导出API错误] {str(e)}")
        import traceback
        print(f"[pPQR导出API错误] 堆栈跟踪:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导出Word失败: {str(e)}")


@router.post("/{ppqr_id}/export/pdf")
async def export_ppqr_to_pdf(
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
    # 获取pPQR数据
    ppqr = db.query(PPQR).filter(PPQR.id == ppqr_id).first()
    if not ppqr:
        raise HTTPException(status_code=404, detail="pPQR不存在")
    
    # 检查权限
    # TODO: 添加权限检查
    
    try:
        # 使用导出服务生成PDF文档
        export_service = DocumentExportService(db)
        pdf_stream = export_service.export_ppqr_to_pdf(ppqr)

        # 生成文件名，使用URL编码处理中文字符
        filename = f"pPQR_{ppqr.ppqr_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
        encoded_filename = quote(filename)

        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出PDF失败: {str(e)}")


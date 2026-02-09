"""
WPS文档导出API端点
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
from app.models.wps import WPS
from app.services.document_export_service import DocumentExportService

router = APIRouter()


@router.post("/{wps_id}/export/word")
async def export_wps_to_word(
    wps_id: int,
    style: str = "blue_white",  # 默认蓝白相间风格
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出WPS为Word文档

    Args:
        wps_id: WPS ID
        style: 表格风格，可选值：
            - "blue_white": 蓝白相间风格（默认）
            - "plain": 纯白风格
            - "classic": 经典风格（深蓝标题）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        Word文档文件流
    """
    # 获取WPS数据
    wps = db.query(WPS).filter(WPS.id == wps_id).first()
    if not wps:
        raise HTTPException(status_code=404, detail="WPS不存在")

    # 检查权限（简化版，实际应该检查用户是否有权限访问此WPS）
    # TODO: 添加权限检查

    try:
        # 使用导出服务生成Word文档
        export_service = DocumentExportService(db)
        word_stream = export_service.export_wps_to_word(wps, style=style)

        # 生成文件名，使用URL编码处理中文字符
        filename = f"WPS_{wps.wps_number}_{datetime.now().strftime('%Y%m%d')}.docx"
        encoded_filename = quote(filename)

        return StreamingResponse(
            word_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出Word失败: {str(e)}")


@router.post("/{wps_id}/export/pdf")
async def export_wps_to_pdf(
    wps_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出WPS为PDF文档
    
    Args:
        wps_id: WPS ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        PDF文档文件流
    """
    # 获取WPS数据
    wps = db.query(WPS).filter(WPS.id == wps_id).first()
    if not wps:
        raise HTTPException(status_code=404, detail="WPS不存在")
    
    # 检查权限
    # TODO: 添加权限检查
    
    try:
        # 使用导出服务生成PDF文档
        export_service = DocumentExportService(db)
        pdf_stream = export_service.export_wps_to_pdf(wps)

        # 生成文件名，使用URL编码处理中文字符
        filename = f"WPS_{wps.wps_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
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


"""
File upload endpoints for the welding system backend.
"""
import os
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

from app.api import deps
from app.models.user import User
from app.core.config import settings

router = APIRouter()

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/avatar")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    上传用户头像

    Args:
        request: HTTP请求对象
        file: 上传的文件
        current_user: 当前用户
        db: 数据库会话

    Returns:
        上传结果和文件URL

    Raises:
        HTTPException: 如果文件格式不支持或上传失败
    """
    # 检查文件是否为空
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有选择文件"
        )

    # 检查文件扩展名
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式，只支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 检查文件大小
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过5MB"
        )

    # 创建上传目录
    upload_dir = os.path.join(os.getcwd(), "storage", "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一的文件名
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    try:
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        # 构建文件URL
        # 在开发环境中，使用相对路径
        file_url = f"/storage/uploads/avatars/{unique_filename}"

        # 更新用户头像URL
        current_user.avatar_url = file_url
        db.commit()

        print(f"✅ 用户头像上传成功: {current_user.email}, 文件: {unique_filename}")

        return {
            "success": True,
            "message": "头像上传成功",
            "url": file_url,
            "filename": unique_filename
        }

    except Exception as e:
        # 如果上传失败，删除可能已创建的文件
        if os.path.exists(file_path):
            os.remove(file_path)

        print(f"❌ 头像上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"头像上传失败: {str(e)}"
        )

@router.delete("/avatar")
async def delete_avatar(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    删除用户头像

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        删除结果

    Raises:
        HTTPException: 如果删除失败
    """
    try:
        if current_user.avatar_url:
            # 构建文件路径
            filename = current_user.avatar_url.split('/')[-1]
            file_path = os.path.join(os.getcwd(), "storage", "uploads", "avatars", filename)

            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)

            # 更新数据库
            current_user.avatar_url = None
            db.commit()

            print(f"✅ 用户头像删除成功: {current_user.email}")

        return {
            "success": True,
            "message": "头像删除成功"
        }

    except Exception as e:
        print(f"❌ 头像删除失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"头像删除失败: {str(e)}"
        )
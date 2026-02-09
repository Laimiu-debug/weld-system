"""
认证相关功能
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"=== 认证层：验证用户token ===")
    logger.info(f"Token存在: {token is not None}")

    if not token:
        logger.info("未提供token，返回匿名用户")
        return None

    try:
        logger.info("开始解码JWT token...")
        # 解码JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        logger.info(f"解码成功 - 用户ID: {user_id}, Token类型: {token_type}")

        if user_id is None or token_type != "access":
            logger.error(f"Token验证失败 - user_id: {user_id}, token_type: {token_type}")
            return None

        # 从数据库获取用户
        logger.info(f"查询数据库中的用户，ID: {user_id}")
        user = db.query(User).filter(User.id == int(user_id)).first()

        if user:
            logger.info(f"用户验证成功 - ID: {user.id}, 用户名: {user.username}")
        else:
            logger.error(f"数据库中未找到用户，ID: {user_id}")

        return user
    except (JWTError, ValueError, KeyError) as e:
        logger.error(f"Token解码失败: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        return None

async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证"
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user
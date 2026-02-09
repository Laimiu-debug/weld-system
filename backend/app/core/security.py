"""
Security utilities for the welding system backend application.
"""
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌.

    Args:
        subject: 令牌主题，通常是用户ID
        expires_delta: 过期时间增量

    Returns:
        JWT访问令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建刷新令牌.

    Args:
        subject: 令牌主题，通常是用户ID
        expires_delta: 过期时间增量

    Returns:
        JWT刷新令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    验证令牌并提取用户ID.

    Args:
        token: JWT令牌
        token_type: 令牌类型 ("access" 或 "refresh")

    Returns:
        用户ID，如果令牌无效则返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type_claim: str = payload.get("type")

        if user_id is None or token_type_claim != token_type:
            return None

        return user_id
    except jwt.JWTError:
        # 开发环境临时修复：如果JWT验证失败，尝试解析开发环境token
        if settings.DEVELOPMENT:
            try:
                import base64
                from urllib.parse import unquote

                # 检查是否是JWT格式的token
                if '.' in token:
                    parts = token.split('.')
                    if len(parts) == 3:
                        # 尝试手动解析payload
                        payload_str = base64.b64decode(parts[1] + '==').decode('utf-8')
                        payload = eval(payload_str)  # 注意：仅在开发环境中使用
                        user_id = payload.get("sub")
                        token_type_claim = payload.get("type")

                        if user_id and token_type_claim == token_type:
                            print(f"DEBUG: Using dev environment token validation for user {user_id}")
                            return user_id
            except Exception as e:
                print(f"DEBUG: Dev environment token validation failed: {e}")

        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码.

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希值.

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    """
    生成密码重置令牌.

    Args:
        email: 用户邮箱

    Returns:
        密码重置令牌
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    验证密码重置令牌.

    Args:
        token: 密码重置令牌

    Returns:
        用户邮箱，如果令牌无效则返回None
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


def generate_api_key() -> str:
    """
    生成API密钥.

    Returns:
        随机生成的API密钥
    """
    return secrets.token_urlsafe(32)


def generate_verification_token() -> str:
    """
    生成邮箱验证令牌.

    Returns:
        随机生成的验证令牌
    """
    return secrets.token_urlsafe(32)


def check_permissions(
    user_permissions: list,
    required_permissions: list
) -> bool:
    """
    检查用户权限.

    Args:
        user_permissions: 用户拥有的权限列表
        required_permissions: 需要的权限列表

    Returns:
        是否具有所需权限
    """
    return all(perm in user_permissions for perm in required_permissions)


def check_member_tier_limits(
    current_tier: str,
    current_usage: Dict[str, int],
    tier_limits: Dict[str, int]
) -> Dict[str, bool]:
    """
    检查会员等级限制.

    Args:
        current_tier: 当前会员等级
        current_usage: 当前使用情况
        tier_limits: 等级限制配置

    Returns:
        各项限制检查结果
    """
    if current_tier not in tier_limits:
        return {"valid": False, "reason": "invalid_tier"}

    limits = tier_limits[current_tier]
    results = {}

    # 检查WPS数量限制
    if limits.get("max_wps", 0) >= 0:
        results["wps_ok"] = current_usage.get("wps_count", 0) <= limits["max_wps"]
    else:
        results["wps_ok"] = True

    # 检查PQR数量限制
    if limits.get("max_pqr", 0) >= 0:
        results["pqr_ok"] = current_usage.get("pqr_count", 0) <= limits["max_pqr"]
    else:
        results["pqr_ok"] = True

    # 检查用户数量限制
    if limits.get("max_users", 0) >= 0:
        results["users_ok"] = current_usage.get("users_count", 0) <= limits["max_users"]
    else:
        results["users_ok"] = True

    # 检查存储空间限制
    if limits.get("max_storage", 0) >= 0:
        results["storage_ok"] = current_usage.get("storage_used", 0) <= limits["max_storage"]
    else:
        results["storage_ok"] = True

    # 总体检查结果
    results["all_ok"] = all(
        results.get(key, True)
        for key in ["wps_ok", "pqr_ok", "users_ok", "storage_ok"]
    )

    return results


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符.

    Args:
        filename: 原始文件名

    Returns:
        清理后的安全文件名
    """
    import re

    # 移除路径分隔符和其他危险字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)

    # 移除控制字符
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)

    # 限制文件名长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext

    return filename.strip()


def generate_file_hash(content: bytes) -> str:
    """
    生成文件内容的哈希值.

    Args:
        content: 文件内容

    Returns:
        文件哈希值
    """
    import hashlib

    return hashlib.sha256(content).hexdigest()


def is_safe_url(url: str, allowed_hosts: list) -> bool:
    """
    检查URL是否安全.

    Args:
        url: 待检查的URL
        allowed_hosts: 允许的主机列表

    Returns:
        URL是否安全
    """
    from urllib.parse import urlparse

    try:
        parsed_url = urlparse(url)
        host = parsed_url.netloc

        # 检查是否在允许的主机列表中
        if host in allowed_hosts:
            return True

        # 检查是否是相对URL
        if not host and not parsed_url.scheme:
            return True

        return False
    except Exception:
        return False
"""
User management endpoints for the welding system backend.
"""
import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.rate_limit import client_ip, enforce_rate_limit
from app.core.security import verify_password
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserPreferences,
    SecuritySettingsUpdate,
    SecurityOverview,
    LoginHistoryItem,
    PhoneBindSendCodeRequest,
    PhoneBindConfirmRequest,
)
from app.schemas.verification_code import VerificationCodeResponse
from app.services.user_service import user_service
from app.services.membership_service import MembershipService
from app.services.verification_service import verification_service
from app.services.sms_service import sms_service
from app.models.user import User
from app.models.system_log import SystemLog

router = APIRouter()

_DEFAULT_PREFERENCES = UserPreferences().model_dump()


def _parse_preferences(raw: Any) -> dict:
    if not raw:
        return dict(_DEFAULT_PREFERENCES)
    if isinstance(raw, dict):
        return {**_DEFAULT_PREFERENCES, **raw}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {**_DEFAULT_PREFERENCES, **data}
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    return dict(_DEFAULT_PREFERENCES)


@router.get("/", response_model=List[UserResponse])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """获取用户列表."""
    users = user_service.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """创建用户."""
    user = user_service.create(db, obj_in=user_in)
    return user


@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """获取当前用户信息."""
    updated_user = user_service.get(db, id=current_user.id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return updated_user


@router.put("/me", response_model=UserResponse)
def update_user_me(
    user_in: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """更新当前用户信息."""
    user = user_service.get(db, id=current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    # 手机号须经短信验证绑定，禁止个人资料直接改号
    update_data = user_in.model_dump(exclude_unset=True)
    update_data.pop("phone", None)
    user = user_service.update(db, db_obj=user, obj_in=UserUpdate(**update_data))
    return user


@router.get("/me/preferences", response_model=UserPreferences)
def get_my_preferences(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """获取当前用户的系统偏好设置."""
    user = user_service.get(db, id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return UserPreferences(**_parse_preferences(getattr(user, "preferences", None)))


@router.put("/me/preferences", response_model=UserPreferences)
def update_my_preferences(
    preferences: UserPreferences,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """更新当前用户的系统偏好设置."""
    user = user_service.get(db, id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    payload = preferences.model_dump()
    user.preferences = json.dumps(payload, ensure_ascii=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserPreferences(**_parse_preferences(user.preferences))


def _security_score(prefs: dict, user: User) -> int:
    score = 20
    if getattr(user, "is_verified", False):
        score += 25
    if prefs.get("loginNotifications"):
        score += 15
    if prefs.get("sessionTimeout"):
        score += 15
    if prefs.get("autoLogout"):
        score += 15
    if getattr(user, "phone", None):
        score += 10
    return min(score, 100)


def _parse_device(user_agent: Optional[str]) -> str:
    if not user_agent:
        return "未知设备"
    ua = user_agent.lower()
    browser = "浏览器"
    if "edg/" in ua:
        browser = "Edge"
    elif "chrome" in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua:
        browser = "Safari"
    os_name = "Unknown"
    if "windows" in ua:
        os_name = "Windows"
    elif "mac os" in ua or "macintosh" in ua:
        os_name = "macOS"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua:
        os_name = "iOS"
    elif "linux" in ua:
        os_name = "Linux"
    return f"{browser} - {os_name}"


@router.get("/me/security", response_model=SecurityOverview)
def get_my_security(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """获取当前用户的安全概览与最近登录记录."""
    user = user_service.get(db, id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    prefs = _parse_preferences(getattr(user, "preferences", None))
    logs = (
        db.query(SystemLog)
        .filter(
            SystemLog.user_id == user.id,
            SystemLog.log_type == "security",
            SystemLog.message.in_(["login_success", "login_failed", "password_changed"]),
        )
        .order_by(SystemLog.created_at.desc())
        .limit(20)
        .all()
    )

    recent = []
    for item in logs:
        status_value = "success"
        if item.message == "login_failed":
            status_value = "failed"
        elif item.message == "password_changed":
            status_value = "success"
        details = item.details or {}
        recent.append(
            LoginHistoryItem(
                id=item.id,
                time=item.created_at.isoformat() if item.created_at else None,
                ip=item.ip_address,
                device=details.get("device") or _parse_device(item.user_agent),
                status=status_value,
                message=item.message,
            )
        )

    return SecurityOverview(
        email=user.email,
        phone=user.phone,
        is_verified=bool(user.is_verified),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        last_login_ip=user.last_login_ip,
        loginNotifications=bool(prefs.get("loginNotifications", True)),
        sessionTimeout=bool(prefs.get("sessionTimeout", True)),
        autoLogout=bool(prefs.get("autoLogout", False)),
        autoLogoutMinutes=int(prefs.get("autoLogoutMinutes", 30) or 30),
        recent_logins=recent,
        security_score=_security_score(prefs, user),
    )


@router.put("/me/security", response_model=SecurityOverview)
def update_my_security(
    payload: SecuritySettingsUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """更新安全相关偏好设置."""
    user = user_service.get(db, id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    prefs = _parse_preferences(getattr(user, "preferences", None))
    updates = payload.model_dump(exclude_unset=True)
    prefs.update(updates)
    user.preferences = json.dumps(prefs, ensure_ascii=False)
    db.add(user)
    db.commit()
    db.refresh(user)

    logs = (
        db.query(SystemLog)
        .filter(
            SystemLog.user_id == user.id,
            SystemLog.log_type == "security",
            SystemLog.message.in_(["login_success", "login_failed", "password_changed"]),
        )
        .order_by(SystemLog.created_at.desc())
        .limit(20)
        .all()
    )
    recent = []
    for item in logs:
        status_value = "failed" if item.message == "login_failed" else "success"
        details = item.details or {}
        recent.append(
            LoginHistoryItem(
                id=item.id,
                time=item.created_at.isoformat() if item.created_at else None,
                ip=item.ip_address,
                device=details.get("device") or _parse_device(item.user_agent),
                status=status_value,
                message=item.message,
            )
        )
    return SecurityOverview(
        email=user.email,
        phone=user.phone,
        is_verified=bool(user.is_verified),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        last_login_ip=user.last_login_ip,
        loginNotifications=bool(prefs.get("loginNotifications", True)),
        sessionTimeout=bool(prefs.get("sessionTimeout", True)),
        autoLogout=bool(prefs.get("autoLogout", False)),
        autoLogoutMinutes=int(prefs.get("autoLogoutMinutes", 30) or 30),
        recent_logins=recent,
        security_score=_security_score(prefs, user),
    )


@router.post("/me/phone/send-code", response_model=VerificationCodeResponse)
def send_phone_bind_code(
    payload: PhoneBindSendCodeRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """发送绑定/换绑手机号的短信验证码."""
    enforce_rate_limit(f"bind-phone:{client_ip(request)}", limit=5, window_seconds=60)
    enforce_rate_limit(f"bind-phone-user:{current_user.id}", limit=3, window_seconds=60)
    enforce_rate_limit(f"bind-phone-num:{payload.phone}", limit=3, window_seconds=60)

    user = user_service.get(db, id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if user.phone and user.phone == payload.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已是当前绑定号码",
        )

    occupied = user_service.get_by_phone(db, phone=payload.phone)
    if occupied and occupied.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已被其他账号使用",
        )

    if not verification_service.can_send_code(
        db, payload.phone, "phone", "bind_phone"
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="发送验证码过于频繁，请稍后再试",
        )

    try:
        verification_code = verification_service.create_verification_code(
            db=db,
            account=payload.phone,
            account_type="phone",
            purpose="bind_phone",
            expires_minutes=10,
        )
        send_success = sms_service.send_verification_code(
            phone=payload.phone,
            code=verification_code.code,
            purpose="bind_phone",
            expires_minutes=10,
        )
        if not send_success and not settings.DEVELOPMENT:
            verification_code.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="验证码发送失败，请稍后重试",
            )
        return {"message": "验证码已发送到您的手机", "expires_in": 600}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败，请稍后重试",
        )


@router.post("/me/phone/bind", response_model=UserResponse)
def bind_phone(
    payload: PhoneBindConfirmRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """通过短信验证码绑定或换绑手机号."""
    enforce_rate_limit(f"bind-phone-confirm:{current_user.id}", limit=10, window_seconds=60)

    user = user_service.get(db, id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if user.phone and user.phone == payload.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已是当前绑定号码",
        )

    # 已有手机号时换绑需验证登录密码
    if user.phone:
        if not payload.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="换绑手机号请输入当前登录密码",
            )
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码不正确",
            )

    occupied = user_service.get_by_phone(db, phone=payload.phone)
    if occupied and occupied.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已被其他账号使用",
        )

    verified = verification_service.verify_code(
        db=db,
        account=payload.phone,
        code=payload.verification_code,
        account_type="phone",
        purpose="bind_phone",
    )
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码无效或已过期",
        )

    old_phone = user.phone
    user.phone = payload.phone
    db.add(user)
    try:
        ua = request.headers.get("user-agent")
        db.add(
            SystemLog(
                log_level="info",
                log_type="security",
                message="phone_bound" if not old_phone else "phone_changed",
                user_id=user.id,
                ip_address=client_ip(request),
                user_agent=ua,
                details={
                    "old_phone": old_phone,
                    "new_phone": payload.phone,
                    "device": (ua or "")[:160],
                },
            )
        )
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="绑定手机号失败，请稍后重试",
        )
    return user


@router.get("/me-membership")
def get_user_membership_info(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """获取当前用户的会员信息."""
    membership_service = MembershipService(db)
    membership_info = membership_service.get_user_membership_info(current_user.id)

    if not membership_info:
        limits = membership_service.get_membership_limits("free")
        features = membership_service.get_membership_features("free")
        member_tier = current_user.member_tier or "free"
        subscription_start_date = current_user.created_at.strftime('%Y-%m-%d') if hasattr(current_user, 'created_at') and current_user.created_at else None

        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "membership_tier": member_tier,
            "membership_type": current_user.membership_type or "personal",
            "subscription_status": "active",
            "subscription_start_date": subscription_start_date,
            "subscription_end_date": None,
            "auto_renewal": current_user.auto_renewal if hasattr(current_user, 'auto_renewal') else False,
            "features": features,
            "quotas": membership_service._build_quota_payload(current_user.id, limits),
        }

    return membership_info


@router.get("/me-usage")
def get_user_usage_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """获取当前用户的使用统计（按实际文档数）。"""
    membership_service = MembershipService(db)
    return membership_service.get_actual_usage_counts(current_user.id)


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int = Path(..., ge=1, description="用户ID,必须是正整数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """获取指定用户信息."""
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    user_id: int = Path(..., ge=1, description="用户ID,必须是正整数"),
    user_in: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user)
) -> Any:
    """更新指定用户信息."""
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    user = user_service.update(db, db_obj=user, obj_in=user_in)
    return user

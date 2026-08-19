"""
Authentication endpoints for the welding system backend.
"""
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.errors import not_implemented
from app.core.rate_limit import client_ip, enforce_rate_limit
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    generate_password_reset_token,
    verify_password_reset_token,
    verify_token,
)
from app.schemas.token import Token, TokenWithUser, TokenRefresh
from app.schemas.user import (
    UserCreate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    EmailTokenRequest,
    ResendVerificationRequest,
)
from app.schemas.verification_code import (
    VerificationCodeRequest,
    VerificationCodeResponse,
    LoginWithVerificationCode
)
from app.services.user_service import user_service
from app.services.verification_service import verification_service
from app.services.email_service import email_service
from app.services.sms_service import sms_service
from pydantic import BaseModel

class RegisterResponse(BaseModel):
    """Register response model."""
    message: str
    user_id: int
    email: str
    full_name: str

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    用户登录获取访问令牌 (OAuth2表单格式).

    Args:
        request: HTTP请求对象
        db: 数据库会话
        form_data: OAuth2密码表单

    Returns:
        JWT令牌信息

    Raises:
        HTTPException: 如果用户名或密码错误
    """
    enforce_rate_limit(f"login:{client_ip(request)}", limit=10, window_seconds=60)
    enforce_rate_limit(f"login-user:{form_data.username.lower()}", limit=10, window_seconds=60)

    # 验证用户凭据
    user = user_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )

    # 在开发环境中跳过邮箱验证
    if not settings.DEVELOPMENT and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先验证邮箱地址"
        )

    # 更新最后登录时间和IP
    client_ip = request.client.host
    if 'x-forwarded-for' in request.headers:
        client_ip = request.headers['x-forwarded-for']
    elif 'x-real-ip' in request.headers:
        client_ip = request.headers['x-real-ip']

    # 使用本地时间而不是UTC时间
    from datetime import datetime
    import pytz

    # 获取中国时区
    china_tz = pytz.timezone('Asia/Shanghai')
    local_time = datetime.now(china_tz)

    user.last_login_at = local_time
    user.last_login_ip = client_ip
    db.commit()

    print(f"用户登录成功: {user.email}, IP: {client_ip}, 时间: {user.last_login_at}")

    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        subject=user.id,
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/login-json", response_model=TokenWithUser)
async def login_with_json(  # Updated to support phone/email login
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    用户登录获取访问令牌 (JSON格式，支持邮箱/手机号).

    Args:
        request: HTTP请求对象
        login_data: 登录请求数据
        db: 数据库会话

    Returns:
        JWT令牌信息和用户信息

    Raises:
        HTTPException: 如果账号或密码错误
    """
    # 检测账号类型
    account_type = verification_service.detect_account_type(login_data.account)

    # 根据账号类型查找用户
    user = None
    if account_type == "email":
        user = user_service.get_by_email(db, email=login_data.account)
    elif account_type == "phone":
        user = user_service.get_by_phone(db, phone=login_data.account)
    else:
        # 如果不是标准格式，尝试按contact查找
        user = user_service.get_by_contact(db, contact=login_data.account)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误"
        )

    # 验证密码
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误"
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )

    # 在开发环境中跳过邮箱验证
    if not settings.DEVELOPMENT and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先验证邮箱地址"
        )

    # 更新最后登录时间和IP
    client_ip = request.client.host
    if 'x-forwarded-for' in request.headers:
        client_ip = request.headers['x-forwarded-for']
    elif 'x-real-ip' in request.headers:
        client_ip = request.headers['x-real-ip']

    # 使用本地时间而不是UTC时间
    import pytz
    china_tz = pytz.timezone('Asia/Shanghai')
    local_time = datetime.now(china_tz)

    user.last_login_at = local_time
    user.last_login_ip = client_ip
    db.commit()

    print(f"用户登录成功(JSON): {user.email}, IP: {client_ip}, 时间: {user.last_login_at}")

    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        subject=user.id,
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse.model_validate(user)
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    token_refresh: TokenRefresh,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    使用刷新令牌获取新的访问令牌.

    Args:
        token_refresh: 刷新令牌请求
        db: 数据库会话

    Returns:
        新的JWT令牌信息

    Raises:
        HTTPException: 如果刷新令牌无效
    """
    # 验证刷新令牌
    user_id = verify_token(token_refresh.refresh_token, token_type="refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )

    # 获取用户信息
    user = user_service.get(db, id=user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )

    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": token_refresh.refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/register", response_model=dict)
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db)
) -> dict:
    """
    用户注册.

    Args:
        user_in: 用户创建数据
        db: 数据库会话

    Returns:
        注册成功消息

    Raises:
        HTTPException: 如果邮箱已存在
    """
    print(f"📝 收到注册请求: email={user_in.email}, username={user_in.username}")

    # 检查邮箱是否已存在
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        print(f"❌ 邮箱已存在: {user_in.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )

    # 创建用户
    try:
        print(f"🔨 开始创建用户...")
        user = user_service.create(db, obj_in=user_in)
        print(f"用户创建成功: id={user.id}, email={user.email}")

        # 只返回基本成功消息，避免任何datetime字段
        response = {"message": "注册成功"}
        print(f"📤 返回响应: {response}")
        return response
    except Exception as e:
        print(f"❌ 用户创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"用户创建失败: {str(e)}"
        )


@router.post("/logout")
async def logout_user(
    current_user: dict = Depends(deps.get_current_user)
) -> Any:
    """
    用户登出.

    Args:
        current_user: 当前用户信息

    Returns:
        登出成功消息
    """
    # 在实际应用中，可以将令牌加入黑名单
    # 这里只是简单返回成功消息
    return {"message": "登出成功"}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """修改密码. 密码必须放在请求体中，不能出现在 query string."""
    if payload.confirm_password and payload.confirm_password != payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PASSWORD_MISMATCH", "message": "两次输入的新密码不一致"},
        )

    user = user_service.get(db, id=current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "用户不存在"},
        )

    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "BAD_PASSWORD", "message": "当前密码错误"},
        )

    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "密码修改成功"}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(deps.get_db)
) -> Any:
    """忘记密码. 无论邮箱是否存在都返回同一消息，避免账号枚举."""
    enforce_rate_limit(f"forgot:{client_ip(request)}", limit=5, window_seconds=60)
    user = user_service.get_by_email(db, email=payload.email)
    if user:
        reset_token = generate_password_reset_token(payload.email)
        try:
            email_service.send_email(
                to_email=payload.email,
                subject="【焊序】密码重置",
                html_content=f"<p>您的密码重置令牌：{reset_token}</p>",
                text_content=f"您的密码重置令牌：{reset_token}",
            )
        except Exception:
            pass
    return {"message": "如果该邮箱已注册，将收到密码重置邮件"}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """重置密码. token 与新密码必须放在请求体中."""
    if payload.confirm_password and payload.confirm_password != payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PASSWORD_MISMATCH", "message": "两次输入的新密码不一致"},
        )

    email = verify_password_reset_token(payload.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_TOKEN", "message": "无效或已过期的重置令牌"},
        )

    user = user_service.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "用户不存在"},
        )

    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "密码重置成功"}


@router.post("/verify-email")
def verify_email(
    payload: EmailTokenRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """验证邮箱. 尚未实现真实校验时返回 501，不伪装成功."""
    del payload, db
    not_implemented("邮箱验证")


@router.post("/resend-verification")
def resend_verification_email(
    payload: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(deps.get_db)
) -> Any:
    """重新发送验证邮件."""
    del payload, request, db
    not_implemented("重发验证邮件")


@router.post("/send-verification-code", response_model=VerificationCodeResponse)
async def send_verification_code(
    payload: VerificationCodeRequest,
    http_request: Request,
    db: Session = Depends(deps.get_db)
) -> Any:
    """发送验证码."""
    enforce_rate_limit(f"otp:{client_ip(http_request)}", limit=5, window_seconds=60)
    enforce_rate_limit(f"otp-account:{payload.account}", limit=3, window_seconds=60)

    account_type = verification_service.detect_account_type(payload.account)
    if account_type != payload.account_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号格式与类型不匹配"
        )

    # 检查用户是否存在（对于登录）
    if payload.purpose == "login":
        user = user_service.get_by_contact(db, contact=payload.account)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该账号未注册"
            )

    # 检查发送频率限制
    if not verification_service.can_send_code(
        db, payload.account, payload.account_type, payload.purpose
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="发送验证码过于频繁，请稍后再试"
        )

    try:
        # 创建验证码
        verification_code = verification_service.create_verification_code(
            db=db,
            account=payload.account,
            account_type=payload.account_type,
            purpose=payload.purpose,
            expires_minutes=10
        )

        send_success = False

        if payload.account_type == "email":
            send_success = email_service.send_verification_code(
                to_email=payload.account,
                code=verification_code.code,
                purpose=payload.purpose,
                expires_minutes=10
            )
        elif payload.account_type == "phone":
            send_success = sms_service.send_verification_code(
                phone=payload.account,
                code=verification_code.code,
                purpose=payload.purpose,
                expires_minutes=10
            )

        if not send_success and not settings.DEVELOPMENT:
            verification_code.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="验证码发送失败，请稍后重试",
            )

        return {
            "message": f"验证码已发送到您的{'邮箱' if payload.account_type == 'email' else '手机'}",
            "expires_in": 600,
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败，请稍后重试"
        )


@router.post("/login-with-verification-code", response_model=Token)
async def login_with_verification_code(
    request: Request,
    login_data: LoginWithVerificationCode,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    使用验证码登录.

    Args:
        request: HTTP请求对象
        login_data: 验证码登录请求
        db: 数据库会话

    Returns:
        JWT令牌信息

    Raises:
        HTTPException: 如果验证码错误或账号不存在
    """
    enforce_rate_limit(f"otp-login:{client_ip(request)}", limit=10, window_seconds=60)

    # 检查账号格式
    account_type = verification_service.detect_account_type(login_data.account)
    if account_type != login_data.account_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号格式与类型不匹配"
        )

    # 查找用户
    user = user_service.get_by_contact(db, contact=login_data.account)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该账号未注册"
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )

    # 验证验证码
    verification_code = verification_service.verify_code(
        db=db,
        account=login_data.account,
        code=login_data.verification_code,
        account_type=login_data.account_type,
        purpose="login"
    )

    if not verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )

    # 在开发环境中跳过邮箱验证
    if not settings.DEVELOPMENT and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先验证邮箱地址"
        )

    # 更新最后登录时间和IP
    client_ip = request.client.host
    if 'x-forwarded-for' in request.headers:
        client_ip = request.headers['x-forwarded-for']
    elif 'x-real-ip' in request.headers:
        client_ip = request.headers['x-real-ip']

    # 使用本地时间而不是UTC时间
    import pytz
    china_tz = pytz.timezone('Asia/Shanghai')
    local_time = datetime.now(china_tz)

    user.last_login_at = local_time
    user.last_login_ip = client_ip
    db.commit()

    print(f"用户登录成功(验证码): {user.email}, IP: {client_ip}, 时间: {user.last_login_at}")

    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        subject=user.id,
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
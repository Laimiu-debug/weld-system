"""
Configuration settings for the welding system backend application.
"""
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LEAKED_SECRETS = {
    "dev-secret-key-for-testing-purposes-change-in-production",
    "secret",
    "changeme",
}

LEAKED_PASSWORDS = {
    "weld_password",
    "WeldDB@2024#Secure!Pass",
    "WeldDB@2024",
    "Redis@2024#Strong!Key",
    "ghzzz123",
    "password",
    "123456",
}


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # 应用基础配置
    APP_NAME: str = "Hanxu Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    DEVELOPMENT: bool = True

    # 服务器配置
    HOST: str = "localhost"
    PORT: int = 8000

    # 数据库配置
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "weld_db"
    DATABASE_USER: str = "weld_user"
    DATABASE_PASSWORD: str = "weld_password"
    DATABASE_URL: Optional[str] = None

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT配置
    SECRET_KEY: str = "dev-secret-key-for-testing-purposes-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:4002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3004",
        "http://127.0.0.1:4002"
    ]
    ALLOWED_CREDENTIALS: bool = True
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]

    # 文件存储配置
    UPLOAD_DIR: str = "./storage/uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [
        ".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx", ".xls", ".xlsx"
    ]

    # 邮件配置
    EMAIL_PROVIDER: str = "smtp"  # smtp, sendgrid, aliyun
    SMTP_TLS_PORT: int = 587
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"
    EMAILS_FROM_EMAIL: str = "noreply@yourdomain.com"
    EMAILS_FROM_NAME: str = "焊序"
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 4
    EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 48
    FRONTEND_URL: str = "http://localhost:3000"

    # SendGrid配置（可选）
    SENDGRID_API_KEY: Optional[str] = None

    # 阿里云配置（邮件和短信共用）
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_REGION_ID: str = "cn-hangzhou"

    # 短信配置
    SMS_PROVIDER: str = "aliyun"  # aliyun, tencent, yunpian

    # 阿里云短信配置
    ALIYUN_SMS_SIGN_NAME: str = "焊序"
    SMS_TEMPLATE_LOGIN: str = "SMS_LOGIN"  # 登录验证码模板ID
    SMS_TEMPLATE_REGISTER: str = "SMS_REGISTER"  # 注册验证码模板ID
    SMS_TEMPLATE_RESET_PASSWORD: str = "SMS_RESET_PASSWORD"  # 重置密码验证码模板ID

    # 腾讯云短信配置（可选）
    TENCENT_SECRET_ID: Optional[str] = None
    TENCENT_SECRET_KEY: Optional[str] = None
    TENCENT_SMS_APP_ID: Optional[str] = None
    TENCENT_SMS_SIGN_NAME: str = "焊序"
    TENCENT_SMS_REGION: str = "ap-guangzhou"

    # 云片短信配置（可选）
    YUNPIAN_API_KEY: Optional[str] = None

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "Asia/Shanghai"

    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Hanxu"
    PROJECT_DESCRIPTION: str = "焊序API服务"

    # 安全配置
    BCRYPT_ROUNDS: int = 12

    # 监控配置
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    # 系统配置
    TIMEZONE: str = "Asia/Shanghai"
    LOCALE: str = "zh_CN"

    # 支付配置
    PAYMENT_PROVIDER: str = "mock"  # mock, xunhu, pingpp

    # 虎皮椒支付配置（个人开发者推荐）
    XUNHU_APPID: Optional[str] = None
    XUNHU_APPSECRET: Optional[str] = None

    # Ping++支付配置（企业用户）
    PAYMENT_APP_ID: Optional[str] = None
    PAYMENT_API_KEY: Optional[str] = None

    # 支付回调配置
    PAYMENT_NOTIFY_URL: Optional[str] = "http://localhost:8000/api/v1/payments/callback"
    PAYMENT_RETURN_URL: Optional[str] = "http://localhost:3000/membership/payment-result"

    # 会员等级配置
    MEMBER_TIERS: Dict[str, Dict[str, Any]] = {
        "personal_free": {
            "name": "个人免费版",
            "max_wps": 10,
            "max_pqr": 10,
            "max_ppqr": 0,
            "max_users": 1,
            "max_storage": 10,  # GB
            "features": ["basic_wps", "basic_pqr", "export_pdf"]
        },
        "personal_pro": {
            "name": "个人专业版",
            "max_wps": 30,
            "max_pqr": 30,
            "max_ppqr": 30,
            "max_users": 1,
            "max_storage": 50,
            "features": ["advanced_wps", "advanced_pqr", "ppqr_basic", "materials_basic", "welders_basic"]
        },
        "personal_advanced": {
            "name": "个人高级版",
            "max_wps": 50,
            "max_pqr": 50,
            "max_ppqr": 50,
            "max_users": 1,
            "max_storage": 100,
            "features": ["enterprise_wps", "enterprise_pqr", "ppqr_advanced", "materials_advanced", "welders_advanced", "production_basic", "equipment_basic", "quality_basic"]
        },
        "personal_flagship": {
            "name": "个人旗舰版",
            "max_wps": 100,
            "max_pqr": 100,
            "max_ppqr": 100,
            "max_users": 1,
            "max_storage": 500,
            "features": ["all_personal_features", "reports_basic", "api_access"]
        },
        "enterprise": {
            "name": "企业版",
            "max_wps": 200,
            "max_pqr": 200,
            "max_ppqr": 200,
            "max_users": 10,
            "max_storage": 1000,
            "features": ["personal_flagship_features", "employee_management", "multi_factory_3", "reports_enterprise"]
        },
        "enterprise_pro": {
            "name": "企业版PRO",
            "max_wps": 400,
            "max_pqr": 400,
            "max_ppqr": 400,
            "max_users": 20,
            "max_storage": 10000,
            "features": ["enterprise_features", "multi_factory_unlimited", "reports_pro", "api_enterprise"]
        },
        "enterprise_pro_max": {
            "name": "企业版PRO MAX",
            "max_wps": 500,
            "max_pqr": 500,
            "max_ppqr": 500,
            "max_users": 50,
            "max_storage": -1,  # 无限制
            "features": ["enterprise_pro_features", "customization", "strategic_support", "dedicated_infrastructure"]
        }
    }

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def keep_explicit_db_url(cls, v: Optional[str]) -> Optional[str]:
        """Keep an explicit DATABASE_URL; assemble later from parts if missing."""
        if isinstance(v, str) and v:
            return v
        return None

    @model_validator(mode="after")
    def finalize_runtime_settings(self) -> "Settings":
        """Assemble connection URLs and reject weak production secrets."""
        from urllib.parse import quote

        if not self.DATABASE_URL:
            object.__setattr__(
                self,
                "DATABASE_URL",
                (
                    f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
                    f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
                ),
            )

        if self.REDIS_PASSWORD:
            encoded = quote(self.REDIS_PASSWORD, safe="")
            object.__setattr__(
                self,
                "REDIS_URL",
                f"redis://:{encoded}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}",
            )

        if not self.DEVELOPMENT:
            self._reject_insecure_production_values()
        return self

    def _reject_insecure_production_values(self) -> None:
        if (
            not self.SECRET_KEY
            or len(self.SECRET_KEY) < 32
            or self.SECRET_KEY in LEAKED_SECRETS
        ):
            raise ValueError(
                "Production SECRET_KEY must be at least 32 characters "
                "and must not use a default or leaked value"
            )

        if not self.DATABASE_PASSWORD or self.DATABASE_PASSWORD in LEAKED_PASSWORDS:
            raise ValueError(
                "Production DATABASE_PASSWORD must not use a default or leaked value"
            )
        if self.DATABASE_URL and any(
            leaked in self.DATABASE_URL
            for leaked in ("weld_password", "WeldDB@2024", "ghzzz123")
        ):
            raise ValueError(
                "Production DATABASE_URL must not use a default or leaked value"
            )

        if not self.REDIS_PASSWORD or self.REDIS_PASSWORD in LEAKED_PASSWORDS:
            raise ValueError(
                "Production REDIS_PASSWORD must be set and must not use a leaked default"
            )
        if self.REDIS_URL and "Redis@2024" in self.REDIS_URL:
            raise ValueError(
                "Production REDIS_URL must not use a leaked default"
            )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("ALLOWED_METHODS", mode="before")
    def assemble_cors_methods(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS methods from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("ALLOWED_HEADERS", mode="before")
    def assemble_cors_headers(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS headers from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    def assemble_file_extensions(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse allowed file extensions from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("CELERY_ACCEPT_CONTENT", mode="before")
    def assemble_celery_content(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse Celery accepted content types from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

# 创建全局设置实例
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def get_database_url() -> str:
    """Get database connection URL."""
    return str(settings.DATABASE_URL)


def get_redis_url() -> str:
    """Get Redis connection URL."""
    return settings.REDIS_URL


def is_development() -> bool:
    """Check if running in development mode."""
    return settings.DEVELOPMENT


def is_production() -> bool:
    """Check if running in production mode."""
    return not settings.DEVELOPMENT

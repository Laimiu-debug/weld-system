"""Encrypted AI credentials and enterprise AI governance."""
from __future__ import annotations

import base64
import hashlib
from urllib.parse import urlsplit

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.core.module_permissions import user_can_manage_employees
from app.models.company import Company
from app.models.smart_import import AIProviderConfig, EnterpriseAIPolicy
from app.models.operations import CredentialRotationAudit, DeploymentProfile
from app.models.user import User
from app.schemas.smart_import import (
    AIProviderConfigCreate,
    AIProviderConfigResponse,
    AIProviderConfigUpdate,
    EnterpriseAIPolicyUpdate,
)
from app.services.ai_provider_service import validate_ai_base_url


PLATFORM_AI_TASK_TYPES = {
    "wps_import",
    "pqr_import",
    "ppqr_import",
    "welder_import",
    "drawing_import",
    "general",
}
PLATFORM_AI_COMPLEXITIES = {"simple", "standard", "advanced"}


class AICredentialCipher:
    def __init__(self, key: str | None = None):
        raw = key or settings.AI_CREDENTIAL_ENCRYPTION_KEY
        if not raw:
            # Existing installations already have a stable application secret.
            # Derive a dedicated Fernet key so the admin UI can safely persist
            # provider credentials without adding another mandatory setup step.
            raw = base64.urlsafe_b64encode(
                hashlib.sha256(
                    f"weldsystem-ai-credentials:{settings.SECRET_KEY}".encode("utf-8")
                ).digest()
            ).decode("ascii")
        try:
            self._fernet = Fernet(raw.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise HTTPException(status_code=503, detail="AI 密钥加密配置无效") from exc

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError, UnicodeError) as exc:
            raise HTTPException(status_code=503, detail="已保存的 AI 密钥无法解密，请重新录入") from exc


def mask_key(last_four: str) -> str:
    return f"••••••••{last_four}"


def _platform_config_payload(item: AIProviderConfig, *, include_key: bool) -> dict:
    result = {
        "id": item.id,
        "name": item.name,
        "provider": item.provider,
        "base_url": item.base_url,
        "model": item.model,
        "task_types": list(item.task_types or []),
        "complexity_level": item.complexity_level or "standard",
        "point_multiplier": float(item.point_multiplier or 1),
        "priority": int(item.priority or 100),
        "is_default": bool(item.is_default),
        "is_active": bool(item.is_active),
        "last_test_status": item.last_test_status,
        "last_tested_at": item.last_tested_at,
        "last_error": item.last_error,
        "key_configured": True,
        "masked_api_key": mask_key(item.key_last_four),
        "source": "admin",
    }
    if include_key:
        result["api_key"] = AICredentialCipher().decrypt(item.encrypted_api_key)
    return result


def list_platform_ai_configs(
    db: Session, *, include_inactive: bool = True
) -> list[dict]:
    query = db.query(AIProviderConfig).filter(
        AIProviderConfig.scope_type == "platform"
    )
    if not include_inactive:
        query = query.filter(AIProviderConfig.is_active == True)  # noqa: E712
    return [
        _platform_config_payload(item, include_key=False)
        for item in query.order_by(
            AIProviderConfig.is_default.desc(),
            AIProviderConfig.priority.asc(),
            AIProviderConfig.updated_at.desc(),
        ).all()
    ]


def resolve_platform_ai_config(
    db: Session,
    *,
    include_key: bool = False,
    task_type: str | None = None,
    complexity: str | None = None,
    config_id: str | None = None,
) -> dict:
    """Resolve a routed platform model, falling back to environment defaults."""
    items = (
        db.query(AIProviderConfig)
        .filter(
            AIProviderConfig.scope_type == "platform",
            AIProviderConfig.is_active == True,  # noqa: E712
        )
        .all()
    )
    if config_id:
        selected = next((item for item in items if item.id == config_id), None)
        if selected is not None and selected.last_test_status == "success":
            return _platform_config_payload(selected, include_key=include_key)
        raise HTTPException(409, "已选模型配置已停用或未通过测试，请重新选择并授权")
    # A saved platform model is only user-routable after the administrator's
    # real provider test succeeds. This prevents a merely persisted key/model
    # from appearing available in the user portal.
    items = [item for item in items if item.last_test_status == "success"]
    candidates = [
        item
        for item in items
        if not task_type or not item.task_types or task_type in item.task_types
    ] or items
    target = complexity if complexity in PLATFORM_AI_COMPLEXITIES else "standard"
    rank = {"standard": 1, "simple": 2, "advanced": 3}
    rank[target] = 0
    item = min(
        candidates,
        key=lambda value: (
            rank.get(value.complexity_level or "standard", 4),
            not bool(value.is_default),
            int(value.priority or 100),
        ),
        default=None,
    )
    if item:
        return _platform_config_payload(item, include_key=include_key)

    result = {
        "id": None,
        "name": "环境变量默认模型",
        "provider": settings.AI_PLATFORM_PROVIDER,
        "base_url": settings.AI_PLATFORM_BASE_URL,
        "model": settings.AI_PLATFORM_MODEL or "",
        "task_types": [],
        "complexity_level": "standard",
        "point_multiplier": 1.0,
        "priority": 100,
        "is_default": True,
        "is_active": True,
        "last_test_status": "untested",
        "last_tested_at": None,
        "last_error": None,
        "key_configured": bool(settings.AI_PLATFORM_API_KEY),
        "masked_api_key": mask_key(settings.AI_PLATFORM_API_KEY[-4:])
        if settings.AI_PLATFORM_API_KEY
        else "",
        "source": "environment",
    }
    if include_key:
        result["api_key"] = settings.AI_PLATFORM_API_KEY or ""
    return result


def update_platform_ai_config(
    db: Session, data: dict, *, create_new: bool = False
) -> dict:
    """Create or update one platform model and its routing rule."""
    provider = str(data.get("provider") or "openai_responses").strip()
    if provider not in {"openai_responses", "openai_compatible_chat"}:
        raise HTTPException(status_code=422, detail="不支持的平台模型接口协议")
    base_url = str(data.get("base_url") or "").strip()
    model = str(data.get("model") or "").strip()
    if not base_url or not model:
        raise HTTPException(status_code=422, detail="接口地址和模型名称不能为空")
    task_types = sorted(
        {str(value).strip() for value in data.get("task_types") or [] if str(value).strip()}
    )
    if any(value not in PLATFORM_AI_TASK_TYPES for value in task_types):
        raise HTTPException(status_code=422, detail="包含不支持的平台模型任务类型")
    complexity = str(data.get("complexity_level") or "standard").strip()
    if complexity not in PLATFORM_AI_COMPLEXITIES:
        raise HTTPException(status_code=422, detail="模型复杂度等级无效")
    try:
        multiplier = float(data.get("point_multiplier", 1))
        priority = int(data.get("priority", 100))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="积分倍率或路由优先级无效") from exc
    if not 0 < multiplier <= 20 or priority < 0:
        raise HTTPException(status_code=422, detail="积分倍率或路由优先级超出范围")
    hostname = (urlsplit(base_url).hostname or "").lower()
    try:
        base_url = validate_ai_base_url(
            base_url,
            [hostname],
            allow_private=settings.AI_ALLOW_PRIVATE_PLATFORM_URL,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    item = None
    config_id = str(data.get("id") or "").strip()
    if config_id:
        item = db.query(AIProviderConfig).filter(
            AIProviderConfig.id == config_id,
            AIProviderConfig.scope_type == "platform",
        ).first()
        if item is None:
            raise HTTPException(status_code=404, detail="平台模型配置不存在")
    elif not create_new:
        item = (
            db.query(AIProviderConfig)
            .filter(AIProviderConfig.scope_type == "platform")
            .order_by(
                AIProviderConfig.is_default.desc(), AIProviderConfig.updated_at.desc()
            )
            .first()
        )
    api_key = str(data.get("api_key") or "").strip()
    if item is None and not api_key:
        raise HTTPException(status_code=422, detail="首次配置平台模型时必须填写 API Key")
    if item is None:
        item = AIProviderConfig(
            scope_type="platform",
            name=str(data.get("name") or model).strip(),
            provider=provider,
            base_url=base_url,
            model=model,
            encrypted_api_key=AICredentialCipher().encrypt(api_key),
            key_last_four=api_key[-4:],
            task_types=task_types,
            complexity_level=complexity,
            point_multiplier=multiplier,
            priority=priority,
            is_default=bool(data.get("is_default", False)),
        )
        db.add(item)
    else:
        item.name = str(data.get("name") or item.name).strip()
        item.provider = provider
        item.base_url = base_url
        item.model = model
        item.is_active = True
        item.task_types = task_types
        item.complexity_level = complexity
        item.point_multiplier = multiplier
        item.priority = priority
        item.is_default = bool(data.get("is_default", item.is_default))
        item.last_test_status = "untested"
        item.last_error = None
        if api_key:
            item.encrypted_api_key = AICredentialCipher().encrypt(api_key)
            item.key_last_four = api_key[-4:]
            item.key_version += 1
    if item.is_default:
        db.query(AIProviderConfig).filter(
            AIProviderConfig.scope_type == "platform",
            AIProviderConfig.id != item.id,
        ).update({AIProviderConfig.is_default: False}, synchronize_session=False)
    db.commit()
    db.refresh(item)
    return _platform_config_payload(item, include_key=False)


def disable_platform_ai_config(db: Session, config_id: str) -> None:
    item = db.query(AIProviderConfig).filter(
        AIProviderConfig.id == config_id,
        AIProviderConfig.scope_type == "platform",
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="平台模型配置不存在")
    item.is_active = False
    item.is_default = False
    db.commit()


class AIProviderConfigService:
    def __init__(self, db: Session):
        self.db = db

    def get_policy(self, context: WorkspaceContext) -> EnterpriseAIPolicy | None:
        if context.workspace_type != WorkspaceType.ENTERPRISE or not context.company_id:
            return None
        return (
            self.db.query(EnterpriseAIPolicy)
            .filter(EnterpriseAIPolicy.company_id == context.company_id)
            .first()
        )

    def policy_payload(self, context: WorkspaceContext) -> dict:
        policy = self.get_policy(context)
        return {
            "company_id": context.company_id,
            "allow_ai": policy.allow_ai if policy else True,
            "allow_external_providers": policy.allow_external_providers
            if policy
            else True,
            "allow_personal_keys": policy.allow_personal_keys if policy else True,
            "require_enterprise_key": policy.require_enterprise_key
            if policy
            else False,
            "allowed_hosts": list(policy.allowed_hosts or []) if policy else [],
            "updated_at": policy.updated_at if policy else None,
        }

    def _company(self, context: WorkspaceContext) -> Company:
        if context.workspace_type != WorkspaceType.ENTERPRISE or not context.company_id:
            raise HTTPException(status_code=400, detail="当前不是企业工作区")
        company = (
            self.db.query(Company).filter(Company.id == context.company_id).first()
        )
        if not company:
            raise HTTPException(status_code=404, detail="企业不存在")
        return company

    def ensure_company_manager(self, user: User, context: WorkspaceContext) -> Company:
        company = self._company(context)
        if not user_can_manage_employees(self.db, user, company):
            raise HTTPException(status_code=403, detail="仅企业管理员可管理企业 AI 配置")
        return company

    def update_policy(
        self, data: EnterpriseAIPolicyUpdate, user: User, context: WorkspaceContext
    ) -> EnterpriseAIPolicy:
        company = self.ensure_company_manager(user, context)
        hosts = sorted(
            {host.strip().lower() for host in data.allowed_hosts if host.strip()}
        )
        for host in hosts:
            if "/" in host or ":" in host or host.startswith("."):
                raise HTTPException(status_code=422, detail=f"不合法的允许域名：{host}")
        policy = self.get_policy(context)
        if not policy:
            policy = EnterpriseAIPolicy(company_id=company.id, created_by=user.id)
            self.db.add(policy)
        for field, value in data.model_dump().items():
            setattr(policy, field, hosts if field == "allowed_hosts" else value)
        policy.updated_by = user.id
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def _allowed_hosts(self, context: WorkspaceContext) -> list[str]:
        policy = self.get_policy(context)
        return list(settings.AI_BYOK_ALLOWED_HOSTS) + list(
            policy.allowed_hosts or [] if policy else []
        )

    def _validate_url(self, value: str, context: WorkspaceContext) -> str:
        try:
            return validate_ai_base_url(
                value, self._allowed_hosts(context), allow_private=False
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def list(self, user: User, context: WorkspaceContext) -> list[AIProviderConfig]:
        query = self.db.query(AIProviderConfig).filter(
            AIProviderConfig.is_active == True
        )  # noqa: E712
        personal = (AIProviderConfig.scope_type == "personal") & (
            AIProviderConfig.user_id == user.id
        )
        if context.workspace_type == WorkspaceType.ENTERPRISE and context.company_id:
            enterprise = (AIProviderConfig.scope_type == "enterprise") & (
                AIProviderConfig.company_id == context.company_id
            )
            return (
                query.filter(personal | enterprise)
                .order_by(AIProviderConfig.scope_type, AIProviderConfig.name)
                .all()
            )
        return query.filter(personal).order_by(AIProviderConfig.name).all()

    def get(
        self, config_id: str, user: User, context: WorkspaceContext
    ) -> AIProviderConfig:
        item = (
            self.db.query(AIProviderConfig)
            .filter(AIProviderConfig.id == config_id)
            .first()
        )
        allowed = item and (
            (item.scope_type == "personal" and item.user_id == user.id)
            or (
                item.scope_type == "enterprise"
                and context.workspace_type == WorkspaceType.ENTERPRISE
                and item.company_id == context.company_id
            )
        )
        if not allowed:
            raise HTTPException(status_code=404, detail="AI 配置不存在或无权访问")
        return item

    def create(
        self, data: AIProviderConfigCreate, user: User, context: WorkspaceContext
    ) -> AIProviderConfig:
        key = data.api_key.get_secret_value().strip()
        if not key or len(key) > 500:
            raise HTTPException(status_code=422, detail="API Key 无效")
        company_id = None
        owner_id = user.id
        if data.scope_type == "enterprise":
            company_id = self.ensure_company_manager(user, context).id
            owner_id = None
        base_url = self._validate_url(data.base_url, context)
        if data.is_default:
            self._clear_defaults(data.scope_type, owner_id, company_id)
        item = AIProviderConfig(
            scope_type=data.scope_type,
            user_id=owner_id,
            company_id=company_id,
            name=data.name.strip(),
            provider=data.provider,
            base_url=base_url,
            model=data.model.strip(),
            encrypted_api_key=AICredentialCipher().encrypt(key),
            key_last_four=key[-4:],
            is_default=data.is_default,
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(
        self,
        item: AIProviderConfig,
        data: AIProviderConfigUpdate,
        user: User,
        context: WorkspaceContext,
    ) -> AIProviderConfig:
        if item.scope_type == "enterprise":
            self.ensure_company_manager(user, context)
        values = data.model_dump(exclude_none=True)
        if "base_url" in values:
            values["base_url"] = self._validate_url(values["base_url"], context)
        if any(field in values for field in ("provider", "base_url", "model")):
            item.last_test_status = "untested"
            item.last_error = None
        if values.get("is_default"):
            self._clear_defaults(item.scope_type, item.user_id, item.company_id)
        for field, value in values.items():
            setattr(item, field, value.strip() if isinstance(value, str) else value)
        item.updated_by = user.id
        self.db.commit()
        self.db.refresh(item)
        return item

    def rotate(
        self, item: AIProviderConfig, key: str, user: User, context: WorkspaceContext
    ) -> AIProviderConfig:
        if item.scope_type == "enterprise":
            self.ensure_company_manager(user, context)
        key = key.strip()
        if not key or len(key) > 500:
            raise HTTPException(status_code=422, detail="API Key 无效")
        old_version = item.key_version
        item.encrypted_api_key = AICredentialCipher().encrypt(key)
        item.key_last_four = key[-4:]
        item.key_version += 1
        item.last_test_status = "untested"
        item.last_error = None
        item.updated_by = user.id
        self.db.add(
            CredentialRotationAudit(
                credential_type="ai_api_key",
                credential_ref=item.id,
                scope_type=item.scope_type,
                company_id=item.company_id,
                user_id=item.user_id,
                old_version=old_version,
                new_version=item.key_version,
                rotated_by=user.id,
                reason="用户主动轮换 AI API Key",
            )
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def disable(
        self, item: AIProviderConfig, user: User, context: WorkspaceContext
    ) -> None:
        if item.scope_type == "enterprise":
            self.ensure_company_manager(user, context)
        item.is_active = False
        item.is_default = False
        item.updated_by = user.id
        self.db.commit()

    def resolve_for_use(
        self, config_id: str, user: User, context: WorkspaceContext
    ) -> tuple[AIProviderConfig, str]:
        item = self.get(config_id, user, context)
        if not item.is_active:
            raise HTTPException(status_code=422, detail="AI 配置已停用")
        self.enforce_policy("byok", item, context)
        return item, AICredentialCipher().decrypt(item.encrypted_api_key)

    def enforce_policy(
        self, mode: str, item: AIProviderConfig | None, context: WorkspaceContext
    ) -> None:
        deployment = (
            self.db.query(DeploymentProfile)
            .filter(DeploymentProfile.company_id == context.company_id)
            .first()
            if self.db is not None and context.company_id
            else None
        )
        deployment_mode = (
            deployment.deployment_mode if deployment else settings.DEPLOYMENT_MODE
        )
        network_policy = (
            deployment.network_policy
            if deployment
            else ("offline" if deployment_mode == "offline" else "external_allowed")
        )
        if mode in {"platform", "byok"} and network_policy == "offline":
            raise HTTPException(
                status_code=503,
                detail="当前为完全离线模式，请使用企业本地模型或手工录入",
            )
        policy = self.get_policy(context)
        if not policy:
            return
        if not policy.allow_ai:
            raise HTTPException(status_code=403, detail="企业已停用 AI 分析")
        if policy.require_enterprise_key and (
            not item or item.scope_type != "enterprise"
        ):
            raise HTTPException(status_code=403, detail="企业要求使用企业统一 AI 配置")
        if (
            mode == "byok"
            and item
            and item.scope_type == "personal"
            and not policy.allow_personal_keys
        ):
            raise HTTPException(status_code=403, detail="企业不允许使用个人 AI Key")
        if mode == "byok" and item is None and not policy.allow_personal_keys:
            raise HTTPException(status_code=403, detail="企业不允许使用临时个人 AI Key")
        if mode == "byok" and not policy.allow_external_providers:
            platform_host = (
                urlsplit(resolve_platform_ai_config(self.db)["base_url"]).hostname or ""
            ).lower()
            item_host = (urlsplit(item.base_url).hostname or "").lower() if item else ""
            if not item or item_host != platform_host:
                raise HTTPException(status_code=403, detail="企业不允许使用外部模型服务")

    def _clear_defaults(
        self, scope: str, user_id: int | None, company_id: int | None
    ) -> None:
        self.db.query(AIProviderConfig).filter(
            AIProviderConfig.scope_type == scope,
            AIProviderConfig.user_id.is_(user_id),
            AIProviderConfig.company_id.is_(company_id),
        ).update({AIProviderConfig.is_default: False}, synchronize_session=False)


def provider_config_response(item: AIProviderConfig) -> AIProviderConfigResponse:
    return AIProviderConfigResponse(
        id=item.id,
        scope_type=item.scope_type,
        name=item.name,
        provider=item.provider,
        base_url=item.base_url,
        model=item.model,
        task_types=list(getattr(item, "task_types", None) or []),
        complexity_level=getattr(item, "complexity_level", "standard") or "standard",
        point_multiplier=float(getattr(item, "point_multiplier", 1) or 1),
        priority=int(getattr(item, "priority", 100) or 100),
        masked_api_key=mask_key(item.key_last_four),
        key_version=item.key_version,
        is_active=item.is_active,
        is_default=item.is_default,
        last_test_status=item.last_test_status,
        last_tested_at=item.last_tested_at,
        last_error=item.last_error,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )

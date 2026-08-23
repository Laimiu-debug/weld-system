from datetime import datetime
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1.endpoints.smart_import import validate_ai_extraction_request
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.schemas.smart_import import AIExtractionRequest
from app.services.ai_credential_service import (
    AICredentialCipher,
    AIProviderConfigService,
    mask_key,
    provider_config_response,
)
from app.services.ai_extraction_service import build_provider


def test_saved_credential_encrypts_and_only_returns_masked_key() -> None:
    cipher = AICredentialCipher(Fernet.generate_key().decode())
    ciphertext = cipher.encrypt("sk-super-secret-1234")

    assert ciphertext != "sk-super-secret-1234"
    assert cipher.decrypt(ciphertext) == "sk-super-secret-1234"
    assert mask_key("1234") == "••••••••1234"

    now = datetime.utcnow()
    response = provider_config_response(
        SimpleNamespace(
            id="config-1",
            scope_type="personal",
            name="我的模型",
            provider="openai_responses",
            base_url="https://api.openai.com/v1",
            model="gpt-test",
            encrypted_api_key=ciphertext,
            key_last_four="1234",
            key_version=1,
            is_active=True,
            is_default=False,
            last_test_status="untested",
            last_tested_at=None,
            last_error=None,
            created_at=now,
            updated_at=now,
        )
    )
    assert "encrypted_api_key" not in response.model_dump()
    assert response.masked_api_key.endswith("1234")


def test_byok_request_accepts_saved_or_temporary_but_not_both() -> None:
    saved = AIExtractionRequest(
        mode="byok", provider_config_id="config-1", module_id="module-1"
    )
    validate_ai_extraction_request(saved)

    temporary = AIExtractionRequest(
        mode="byok",
        provider="openai_responses",
        model="gpt-test",
        api_key="sk-temp",
        module_id="module-1",
    )
    validate_ai_extraction_request(temporary)

    with pytest.raises(ValidationError):
        AIExtractionRequest(
            mode="byok",
            provider_config_id="config-1",
            api_key="sk-temp",
            module_id="module-1",
        )


def test_saved_provider_uses_server_resolved_values() -> None:
    request = AIExtractionRequest(
        mode="byok", provider_config_id="config-1", module_id="module-1"
    )
    saved = SimpleNamespace(
        provider="openai_compatible_chat",
        base_url="https://api.openai.com/v1",
        model="company-model",
    )

    provider = build_provider(request, saved, "sk-decrypted")
    try:
        assert provider.config.model == "company-model"
        assert provider.config.api_key == "sk-decrypted"
    finally:
        provider.close()


def test_enterprise_policy_can_require_enterprise_key() -> None:
    service = AIProviderConfigService(None)  # type: ignore[arg-type]
    service.get_policy = lambda context: SimpleNamespace(  # type: ignore[method-assign]
        allow_ai=True,
        require_enterprise_key=True,
        allow_personal_keys=False,
        allow_external_providers=True,
    )
    context = WorkspaceContext(
        user_id=7, workspace_type=WorkspaceType.ENTERPRISE, company_id=9
    )

    with pytest.raises(HTTPException) as exc:
        service.enforce_policy("platform", None, context)
    assert exc.value.status_code == 403

    enterprise_config = SimpleNamespace(
        scope_type="enterprise", base_url="https://api.openai.com/v1"
    )
    service.enforce_policy("byok", enterprise_config, context)

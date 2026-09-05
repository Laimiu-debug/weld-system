from types import SimpleNamespace
from unittest.mock import Mock, patch
import httpx
import pytest
from fastapi import HTTPException

from app.services.ai_provider_service import (
    OpenAICompatibleProvider,
    AIProviderConfig,
    StructuredAIRequest,
    AIProviderError,
)
from app.services.ai_routing_service import (
    routing_snapshot,
    validate_routing_snapshot,
    route_fingerprint,
    require_expected_route,
)
from app.services.ai_credential_service import resolve_platform_ai_config
from app.services.cad_conversion_service import cad_capabilities
from app.api.v1.endpoints import smart_import as endpoint
from app.schemas.smart_import import BatchAIExtractionRequest
from app.core.data_access import WorkspaceContext


@pytest.mark.parametrize(
    "body,code",
    [
        ([], "invalid_provider_response"),
        (
            {
                "choices": [{"message": {"content": "{}"}}],
                "usage": {"total_tokens": "invalid"},
            },
            "invalid_provider_response",
        ),
        (
            {"choices": [{"message": {"content": "{}"}, "finish_reason": "length"}]},
            "provider_output_truncated",
        ),
        ({"status": "incomplete"}, "provider_output_truncated"),
    ],
)
def test_provider_errors_have_stable_safe_diagnostics(body, code):
    client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body))
    )
    provider = OpenAICompatibleProvider(
        AIProviderConfig(
            "openai_compatible_chat", "https://model.example/v1", "test-key", "test"
        ),
        client,
    )
    try:
        with pytest.raises(AIProviderError) as exc:
            provider.structured_response(
                StructuredAIRequest("JSON", "", {"type": "object"})
            )
        assert exc.value.code == code
    finally:
        provider.close()


@pytest.mark.parametrize(
    "field,value",
    [
        ("model", "new"),
        ("base_url", "https://different.example/v1"),
        ("provider", "openai_responses"),
    ],
)
def test_worker_cannot_switch_recipient_or_model(field, value):
    config = SimpleNamespace(
        id="one",
        provider="openai_compatible_chat",
        model="vision",
        base_url="https://model.example/v1",
    )
    snapshot = routing_snapshot(config, "drawing_import", "advanced")
    fingerprint = route_fingerprint(config)
    validate_routing_snapshot(snapshot, config)
    require_expected_route(fingerprint, config)
    setattr(config, field, value)
    with pytest.raises(HTTPException, match="409"):
        validate_routing_snapshot(snapshot, config)
    with pytest.raises(HTTPException):
        require_expected_route(fingerprint, config)


def test_deleted_pinned_model_never_falls_back():
    db = Mock()
    db.query.return_value.filter.return_value.all.return_value = []
    with pytest.raises(HTTPException) as exc:
        resolve_platform_ai_config(db, config_id="deleted")
    assert exc.value.status_code == 409


def test_dwg_capability_is_not_advertised_without_executable(monkeypatch):
    monkeypatch.setenv("CAD_DWG_CONVERTER", "C:/nonexistent/converter.exe")
    assert ".dwg" not in cad_capabilities()["extensions"]


def test_batch_routes_each_document_and_saves_recipient_identity():
    db, owner = Mock(), SimpleNamespace(id=7)
    docs = [
        SimpleNamespace(id="short", document_type="pqr", page_count=2),
        SimpleNamespace(id="long", document_type="pqr", page_count=15),
    ]
    batch = SimpleNamespace(id="batch", target_entity_type="pqr")
    smart = Mock()
    smart.get_batch.return_value = batch
    smart.get_batch_documents.return_value = docs
    queue = Mock()
    queue.create_job.side_effect = [SimpleNamespace(id="j1"), SimpleNamespace(id="j2")]

    def resolve(db, document):
        return (
            SimpleNamespace(
                id=document.id,
                provider="openai_compatible_chat",
                model=document.id,
                base_url="https://model.example/v1",
                complexity_level="simple",
                point_multiplier=1,
            ),
            "secret",
        )

    with patch.object(
        endpoint, "resolve_workspace", return_value=WorkspaceContext(7, "personal")
    ), patch.object(endpoint, "ensure_import_permission"), patch.object(
        endpoint, "SmartImportService", return_value=smart
    ), patch.object(
        endpoint, "AIProviderConfigService"
    ), patch.object(
        endpoint, "build_requested_schema", return_value=({"schema_version": "1"}, None)
    ), patch.object(
        endpoint, "resolve_platform_provider_config", side_effect=resolve
    ), patch.object(
        endpoint, "require_sensitive_document_consent"
    ), patch.object(
        endpoint, "AIExtractionQueueService", return_value=queue
    ), patch.object(
        endpoint, "dispatch_extraction_job"
    ):
        result = endpoint.queue_batch_extraction(
            "batch", BatchAIExtractionRequest(mode="platform"), db, owner, None
        )
    assert result.succeeded == 2
    calls = queue.create_job.call_args_list
    assert [
        call.kwargs["schema_snapshot"]["x-weld-routing"]["model"] for call in calls
    ] == ["short", "long"]
    assert [
        call.kwargs["schema_snapshot"]["x-weld-routing"]["complexity"] for call in calls
    ] == ["simple", "advanced"]
    assert "secret" not in str(calls)

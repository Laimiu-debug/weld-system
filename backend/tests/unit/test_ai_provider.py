import json

import httpx
import pytest

from app.services.ai_provider_service import (
    AIProviderConfig,
    AIProviderError,
    OpenAICompatibleProvider,
    StructuredAIRequest,
    make_strict_provider_schema,
    validate_ai_base_url,
)


SCHEMA = {
    "type": "object",
    "properties": {
        "required_value": {"type": "string"},
        "optional_value": {"type": "number", "x-weld-unit": "mm"},
    },
    "required": ["required_value"],
    "additionalProperties": False,
}


def test_strict_schema_makes_optional_fields_nullable_and_removes_extensions() -> None:
    schema = make_strict_provider_schema(SCHEMA)

    assert schema["required"] == ["required_value", "optional_value"]
    assert schema["properties"]["required_value"] == {"type": "string"}
    optional = schema["properties"]["optional_value"]
    assert optional["anyOf"] == [{"type": "number"}, {"type": "null"}]


def test_responses_provider_sends_image_capable_structured_request() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers["authorization"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "resp-1",
                "output_text": json.dumps(
                    {"required_value": "Q345R", "optional_value": None}
                ),
                "usage": {
                    "input_tokens": 20,
                    "output_tokens": 8,
                    "total_tokens": 28,
                },
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        AIProviderConfig(
            provider="openai_responses",
            base_url="https://api.openai.com/v1",
            api_key="secret-key",
            model="vision-model",
        ),
        client,
    )

    result = provider.structured_response(
        StructuredAIRequest("system", "source", SCHEMA)
    )

    assert captured["authorization"] == "Bearer secret-key"
    assert captured["body"]["store"] is False
    assert captured["body"]["text"]["format"]["strict"] is True
    assert result.data["required_value"] == "Q345R"
    assert result.total_tokens == 28


def test_provider_errors_do_not_expose_remote_response_body() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(401, text="echoed-secret-key")
        )
    )
    provider = OpenAICompatibleProvider(
        AIProviderConfig(
            provider="openai_responses",
            base_url="https://api.openai.com/v1",
            api_key="secret-key",
            model="model",
        ),
        client,
    )

    with pytest.raises(AIProviderError) as exc_info:
        provider.structured_response(StructuredAIRequest("system", "source", SCHEMA))

    assert exc_info.value.code == "provider_auth_failed"
    assert "secret" not in str(exc_info.value)


def test_provider_rejects_non_json_structured_output() -> None:
    provider = OpenAICompatibleProvider(
        AIProviderConfig(
            provider="openai_responses",
            base_url="https://api.openai.com/v1",
            api_key="secret-key",
            model="model",
        ),
        httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"output_text": "not-json"})
            )
        ),
    )

    with pytest.raises(AIProviderError) as exc_info:
        provider.structured_response(StructuredAIRequest("system", "source", SCHEMA))

    assert exc_info.value.code == "invalid_provider_response"


def test_chat_compatible_provider_parses_structured_output() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["response_format"]["type"] == "json_schema"
        return httpx.Response(
            200,
            json={
                "id": "chat-1",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"required_value": "Q345R", "optional_value": 12}
                            )
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 4,
                    "completion_tokens": 3,
                    "total_tokens": 7,
                },
            },
        )

    provider = OpenAICompatibleProvider(
        AIProviderConfig(
            provider="openai_compatible_chat",
            base_url="https://compatible.example/v1",
            api_key="temporary-key",
            model="vision-model",
        ),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = provider.structured_response(
        StructuredAIRequest("system", "source", SCHEMA)
    )

    assert result.response_id == "chat-1"
    assert result.total_tokens == 7


def test_deepseek_uses_json_object_mode_and_schema_in_prompt() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.deepseek.com/chat/completions"
        body = json.loads(request.content)
        assert body["model"] == "deepseek-v4-flash"
        assert body["response_format"] == {"type": "json_object"}
        assert body["thinking"] == {"type": "disabled"}
        assert "JSON Schema" in body["messages"][0]["content"]
        assert "required_value" in body["messages"][0]["content"]
        return httpx.Response(
            200,
            json={
                "id": "deepseek-1",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"required_value": "Q345R", "optional_value": None}
                            )
                        }
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            },
        )

    provider = OpenAICompatibleProvider(
        AIProviderConfig(
            provider="openai_compatible_chat",
            base_url="https://api.deepseek.com",
            api_key="deepseek-key",
            model="deepseek-v4-flash",
        ),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = provider.structured_response(
        StructuredAIRequest("Return JSON.", "source", SCHEMA)
    )

    assert result.response_id == "deepseek-1"
    assert result.total_tokens == 8


def test_deepseek_retries_one_empty_json_response() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        content = "" if calls == 1 else json.dumps(
            {"required_value": "Q345R", "optional_value": None}
        )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}], "usage": {}},
        )

    provider = OpenAICompatibleProvider(
        AIProviderConfig(
            provider="openai_compatible_chat",
            base_url="https://api.deepseek.com",
            api_key="temporary-key",
            model="deepseek-v4-flash",
        ),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = provider.structured_response(
        StructuredAIRequest("Return JSON.", "source", SCHEMA)
    )

    assert calls == 2
    assert result.data["required_value"] == "Q345R"


def test_byok_url_requires_https_and_allowlisted_host() -> None:
    assert (
        validate_ai_base_url("https://api.openai.com/v1", ["api.openai.com"], False)
        == "https://api.openai.com/v1"
    )
    with pytest.raises(ValueError, match="HTTPS"):
        validate_ai_base_url("http://127.0.0.1:8000/v1", ["127.0.0.1"], False)
    with pytest.raises(ValueError, match="允许清单"):
        validate_ai_base_url("https://evil.example/v1", ["api.openai.com"], False)

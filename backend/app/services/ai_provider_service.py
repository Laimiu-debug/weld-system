"""Provider-neutral structured AI calls for OCR and document extraction."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx


SUPPORTED_AI_PROVIDERS = {"openai_responses", "openai_compatible_chat"}

VISION_TEST_IMAGE_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAIAAAABACAIAAABdtOgoAAAElUlEQVR4nO2cTUhqTRiAz/mqG7axRRDSrk1BoKSE2lHpqAlB0SKqTUEQtEqyRbUJyk0/m/YF/S7LcBX9WJihZhFWBAYVLbJFGGRUizpJcxfDPRxST12593sX931WM+/MmXnPPMwcgyGWEMIgcPwHncC/DgoABgUAky+tsCwLlcc/hfS7izsAmPz0EP4u+nuknzG4A4BBAcCgAGBQADAoABgUAAwKAAYFAIMCgEEBwKAAYFAAMCgAGBQADAoABgUAgwKAQQHAoABgchTQ1dW1srJCyxqNpr+/n5ZdLpfH42EYpqioqO4XU1NTDMMUFxd/GoT24Xme47iFhQUxPjg4ODs7K1YdDsfp6an4eDQadTgcPM/X19fH43HpyPPz8zqdzmg06nS6xcVFGlQoFDzPi6NJ0/B6vTTD/Px8WvB4POmZf5ox41O5LSPDMAyRkB7JxvT09MDAACHk6elJq9UajUYaNxgMd3d3hBClUvnpEZnIy8uL1WpdXl6m1UAg0NLSQsvPz88VFRXSzhqNJh6PE0I8Hk9bW5vYtLGxwXFcMpkkhCSTSY7jfD4fbTWZTH6/P1san4LpHdJnlBlKngxrLt+cjbOzM57nCSFbW1vDw8Majeb19VUQBLVanS05+cjR0RHHcbScSqXKy8vf398JIV6vt6+vT9pZpVJdXl4SQgRB2NvbE5tsNls4HBYHDIVCdrudtu7s7FgslmxpkK8EpM8oM5Q86Suc4xFUVVV1fX1NCAmHw2azWafTHR8fn5yc1NTU5DagWq2+urqi5by8PIPBEIlEGIZZW1trbm6W9hwbGzObzd3d3cFg0Gw2i/Hz8/Pq6mqxqtVqY7EYLVutVoZh/H5/brllm/GPkKMAlmUrKysvLi4ODw+NRmNtbW0kEjk4OLBYLLSDIAjiSbq/v//lgKlUqqCgQKw2NTWtr68zDBOJRD69c1dXVywWM5lMLpdrdHQ024CEEOklHLfbPTIy8p1XS8/8mzPmiPwGkcHtdi8tLdGDKBaLtbe3d3R00G2RcXvKR3Z3dxsaGsRqMpnU6/XRaLSzs1PaOZFIhEIhGkkkEqWlpWKT3W4XmwghwWDQ4XBIZ6mrq9vZ2fndIyjjjNne6EsyrLl8sww+n89mszmdTkLIx8eHVqulMrIlJxN5eHjQ6/Xid5LC83xvb+/q6qq08/39fVlZ2c3NDSHk/Py8pqZGbNrc3OQ47vHxkfz6CG9vb0tnCQQCJpPpdwVknDHbG31J+gpnuJr4TQwGQyAQ6OnpYRiGZVmVSqVUKsVWupFp2Wg0jo+PC4JgMplohOO4yclJ2odl2ff396GhIbE/pbGxcWRkZGJiQhosKSmZmZlpbW1VKBR5eXlzc3Nik8PhuL295Xm+sLBQEASn02mz2aTPWiyWHz9+vL29yb9XeubZZvwjsERyE5QemgTvhv410lcY/xIGBgUAgwKAQQHAoABgUAAwKAAYFAAMCgAGBQCDAoBBAcCgAGBQADAoABgUAAwKAAYFAIMCgEEBwKAAYFAAMCgAmAwXs/B/J/6f4A4AhsV7cLDgDgAGBQCDAoD5CV+8u9hOXJ4VAAAAAElFTkSuQmCC"
)


class AIProviderError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class AIProviderConfig:
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 90
    max_output_tokens: int = 12000


@dataclass(frozen=True)
class AIImageInput:
    data_url: str
    page_number: int


@dataclass(frozen=True)
class StructuredAIRequest:
    instructions: str
    input_text: str
    json_schema: dict[str, Any]
    images: list[AIImageInput] = field(default_factory=list)
    schema_name: str = "weld_document_extraction"


@dataclass(frozen=True)
class AIProviderResult:
    data: dict[str, Any]
    response_id: str | None
    input_tokens: int
    output_tokens: int
    total_tokens: int


class AIProvider(Protocol):
    @property
    def provider_name(self) -> str:
        ...

    @property
    def model_name(self) -> str:
        ...

    def structured_response(self, request: StructuredAIRequest) -> AIProviderResult:
        ...


class OpenAICompatibleProvider:
    """Calls OpenAI Responses or compatible Chat Completions over HTTP."""

    def __init__(
        self,
        config: AIProviderConfig,
        client: httpx.Client | None = None,
    ):
        if config.provider not in SUPPORTED_AI_PROVIDERS:
            raise AIProviderError("unsupported_provider", "不支持的 AI 服务协议")
        self.config = config
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(config.timeout_seconds),
            follow_redirects=False,
            trust_env=False,
        )

    @property
    def provider_name(self) -> str:
        return self.config.provider

    @property
    def model_name(self) -> str:
        return self.config.model

    def structured_response(self, request: StructuredAIRequest) -> AIProviderResult:
        provider_schema = make_strict_provider_schema(request.json_schema)
        if self.config.provider == "openai_responses":
            endpoint = "/responses"
            payload = self._responses_payload(request, provider_schema)
        else:
            endpoint = "/chat/completions"
            payload = self._chat_payload(request, provider_schema)
        response = self._post(endpoint, payload)
        try:
            body = response.json()
            output = (
                _responses_output_text(body)
                if self.config.provider == "openai_responses"
                else body["choices"][0]["message"]["content"]
            )
            if self._is_deepseek() and not str(output or "").strip():
                # DeepSeek documents that JSON mode can occasionally return an
                # empty content. Retry once so a healthy endpoint is not reported
                # as disconnected and extraction jobs are less brittle.
                response = self._post(endpoint, payload)
                body = response.json()
                output = body["choices"][0]["message"]["content"]
            data = json.loads(output)
            if not isinstance(data, dict):
                raise TypeError("structured output is not an object")
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise AIProviderError(
                "invalid_provider_response", "AI 服务返回了无法解析的结构化结果"
            ) from exc
        usage = body.get("usage") or {}
        input_tokens = int(
            usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0
        )
        output_tokens = int(
            usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0
        )
        return AIProviderResult(
            data=data,
            response_id=body.get("id"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=int(
                usage.get("total_tokens", input_tokens + output_tokens) or 0
            ),
        )

    def close(self) -> None:
        self.client.close()

    def _post(self, endpoint: str, payload: dict[str, Any]) -> httpx.Response:
        try:
            response = self.client.post(
                f"{self.config.base_url.rstrip('/')}{endpoint}",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "weldsystem-smart-import/1.0",
                },
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise AIProviderError("provider_timeout", "AI 服务响应超时", True) from exc
        except httpx.RequestError as exc:
            raise AIProviderError("provider_unavailable", "无法连接 AI 服务", True) from exc
        if response.status_code in {401, 403}:
            raise AIProviderError("provider_auth_failed", "AI API Key 无效或无权访问")
        if response.status_code == 429:
            raise AIProviderError("provider_rate_limited", "AI 服务额度不足或请求过快", True)
        if response.status_code >= 500:
            raise AIProviderError("provider_unavailable", "AI 服务暂时不可用", True)
        if response.status_code >= 400:
            raise AIProviderError("provider_rejected", "AI 服务拒绝了本次请求")
        return response

    def _responses_payload(
        self, request: StructuredAIRequest, schema: dict[str, Any]
    ) -> dict[str, Any]:
        content: list[dict[str, Any]] = [
            {"type": "input_text", "text": request.input_text}
        ]
        content.extend(
            {"type": "input_image", "image_url": image.data_url, "detail": "high"}
            for image in request.images
        )
        payload = {
            "model": self.config.model,
            "instructions": request.instructions,
            "input": [{"role": "user", "content": content}],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": request.schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
            "max_output_tokens": self.config.max_output_tokens,
            "store": False,
        }
        return payload

    def _chat_payload(
        self, request: StructuredAIRequest, schema: dict[str, Any]
    ) -> dict[str, Any]:
        content: list[dict[str, Any]] = [{"type": "text", "text": request.input_text}]
        content.extend(
            {
                "type": "image_url",
                "image_url": {"url": image.data_url, "detail": "high"},
            }
            for image in request.images
        )
        if self._is_deepseek():
            instructions = (
                f"{request.instructions}\n\n"
                "Return valid JSON matching this JSON Schema exactly:\n"
                f"{json.dumps(schema, ensure_ascii=False)}"
            )
            response_format: dict[str, Any] = {"type": "json_object"}
        else:
            instructions = request.instructions
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": request.schema_name,
                    "strict": True,
                    "schema": schema,
                },
            }
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": content},
            ],
            "response_format": response_format,
            "max_tokens": self.config.max_output_tokens,
        }
        if self._is_deepseek():
            # DeepSeek V4 enables thinking by default. Structured extraction and
            # connectivity checks need the final JSON rather than reasoning tokens.
            payload["thinking"] = {"type": "disabled"}
        return payload

    def _is_deepseek(self) -> bool:
        return (
            urlsplit(self.config.base_url).hostname or ""
        ).lower() == "api.deepseek.com"


def connection_test_request(*, vision: bool = False) -> StructuredAIRequest:
    """Build a structured test that exercises image transport when required."""
    return StructuredAIRequest(
        instructions='Return JSON only in the exact shape {"ok": true}.',
        input_text=(
            "Inspect the supplied test image, then confirm the request succeeded."
            if vision
            else "Connection test. Respond with JSON confirming ok is true."
        ),
        json_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean", "const": True}},
            "required": ["ok"],
            "additionalProperties": False,
        },
        images=[AIImageInput(VISION_TEST_IMAGE_DATA_URL, 1)] if vision else [],
        schema_name="vision_connection_test" if vision else "connection_test",
    )


def make_strict_provider_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Convert optional properties to required nullable properties for strict output."""
    if not isinstance(schema, dict):
        return schema
    result: dict[str, Any] = {}
    original_required = set(schema.get("required") or [])
    for key, value in schema.items():
        if key.startswith("x-weld-") or key in {"required", "format", "default"}:
            continue
        if key == "properties" and isinstance(value, dict):
            properties: dict[str, Any] = {}
            for field_name, field_schema in value.items():
                converted = make_strict_provider_schema(field_schema)
                if field_name not in original_required:
                    converted = _nullable_schema(converted)
                properties[field_name] = converted
            result[key] = properties
            result["required"] = list(properties)
        elif key == "items" and isinstance(value, dict):
            result[key] = make_strict_provider_schema(value)
        else:
            result[key] = value
    if result.get("type") == "object":
        result["additionalProperties"] = False
        result.setdefault("required", list((result.get("properties") or {}).keys()))
    return result


def _nullable_schema(schema: dict[str, Any]) -> dict[str, Any]:
    if schema.get("type") == "null":
        return schema
    return {"anyOf": [schema, {"type": "null"}]}


def _responses_output_text(body: dict[str, Any]) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    for item in body.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text" and isinstance(
                content.get("text"), str
            ):
                return content["text"]
    raise KeyError("output_text")


def validate_ai_base_url(
    base_url: str, allowed_hosts: list[str], allow_private: bool = False
) -> str:
    parsed = urlsplit(base_url)
    if parsed.scheme not in ({"http", "https"} if allow_private else {"https"}):
        raise ValueError("AI 服务地址必须使用 HTTPS")
    if not parsed.hostname or parsed.username or parsed.password or parsed.query:
        raise ValueError("AI 服务地址无效")
    hostname = parsed.hostname.lower()
    if not allow_private and hostname not in {item.lower() for item in allowed_hosts}:
        raise ValueError("该 AI 服务域名未列入系统允许清单")
    return base_url.rstrip("/")

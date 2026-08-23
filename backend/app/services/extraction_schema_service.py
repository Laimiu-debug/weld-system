"""Build provider-neutral extraction schemas from custom modules/templates."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable
from uuid import NAMESPACE_URL, uuid5

from app.domain.semantic_fields import get_semantic_field


EXTRACTION_SCHEMA_VERSION = "1.0"
FIELD_METADATA_VERSION = 1


def stable_legacy_field_id(module_id: str, field_key: str) -> str:
    """Return a deterministic ID for legacy fields that predate field_id."""
    return str(uuid5(NAMESPACE_URL, f"weldsystem:module:{module_id}:{field_key}"))


def normalize_module_fields(
    module_id: str,
    fields: dict[str, Any],
    existing_fields: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Normalize field AI metadata while preserving unknown presentation keys."""
    existing_fields = existing_fields or {}
    normalized: dict[str, dict[str, Any]] = {}
    for field_key, raw in fields.items():
        value = deepcopy(raw.model_dump() if hasattr(raw, "model_dump") else raw)
        previous = existing_fields.get(field_key) or {}
        value["field_id"] = (
            value.get("field_id")
            or previous.get("field_id")
            or stable_legacy_field_id(module_id, field_key)
        )
        value["aliases"] = _clean_strings(value.get("aliases"))
        value["examples"] = list(value.get("examples") or [])[:10]
        value["ai_extract_mode"] = value.get("ai_extract_mode") or "auto"
        confidence_threshold = value.get("confidence_threshold")
        value["confidence_threshold"] = float(
            0.8 if confidence_threshold is None else confidence_threshold
        )
        value["use_in_rules"] = bool(value.get("use_in_rules", False))
        normalized[field_key] = value
    return normalized


def _clean_strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result[:20]


def _option_values(options: Any) -> list[Any]:
    if not isinstance(options, list):
        return []
    values = []
    for option in options:
        if isinstance(option, dict):
            values.append(option.get("value"))
        else:
            values.append(option)
    return [value for value in values if value is not None]


def _value_schema(field: dict[str, Any]) -> dict[str, Any]:
    field_type = field.get("type", "text")
    if field_type == "number":
        schema: dict[str, Any] = {"type": "number"}
        if field.get("min") is not None:
            schema["minimum"] = field["min"]
        if field.get("max") is not None:
            schema["maximum"] = field["max"]
    elif field_type == "checkbox":
        schema = {"type": "boolean"}
    elif field_type == "date":
        schema = {"type": "string", "format": "date"}
    elif field_type == "table":
        schema = {
            "type": "array",
            "items": {"type": "object", "additionalProperties": True},
            "x-weld-table-definition": field.get("tableDefinition"),
        }
    else:
        schema = {"type": "string"}

    options = _option_values(field.get("options"))
    if options and schema.get("type") == "string":
        schema["enum"] = options
    if field.get("multiple"):
        schema = {"type": "array", "items": schema}
    if field.get("unit"):
        schema["x-weld-unit"] = field["unit"]
    return schema


def _evidence_value_schema(field_key: str, field: dict[str, Any]) -> dict[str, Any]:
    semantic = get_semantic_field(field.get("canonical_field_key"))
    description = field.get("description") or field.get("placeholder") or ""
    aliases = _clean_strings(field.get("aliases"))
    if semantic:
        description = description or semantic.description
        aliases = _clean_strings([*semantic.aliases, *aliases])
    return {
        "type": "object",
        "title": field.get("label") or field_key,
        "description": description,
        "properties": {
            "value": _value_schema(field),
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer", "minimum": 1},
                        "text": {"type": "string"},
                        "bbox": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 4,
                            "maxItems": 4,
                        },
                    },
                    "required": ["page", "text"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["value", "confidence", "evidence"],
        "additionalProperties": False,
        "x-weld-field-id": field["field_id"],
        "x-weld-field-key": field_key,
        "x-weld-canonical-field": field.get("canonical_field_key"),
        "x-weld-aliases": aliases,
        "x-weld-confidence-threshold": field.get("confidence_threshold", 0.8),
        "x-weld-rule-input": bool(field.get("use_in_rules", False)),
    }


def build_module_extraction_schema(module: Any) -> dict[str, Any]:
    fields = normalize_module_fields(module.id, module.fields or {})
    properties: dict[str, Any] = {}
    required: list[str] = []
    bindings: list[dict[str, Any]] = []
    for field_key, field in fields.items():
        mode = field.get("ai_extract_mode", "auto")
        extractable = mode == "auto" and field.get("type") not in ("file", "image")
        bindings.append(_binding(module.id, None, field_key, field, extractable))
        if not extractable:
            continue
        properties[field_key] = _evidence_value_schema(field_key, field)
        if field.get("required"):
            required.append(field_key)

    return {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "document_type": module.module_type,
        "source": {
            "kind": "module",
            "id": module.id,
            "name": module.name,
            "version": str(getattr(module, "schema_version", 1)),
        },
        "json_schema": _object_schema(module.name, properties, required),
        "field_bindings": bindings,
    }


def build_template_extraction_schema(
    template: Any,
    modules: Iterable[Any],
) -> dict[str, Any]:
    by_id = {module.id: module for module in modules}
    module_properties: dict[str, Any] = {}
    required_instances: list[str] = []
    bindings: list[dict[str, Any]] = []
    missing_modules: list[str] = []

    for instance in sorted(
        template.module_instances or [], key=lambda item: item.get("order", 0)
    ):
        instance_id = instance["instanceId"]
        module_id = instance["moduleId"]
        module = by_id.get(module_id)
        if module is None:
            missing_modules.append(module_id)
            continue
        fields = normalize_module_fields(module.id, module.fields or {})
        field_properties: dict[str, Any] = {}
        field_required: list[str] = []
        for field_key, field in fields.items():
            mode = field.get("ai_extract_mode", "auto")
            extractable = mode == "auto" and field.get("type") not in ("file", "image")
            bindings.append(
                _binding(module.id, instance_id, field_key, field, extractable)
            )
            if not extractable:
                continue
            field_properties[field_key] = _evidence_value_schema(field_key, field)
            if field.get("required"):
                field_required.append(field_key)
        title = instance.get("customName") or module.name
        module_properties[instance_id] = _object_schema(
            title, field_properties, field_required
        )
        if field_required:
            required_instances.append(instance_id)

    return {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "document_type": template.module_type,
        "source": {
            "kind": "template",
            "id": template.id,
            "name": template.name,
            "version": template.version,
        },
        "json_schema": _object_schema(
            template.name, module_properties, required_instances
        ),
        "field_bindings": bindings,
        "warnings": (
            [
                {"code": "MISSING_MODULE", "module_id": value}
                for value in missing_modules
            ]
        ),
    }


def _binding(
    module_id: str,
    instance_id: str | None,
    field_key: str,
    field: dict[str, Any],
    extractable: bool,
) -> dict[str, Any]:
    return {
        "module_id": module_id,
        "instance_id": instance_id,
        "field_id": field["field_id"],
        "field_key": field_key,
        "canonical_field_key": field.get("canonical_field_key"),
        "ai_extract_mode": field.get("ai_extract_mode", "auto"),
        "extractable": extractable,
    }


def _object_schema(
    title: str,
    properties: dict[str, Any],
    required: list[str],
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "title": title,
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema

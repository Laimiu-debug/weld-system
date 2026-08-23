"""Build provider-neutral extraction schemas from custom modules/templates."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable
from uuid import NAMESPACE_URL, uuid5

from app.domain.semantic_fields import get_semantic_field


EXTRACTION_SCHEMA_VERSION = "1.0"
FIELD_METADATA_VERSION = 1


def _core_field(
    field_key: str,
    label: str,
    field_type: str = "text",
    *,
    canonical: str | None = None,
    required: bool = False,
    aliases: tuple[str, ...] = (),
    unit: str | None = None,
    rule_input: bool = False,
) -> dict[str, Any]:
    return {
        "field_key": field_key,
        "label": label,
        "type": field_type,
        "canonical_field_key": canonical,
        "required": required,
        "aliases": list(aliases),
        "unit": unit,
        "use_in_rules": rule_input,
    }


BUILTIN_CORE_FIELDS: dict[str, tuple[dict[str, Any], ...]] = {
    "pqr": (
        _core_field("title", "标题", required=True, aliases=("文件名称", "评定名称")),
        _core_field("pqr_number", "PQR编号", canonical="document.number", required=True),
        _core_field("test_date", "试验日期", "datetime", canonical="document.date"),
        _core_field(
            "process_specification",
            "标准及版本",
            canonical="standard.code",
            aliases=("执行标准", "标准版本"),
            rule_input=True,
        ),
        _core_field(
            "welding_process", "焊接方法", canonical="welding.process", rule_input=True
        ),
        _core_field(
            "base_material_spec",
            "母材牌号",
            canonical="base_material.specification",
            rule_input=True,
        ),
        _core_field(
            "base_material_group",
            "母材组别",
            canonical="base_material.group",
            rule_input=True,
        ),
        _core_field(
            "base_material_thickness",
            "母材厚度",
            "number",
            canonical="base_material.thickness",
            unit="mm",
            rule_input=True,
        ),
        _core_field("joint_design", "接头形式", canonical="joint.type", rule_input=True),
        _core_field(
            "groove_type", "坡口形式", canonical="joint.groove_type", rule_input=True
        ),
        _core_field(
            "groove_angle_actual",
            "坡口角度",
            "number",
            canonical="joint.groove_angle",
            unit="degree",
        ),
        _core_field(
            "root_gap_actual", "根部间隙", "number", canonical="joint.root_gap", unit="mm"
        ),
        _core_field(
            "root_face_actual", "钝边", "number", canonical="joint.root_face", unit="mm"
        ),
        _core_field(
            "filler_material_spec",
            "焊材牌号",
            canonical="filler.specification",
            rule_input=True,
        ),
        _core_field(
            "filler_material_classification",
            "焊材分类",
            canonical="filler.classification",
            rule_input=True,
        ),
        _core_field(
            "filler_material_diameter",
            "焊材直径",
            "number",
            canonical="filler.diameter",
            unit="mm",
        ),
        _core_field("shielding_gas", "保护气体", canonical="shielding.gas"),
        _core_field(
            "current_actual", "实际电流", "number", canonical="electrical.current", unit="A"
        ),
        _core_field(
            "voltage_actual", "实际电压", "number", canonical="electrical.voltage", unit="V"
        ),
        _core_field(
            "welding_speed_actual", "实际焊接速度", "number", aliases=("焊速",), unit="mm/min"
        ),
        _core_field(
            "preheat_temp_actual",
            "实际预热温度",
            "number",
            canonical="thermal.preheat_temperature",
            unit="degC",
            rule_input=True,
        ),
        _core_field(
            "interpass_temp_max_actual",
            "最高层间温度",
            "number",
            canonical="thermal.interpass_temperature",
            unit="degC",
            rule_input=True,
        ),
        _core_field(
            "pwht_performed",
            "是否焊后热处理",
            "checkbox",
            canonical="thermal.pwht_required",
            rule_input=True,
        ),
        _core_field(
            "pwht_temperature_actual",
            "焊后热处理温度",
            "number",
            canonical="thermal.pwht_temperature",
            unit="degC",
            rule_input=True,
        ),
        _core_field(
            "pwht_time_actual",
            "焊后热处理时间",
            "number",
            canonical="thermal.pwht_duration",
            unit="h",
            rule_input=True,
        ),
        _core_field("visual_inspection_result", "目视检测结果", aliases=("VT结果", "外观检查")),
        _core_field("rt_result", "射线检测结果", aliases=("RT结果",)),
        _core_field("ut_result", "超声检测结果", aliases=("UT结果",)),
        _core_field("mt_result", "磁粉检测结果", aliases=("MT结果",)),
        _core_field("pt_result", "渗透检测结果", aliases=("PT结果",)),
        _core_field("ndt_report_number", "无损检测报告编号", aliases=("NDE报告号", "NDT报告号")),
        _core_field(
            "tensile_test_result",
            "拉伸试验结果",
            canonical="test.tensile.result",
            rule_input=True,
        ),
        _core_field(
            "tensile_strength_actual",
            "抗拉强度",
            "number",
            aliases=("Rm",),
            unit="MPa",
            rule_input=True,
        ),
        _core_field(
            "tensile_yield_strength",
            "屈服强度",
            "number",
            aliases=("ReL", "Rp0.2"),
            unit="MPa",
        ),
        _core_field("tensile_elongation", "延伸率", "number", aliases=("A%",), unit="%"),
        _core_field(
            "root_bend_result",
            "根弯结果",
            canonical="test.bend.result",
            aliases=("根部弯曲",),
            rule_input=True,
        ),
        _core_field(
            "face_bend_result",
            "面弯结果",
            canonical="test.bend.result",
            aliases=("表面弯曲",),
            rule_input=True,
        ),
        _core_field(
            "side_bend_result",
            "侧弯结果",
            canonical="test.bend.result",
            aliases=("侧面弯曲",),
            rule_input=True,
        ),
        _core_field("charpy_test_performed", "是否进行冲击试验", "checkbox"),
        _core_field(
            "charpy_test_temp",
            "冲击试验温度",
            "number",
            canonical="test.impact.temperature",
            unit="degC",
            rule_input=True,
        ),
        _core_field(
            "charpy_energy_avg",
            "平均冲击功",
            "number",
            canonical="test.impact.energy",
            unit="J",
            rule_input=True,
        ),
        _core_field(
            "charpy_energy_min",
            "最小冲击功",
            "number",
            aliases=("单值最小冲击功",),
            unit="J",
            rule_input=True,
        ),
        _core_field("hardness_test_performed", "是否进行硬度试验", "checkbox"),
        _core_field(
            "hardness_values",
            "硬度值",
            canonical="test.hardness.values",
            aliases=("HV", "HB", "HRC"),
            rule_input=True,
        ),
    ),
    "wps": (
        _core_field("title", "标题", required=True, aliases=("文件名称", "工艺名称")),
        _core_field("wps_number", "WPS编号", canonical="document.number", required=True),
        _core_field("revision", "版本", canonical="document.revision"),
        _core_field(
            "process_specification",
            "标准及版本",
            canonical="standard.code",
            aliases=("执行标准", "标准版本"),
            rule_input=True,
        ),
        _core_field(
            "welding_process", "焊接方法", canonical="welding.process", rule_input=True
        ),
        _core_field(
            "base_material_spec",
            "母材牌号",
            canonical="base_material.specification",
            rule_input=True,
        ),
        _core_field(
            "base_material_group",
            "母材组别",
            canonical="base_material.group",
            rule_input=True,
        ),
        _core_field(
            "base_material_thickness_range",
            "母材厚度范围",
            canonical="base_material.thickness_range",
            unit="mm",
            rule_input=True,
        ),
        _core_field("joint_design", "接头形式", canonical="joint.type", rule_input=True),
        _core_field(
            "groove_type", "坡口形式", canonical="joint.groove_type", rule_input=True
        ),
        _core_field(
            "groove_angle", "坡口角度", canonical="joint.groove_angle", unit="degree"
        ),
        _core_field("root_gap", "根部间隙", canonical="joint.root_gap", unit="mm"),
        _core_field("root_face", "钝边", canonical="joint.root_face", unit="mm"),
        _core_field(
            "filler_material_spec",
            "焊材牌号",
            canonical="filler.specification",
            rule_input=True,
        ),
        _core_field(
            "filler_material_classification",
            "焊材分类",
            canonical="filler.classification",
            rule_input=True,
        ),
        _core_field(
            "filler_material_diameter",
            "焊材直径",
            "number",
            canonical="filler.diameter",
            unit="mm",
        ),
        _core_field("shielding_gas", "保护气体", canonical="shielding.gas"),
        _core_field("current_range", "电流范围", aliases=("焊接电流",), unit="A"),
        _core_field("voltage_range", "电压范围", aliases=("电弧电压",), unit="V"),
        _core_field("welding_speed", "焊接速度", aliases=("焊速",), unit="mm/min"),
        _core_field("weld_passes", "焊道数量", "integer", aliases=("焊道数",)),
        _core_field("weld_layer", "焊层数量", "integer", aliases=("焊层数",)),
        _core_field(
            "preheat_temp_min",
            "最低预热温度",
            "number",
            canonical="thermal.preheat_temperature",
            unit="degC",
            rule_input=True,
        ),
        _core_field(
            "interpass_temp_max",
            "最高层间温度",
            "number",
            canonical="thermal.interpass_temperature",
            unit="degC",
            rule_input=True,
        ),
        _core_field(
            "pwht_required",
            "是否需要焊后热处理",
            "checkbox",
            canonical="thermal.pwht_required",
            rule_input=True,
        ),
        _core_field(
            "pwht_temperature",
            "焊后热处理温度",
            "number",
            canonical="thermal.pwht_temperature",
            unit="degC",
            rule_input=True,
        ),
        _core_field(
            "pwht_time",
            "焊后热处理时间",
            "number",
            canonical="thermal.pwht_duration",
            unit="h",
            rule_input=True,
        ),
        _core_field("ndt_required", "是否需要无损检测", "checkbox", aliases=("NDE要求", "NDT要求")),
        _core_field("ndt_methods", "无损检测方法", aliases=("NDE方法", "NDT方法")),
        _core_field("mechanical_testing", "力学性能试验要求", aliases=("试验要求",)),
        _core_field("wpqr_number", "支持的PQR编号", aliases=("PQR编号", "WPQR编号")),
    ),
}


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
    if field_type in {"number", "integer"}:
        schema: dict[str, Any] = {"type": field_type}
        if field.get("min") is not None:
            schema["minimum"] = field["min"]
        if field.get("max") is not None:
            schema["maximum"] = field["max"]
    elif field_type == "checkbox":
        schema = {"type": "boolean"}
    elif field_type == "date":
        schema = {"type": "string", "format": "date"}
    elif field_type == "datetime":
        schema = {"type": "string", "format": "date-time"}
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


def build_builtin_extraction_schema(document_type: str) -> dict[str, Any]:
    """Build a safe core schema when an enterprise has no template yet."""
    definitions = BUILTIN_CORE_FIELDS.get(document_type)
    if not definitions:
        raise ValueError(f"当前导入类型没有内置提取 Schema：{document_type}")
    module_id = f"builtin:{document_type}"
    properties: dict[str, Any] = {}
    required: list[str] = []
    bindings: list[dict[str, Any]] = []
    for definition in definitions:
        field_key = definition["field_key"]
        field = {
            **definition,
            "field_id": stable_legacy_field_id(module_id, field_key),
            "ai_extract_mode": "auto",
            "confidence_threshold": 0.8,
        }
        properties[field_key] = _evidence_value_schema(field_key, field)
        bindings.append(_binding(module_id, None, field_key, field, True))
        if field.get("required"):
            required.append(field_key)
    label = document_type.upper()
    return {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "document_type": document_type,
        "source": {
            "kind": "builtin",
            "id": module_id,
            "name": f"{label} 核心字段",
            "version": EXTRACTION_SCHEMA_VERSION,
        },
        "json_schema": _object_schema(f"{label} 核心字段", properties, required),
        "field_bindings": bindings,
        "warnings": [],
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

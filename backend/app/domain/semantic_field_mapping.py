"""Mappings between stable semantic keys, legacy fixed columns and module data."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from app.domain.semantic_fields import get_semantic_field


FIXED_TO_CANONICAL: dict[str, dict[str, str]] = {
    "wps": {
        "title": "document.title",
        "wps_number": "document.number",
        "revision": "document.revision",
        "process_specification": "standard.code",
        "welding_process": "welding.process",
        "base_material_spec": "base_material.specification",
        "base_material_group": "base_material.group",
        "base_material_thickness_range": "base_material.thickness_range",
        "joint_design": "joint.type",
        "groove_type": "joint.groove_type",
        "groove_angle": "joint.groove_angle",
        "root_gap": "joint.root_gap",
        "root_face": "joint.root_face",
        "filler_material_spec": "filler.specification",
        "filler_material_classification": "filler.classification",
        "filler_material_diameter": "filler.diameter",
        "shielding_gas": "shielding.gas",
        "current_range": "electrical.current_range",
        "voltage_range": "electrical.voltage_range",
        "welding_speed": "welding.speed_range",
        "weld_passes": "welding.pass_count",
        "weld_layer": "welding.layer_count",
        "preheat_temp_min": "thermal.preheat_temperature",
        "interpass_temp_max": "thermal.interpass_temperature",
        "pwht_required": "thermal.pwht_required",
        "pwht_temperature": "thermal.pwht_temperature",
        "pwht_time": "thermal.pwht_duration",
        "ndt_required": "ndt.required",
        "ndt_methods": "ndt.methods",
        "mechanical_testing": "test.mechanical.requirements",
        "wpqr_number": "supporting.pqr_number",
    },
    "pqr": {
        "title": "document.title",
        "pqr_number": "document.number",
        "test_date": "document.date",
        "process_specification": "standard.code",
        "welding_process": "welding.process",
        "base_material_spec": "base_material.specification",
        "base_material_group": "base_material.group",
        "base_material_thickness": "base_material.thickness",
        "joint_design": "joint.type",
        "groove_type": "joint.groove_type",
        "groove_angle_actual": "joint.groove_angle",
        "root_gap_actual": "joint.root_gap",
        "root_face_actual": "joint.root_face",
        "filler_material_spec": "filler.specification",
        "filler_material_classification": "filler.classification",
        "filler_material_diameter": "filler.diameter",
        "shielding_gas": "shielding.gas",
        "current_actual": "electrical.current",
        "voltage_actual": "electrical.voltage",
        "welding_speed_actual": "welding.speed_actual",
        "weld_passes_actual": "welding.pass_count",
        "weld_layer_actual": "welding.layer_count",
        "preheat_temp_actual": "thermal.preheat_temperature",
        "interpass_temp_max_actual": "thermal.interpass_temperature",
        "pwht_performed": "thermal.pwht_required",
        "pwht_temperature_actual": "thermal.pwht_temperature",
        "pwht_time_actual": "thermal.pwht_duration",
        "visual_inspection_result": "ndt.visual_result",
        "rt_result": "ndt.rt_result",
        "ut_result": "ndt.ut_result",
        "mt_result": "ndt.mt_result",
        "pt_result": "ndt.pt_result",
        "ndt_report_number": "ndt.report_number",
        "tensile_test_result": "test.tensile.result",
        "tensile_strength_actual": "test.tensile.strength",
        "tensile_yield_strength": "test.tensile.yield_strength",
        "tensile_elongation": "test.tensile.elongation",
        "root_bend_result": "test.bend.root_result",
        "face_bend_result": "test.bend.face_result",
        "side_bend_result": "test.bend.side_result",
        "charpy_test_temp": "test.impact.temperature",
        "charpy_energy_avg": "test.impact.energy",
        "charpy_energy_min": "test.impact.minimum_energy",
        "charpy_test_performed": "test.impact.performed",
        "hardness_test_performed": "test.hardness.performed",
        "hardness_values": "test.hardness.values",
    },
}

CANONICAL_TO_FIXED: dict[str, dict[str, str]] = {
    document_type: {canonical: fixed for fixed, canonical in mappings.items()}
    for document_type, mappings in FIXED_TO_CANONICAL.items()
}


class SemanticMappingConflict(ValueError):
    """Raised when two confirmed values target the same formal field."""


def fixed_field_for(document_type: str, canonical_field_key: str | None) -> str | None:
    if not canonical_field_key:
        return None
    return CANONICAL_TO_FIXED.get(document_type, {}).get(canonical_field_key)


def canonical_field_for_fixed(document_type: str, fixed_field: str) -> str | None:
    return FIXED_TO_CANONICAL.get(document_type, {}).get(fixed_field)


def assign_semantic_value(
    document_type: str,
    payload: dict[str, Any],
    canonical_field_key: str | None,
    value: Any,
) -> str | None:
    """Project a semantic value into its formal field with conflict detection."""
    fixed_field = fixed_field_for(document_type, canonical_field_key)
    if fixed_field is None:
        return None
    fixed_value = _to_fixed_value(fixed_field, value)
    if fixed_field in payload and payload[fixed_field] != fixed_value:
        raise SemanticMappingConflict(fixed_field)
    payload[fixed_field] = fixed_value
    return fixed_field


def canonical_values_from_fixed(
    document_type: str, fixed_values: Mapping[str, Any]
) -> dict[str, Any]:
    """Normalize legacy fixed-column values into stable semantic keys."""
    result: dict[str, Any] = {}
    for fixed_field, canonical_field in FIXED_TO_CANONICAL.get(
        document_type, {}
    ).items():
        value = fixed_values.get(fixed_field)
        if value is not None:
            result[canonical_field] = _from_fixed_value(fixed_field, value)
    return result


def modules_data_to_fixed(
    document_type: str,
    modules_data: Mapping[str, Any] | None,
    field_bindings: Iterable[Mapping[str, Any]],
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Copy canonically-bound module values into formal fixed fields."""
    result = dict(payload or {})
    modules_data = modules_data or {}
    for binding in field_bindings:
        canonical = binding.get("canonical_field_key")
        if get_semantic_field(canonical) is None:
            continue
        instance_id = (
            binding.get("instance_id") or binding.get("module_id") or "imported_fields"
        )
        module = modules_data.get(instance_id) or {}
        data = module.get("data") if isinstance(module, Mapping) else None
        if not isinstance(data, Mapping):
            continue
        field_key = binding.get("field_key")
        if field_key in data:
            assign_semantic_value(document_type, result, canonical, data[field_key])
    return result


def fixed_to_modules_data(
    document_type: str,
    fixed_values: Mapping[str, Any],
    modules_data: Mapping[str, Any] | None,
    field_bindings: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Backfill canonically-bound module fields from formal fixed values."""
    result = deepcopy(dict(modules_data or {}))
    semantic_values = canonical_values_from_fixed(document_type, fixed_values)
    for binding in field_bindings:
        canonical = binding.get("canonical_field_key")
        if canonical not in semantic_values:
            continue
        instance_id = (
            binding.get("instance_id") or binding.get("module_id") or "imported_fields"
        )
        module = result.setdefault(
            instance_id,
            {"moduleId": binding.get("module_id") or "imported_fields", "data": {}},
        )
        data = module.setdefault("data", {})
        data.setdefault(binding["field_key"], semantic_values[canonical])
    return result


def _to_fixed_value(fixed_field: str, value: Any) -> Any:
    if fixed_field == "hardness_values" and not isinstance(value, str):
        import json

        return json.dumps(value, ensure_ascii=False)
    return value


def _from_fixed_value(fixed_field: str, value: Any) -> Any:
    if fixed_field == "hardness_values" and isinstance(value, str):
        import json

        try:
            return json.loads(value)
        except ValueError:
            return value
    return value

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.custom_module import FieldDefinition
from app.services.extraction_schema_service import (
    build_builtin_extraction_schema,
    build_module_extraction_schema,
    build_template_extraction_schema,
    normalize_module_fields,
    stable_legacy_field_id,
)


def _module(module_id: str = "module-1") -> SimpleNamespace:
    return SimpleNamespace(
        id=module_id,
        name="母材信息",
        module_type="wps",
        schema_version=2,
        fields={
            "material_grade": {
                "label": "材料牌号",
                "type": "text",
                "required": True,
                "canonical_field_key": "base_material.specification",
                "aliases": ["材质", "材质"],
                "ai_extract_mode": "auto",
                "confidence_threshold": 0.9,
                "use_in_rules": True,
            },
            "internal_note": {
                "label": "内部备注",
                "type": "textarea",
                "ai_extract_mode": "manual",
            },
        },
    )


def test_legacy_field_id_is_deterministic_and_existing_id_is_preserved() -> None:
    expected = stable_legacy_field_id("module-1", "grade")
    first = normalize_module_fields(
        "module-1", {"grade": {"label": "牌号", "type": "text"}}
    )
    second = normalize_module_fields(
        "module-1",
        {"grade": {"label": "新显示名称", "type": "text"}},
        existing_fields={"grade": {"field_id": "saved-id"}},
    )

    assert first["grade"]["field_id"] == expected
    assert second["grade"]["field_id"] == "saved-id"


def test_normalize_fields_handles_legacy_null_metadata() -> None:
    fields = normalize_module_fields(
        "module-1",
        {
            "grade": {
                "label": "牌号",
                "type": "text",
                "confidence_threshold": None,
                "aliases": None,
            }
        },
    )

    assert fields["grade"]["confidence_threshold"] == 0.8
    assert fields["grade"]["aliases"] == []


def test_module_schema_only_exposes_auto_fields_with_evidence() -> None:
    schema = build_module_extraction_schema(_module())
    json_schema = schema["json_schema"]
    grade = json_schema["properties"]["material_grade"]

    assert schema["source"]["version"] == "2"
    assert json_schema["required"] == ["material_grade"]
    assert "internal_note" not in json_schema["properties"]
    assert grade["required"] == ["value", "confidence", "evidence"]
    assert grade["x-weld-canonical-field"] == "base_material.specification"
    assert grade["x-weld-aliases"].count("材质") == 1
    assert grade["x-weld-rule-input"] is True
    assert schema["field_bindings"][1]["extractable"] is False


def test_builtin_pqr_schema_covers_core_and_test_facts_without_qualification() -> None:
    schema = build_builtin_extraction_schema("pqr")
    properties = schema["json_schema"]["properties"]

    assert schema["source"]["kind"] == "builtin"
    assert schema["json_schema"]["required"] == ["title", "pqr_number"]
    assert properties["pqr_number"]["x-weld-canonical-field"] == "document.number"
    assert properties["test_date"]["properties"]["value"]["format"] == "date-time"
    assert (
        properties["base_material_thickness"]["properties"]["value"]["type"] == "number"
    )
    assert "rt_result" in properties
    assert "tensile_strength_actual" in properties
    assert "charpy_energy_avg" in properties
    assert "hardness_values" in properties
    assert "thickness_range_qualified" not in properties
    assert "position_qualified" not in properties


def test_builtin_wps_schema_maps_directly_to_formal_fields() -> None:
    schema = build_builtin_extraction_schema("wps")
    properties = schema["json_schema"]["properties"]

    assert schema["json_schema"]["required"] == ["title", "wps_number"]
    assert properties["weld_passes"]["properties"]["value"]["type"] == "integer"
    assert properties["pwht_required"]["properties"]["value"]["type"] == "boolean"
    assert "wpqr_number" in properties
    assert properties["welding_process_rows"]["properties"]["value"]["type"] == "array"
    assert properties["weld_layer_rows"]["properties"]["value"]["type"] == "array"
    assert (
        properties["welding_parameter_rows"]["properties"]["value"]["type"] == "array"
    )


def test_builtin_welder_schema_covers_identity_certificate_and_multiple_projects() -> (
    None
):
    schema = build_builtin_extraction_schema("welder")
    properties = schema["json_schema"]["properties"]

    assert "welder_code" in properties
    assert "id_number" in properties
    assert "certification_number" in properties
    assert properties["qualified_projects"]["properties"]["value"]["type"] == "array"
    columns = properties["qualified_projects"]["properties"]["value"][
        "x-weld-table-definition"
    ]["columns"]
    assert {
        "welding_process",
        "welding_position",
        "material_group",
        "thickness_range",
        "diameter_range",
    }.issubset({item["key"] for item in columns})
    assert properties["welder_records"]["properties"]["value"]["type"] == "array"


def test_builtin_schema_rejects_unknown_document_type() -> None:
    with pytest.raises(ValueError, match="没有内置提取 Schema"):
        build_builtin_extraction_schema("equipment")


def test_derived_semantic_fields_are_not_sent_to_ai() -> None:
    module = SimpleNamespace(
        id="qualification-module",
        name="资格范围",
        module_type="pqr",
        schema_version=1,
        fields={
            "qualified_thickness": {
                "label": "合格厚度范围",
                "type": "text",
                "canonical_field_key": "qualification.pqr_thickness_range",
                "ai_extract_mode": "auto",
            }
        },
    )

    schema = build_module_extraction_schema(module)

    assert schema["json_schema"]["properties"] == {}
    assert schema["field_bindings"][0]["extractable"] is False


def test_schema_supports_object_list_and_repeated_table_shapes() -> None:
    module = SimpleNamespace(
        id="shape-module",
        name="结构字段",
        module_type="pqr",
        schema_version=1,
        fields={
            "object_value": {"label": "对象", "type": "object"},
            "list_value": {"label": "列表", "type": "array"},
            "rows": {"label": "重复表格", "type": "table"},
        },
    )

    properties = build_module_extraction_schema(module)["json_schema"]["properties"]

    assert properties["object_value"]["properties"]["value"]["type"] == "object"
    assert properties["list_value"]["properties"]["value"]["type"] == "array"
    assert properties["rows"]["properties"]["value"]["items"]["type"] == "object"


def test_template_schema_supports_repeated_instances_and_missing_modules() -> None:
    module = _module()
    template = SimpleNamespace(
        id="template-1",
        name="组合模板",
        module_type="wps",
        version="3",
        module_instances=[
            {"instanceId": "second", "moduleId": module.id, "order": 2},
            {"instanceId": "first", "moduleId": module.id, "order": 1},
            {"instanceId": "missing", "moduleId": "unknown"},
        ],
    )

    schema = build_template_extraction_schema(template, [module])

    assert list(schema["json_schema"]["properties"]) == ["first", "second"]
    assert len(schema["field_bindings"]) == 4
    assert schema["warnings"] == [{"code": "MISSING_MODULE", "module_id": "unknown"}]


def test_field_definition_rejects_unknown_semantic_key() -> None:
    with pytest.raises(ValidationError, match="未知的系统语义字段"):
        FieldDefinition(
            label="未知字段",
            type="text",
            canonical_field_key="unknown.field",
        )


def test_field_definition_rejects_non_uuid_field_id() -> None:
    with pytest.raises(ValidationError, match="field_id 必须是有效 UUID"):
        FieldDefinition(label="牌号", type="text", field_id="not-a-uuid")

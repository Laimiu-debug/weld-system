from app.domain.semantic_field_mapping import (
    CANONICAL_TO_FIXED,
    FIXED_TO_CANONICAL,
    SemanticMappingConflict,
    assign_semantic_value,
    canonical_field_for_fixed,
    canonical_values_from_fixed,
    fixed_field_for,
    fixed_to_modules_data,
    modules_data_to_fixed,
)
from app.domain.semantic_fields import get_semantic_field, list_semantic_fields
from app.schemas.pqr import PQRCreate
from app.schemas.wps import WPSCreate


def _bindings() -> list[dict]:
    return [
        {
            "module_id": "material-module",
            "instance_id": "material-1",
            "field_key": "material_grade",
            "canonical_field_key": "base_material.specification",
        }
    ]


def test_semantic_registry_exposes_contract_metadata_and_welder_fields() -> None:
    number = get_semantic_field("document.number")
    qualification = get_semantic_field("qualification.items")

    assert number is not None
    assert number.to_dict()["required_for"] == ["wps", "pqr"]
    assert number.to_dict()["region_hints"] == ["文件表头", "基本信息"]
    assert number.to_dict()["validation"]["max_length"] == 50
    assert qualification is not None
    assert qualification.value_shape == "table"
    assert qualification.field_kind == "fact"
    assert "welder" in qualification.document_types
    assert len(list_semantic_fields("welder")) >= 10


def test_fixed_and_canonical_registry_is_bidirectional() -> None:
    assert fixed_field_for("wps", "document.number") == "wps_number"
    assert canonical_field_for_fixed("pqr", "pqr_number") == "document.number"
    assert canonical_values_from_fixed(
        "pqr", {"pqr_number": "PQR-001", "base_material_thickness": 12.0}
    ) == {
        "document.number": "PQR-001",
        "base_material.thickness": 12.0,
    }


def test_every_mapping_references_a_real_semantic_key_and_formal_field() -> None:
    models = {"wps": WPSCreate, "pqr": PQRCreate}
    for document_type, mappings in FIXED_TO_CANONICAL.items():
        assert len(mappings) == len(CANONICAL_TO_FIXED[document_type])
        for fixed_field, canonical_field in mappings.items():
            assert fixed_field in models[document_type].model_fields
            assert get_semantic_field(canonical_field) is not None


def test_semantic_assignment_detects_conflicting_formal_values() -> None:
    payload = {"base_material_spec": "Q345R"}

    try:
        assign_semantic_value("pqr", payload, "base_material.specification", "16MnDR")
    except SemanticMappingConflict as exc:
        assert exc.args[0] == "base_material_spec"
    else:
        raise AssertionError("conflicting semantic values must be rejected")


def test_modules_and_fixed_columns_round_trip_through_bindings() -> None:
    modules = {
        "material-1": {
            "moduleId": "material-module",
            "data": {"material_grade": "Q345R"},
        }
    }
    fixed = modules_data_to_fixed("pqr", modules, _bindings())
    assert fixed["base_material_spec"] == "Q345R"

    rebuilt = fixed_to_modules_data(
        "pqr",
        {"base_material_spec": "16MnDR"},
        {},
        _bindings(),
    )
    assert rebuilt["material-1"]["data"]["material_grade"] == "16MnDR"


def test_legacy_json_fixed_field_is_normalized() -> None:
    payload: dict = {}
    assign_semantic_value("pqr", payload, "test.hardness.values", [210, 215])
    assert payload["hardness_values"] == "[210, 215]"
    assert canonical_values_from_fixed("pqr", payload)["test.hardness.values"] == [
        210,
        215,
    ]

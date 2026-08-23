from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.sequence import StepDependency, WeldSequenceRevision, WeldSequenceStep
from app.schemas.sequence import SequenceGenerate, SequenceReorder
from app.services.sequence_service import (
    build_pressure_vessel_blueprint,
    compare_sequence_steps,
    is_production_eligible,
    topological_order,
    validate_sequence,
)


def _part(part_id, name):
    return SimpleNamespace(id=part_id, name=name)


def _joint(joint_id, number, a, b):
    return SimpleNamespace(
        id=joint_id,
        weld_number=number,
        part_a_id=a,
        part_b_id=b,
    )


def _requirement(**overrides):
    values = {
        "special_requirements": None,
        "nde_methods": ["RT"],
        "nde_rate": "100%",
        "pwht_required": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _freeze(freeze_id, joint_id):
    return SimpleNamespace(
        id=freeze_id,
        weld_joint_id=joint_id,
        frozen_snapshot={
            "wps": {"wps_number": f"WPS-{joint_id}"},
            "pqr": {"pqr_number": f"PQR-{joint_id}"},
            "requirement": {},
        },
    )


def _first_family():
    parts = {
        "shell1": _part("shell1", "筒节一"),
        "shell2": _part("shell2", "筒节二"),
        "head": _part("head", "封头"),
        "nozzle": _part("nozzle", "接管 N1"),
    }
    joints = [
        _joint("j1", "纵缝-A", "shell1", "shell1"),
        _joint("j2", "环缝-B", "shell1", "shell2"),
        _joint("j3", "封头环缝-C", "shell2", "head"),
        _joint("j4", "接管焊缝-D", "shell1", "nozzle"),
    ]
    requirements = {
        "j1": _requirement(),
        "j2": _requirement(),
        "j3": _requirement(pwht_required=True),
        "j4": _requirement(special_requirements="必须在封闭前完成内侧焊接"),
    }
    freezes = {item.id: _freeze(f"f-{item.id}", item.id) for item in joints}
    return joints, requirements, parts, freezes


def test_first_pressure_vessel_family_builds_complete_acyclic_sequence():
    steps, dependencies, validation = build_pressure_vessel_blueprint(*_first_family())
    assert validation["valid"] is True
    assert {item["weld_joint_id"] for item in steps if item["step_type"] == "weld"} == {
        "j1",
        "j2",
        "j3",
        "j4",
    }
    assert {item["step_type"] for item in steps} >= {
        "assembly",
        "weld",
        "nde",
        "pwht",
        "closure",
        "inspection",
    }
    order = {item["step_code"]: item["order_index"] for item in steps}
    assert order["WELD-j4"] < order["CLOSE-VESSEL"] < order["WELD-j3"]
    assert all(
        order[item["predecessor_code"]] < order[item["successor_code"]]
        for item in dependencies
    )


def test_ai_preference_cannot_override_mandatory_dependency():
    joints, requirements, parts, freezes = _first_family()
    steps, _, validation = build_pressure_vessel_blueprint(
        joints,
        requirements,
        parts,
        freezes,
        preferred_codes=["WELD-j1", "ASM-j1", "PREP-SHELL"],
    )
    order = {item["step_code"]: item["order_index"] for item in steps}
    assert order["PREP-SHELL"] < order["ASM-j1"] < order["WELD-j1"]
    assert validation["valid"] is True


def test_cycle_and_missing_p4_freeze_are_blocking_errors():
    _, errors = topological_order(["A", "B"], [("A", "B"), ("B", "A")])
    assert errors and "循环依赖" in errors[0]
    steps = [
        {
            "step_code": "ASM",
            "step_type": "assembly",
            "order_index": 1,
            "match_freeze_id": None,
        },
        {
            "step_code": "WELD",
            "step_type": "weld",
            "order_index": 2,
            "match_freeze_id": None,
        },
    ]
    dependencies = [
        {
            "predecessor_code": "ASM",
            "successor_code": "WELD",
            "dependency_type": "assembly",
        }
    ]
    result = validate_sequence(steps, dependencies)
    assert result["valid"] is False
    assert "MISSING_APPROVED_WPS" in {item["code"] for item in result["issues"]}


def test_sequence_models_are_workspace_scoped_and_freezable():
    for model in (WeldSequenceRevision, WeldSequenceStep, StepDependency):
        assert {
            "user_id",
            "workspace_type",
            "company_id",
            "factory_id",
            "access_level",
            "created_by",
        } <= set(model.__table__.columns.keys())
    assert {"frozen_snapshot", "frozen_hash", "approval_snapshot_hash"} <= set(
        WeldSequenceRevision.__table__.columns.keys()
    )


def test_engineer_change_diff_is_preserved_and_unapproved_never_releases():
    difference = compare_sequence_steps(
        [
            {"step_code": "A", "order_index": 1},
            {"step_code": "B", "order_index": 2},
        ],
        [
            {"step_code": "B", "order_index": 1},
            {"step_code": "A", "order_index": 2},
        ],
    )
    assert {item["step_code"] for item in difference["moved"]} == {"A", "B"}
    assert is_production_eligible("draft", "hash", 3, 3) is False
    assert is_production_eligible("pending", "hash", 3, 3) is False
    assert is_production_eligible("approved", None, 3, 3) is False
    assert is_production_eligible("approved", "hash", 2, 3) is False
    assert is_production_eligible("approved", "hash", 3, 3) is True


def test_sequence_inputs_reject_unknown_strategy_duplicate_steps_and_bad_locks():
    with pytest.raises(ValidationError):
        SequenceGenerate(strategies={"unsafe": True})
    with pytest.raises(ValidationError):
        SequenceGenerate(ai_step_codes=["A", "A"])
    with pytest.raises(ValidationError):
        SequenceReorder(
            ordered_step_ids=["A"],
            locked_step_ids=["B"],
            change_summary="人工调整",
        )

from types import SimpleNamespace as NS
from itertools import product

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.sequence import SequenceRecalculate, SequenceStructure
from app.schemas.production_release import ExecutionRecordRequest
from app.services.sequence_structure_service import resolve_structure
from app.services.sequence_service import build_pressure_vessel_blueprint


def inputs():
    parts = {p: NS(id=p, name="无语义编号" + p) for p in ["s", "h", "n"]}
    joints = [
        NS(id=str(i), weld_number=str(i), part_a_id="s", part_b_id=p, length_mm=1250)
        for i, p in enumerate(["s", "s", "n", "h"])
    ]
    requirements = {
        j.id: NS(
            nde_methods=["RT"],
            nde_rate="100%",
            pwht_required=True,
            treatment_plan=[{"code":"H1", "scope":"local", "temperature_min":600, "temperature_max":620, "hold_minutes":60, "nde_after":["RT"]}],
            special_requirements="封闭前内部焊接" if j.id == "2" else "",
        )
        for j in joints
    }
    freezes = {j.id: NS(id="f" + j.id, frozen_snapshot={}) for j in joints}
    return joints, requirements, parts, freezes


@pytest.mark.parametrize(
    "segmented,skip,symmetric", list(product([False, True], repeat=3))
)
def test_strategies_cover_length_once_and_cannot_move_detection_or_closure_earlier(
    segmented, skip, symmetric
):
    joints, reqs, parts, freezes = inputs()
    structure = resolve_structure(
        parts,
        joints,
        {
            "part_roles": {"s": "shell", "h": "head", "n": "nozzle"},
            "closure_joint_ids": ["3"],
            "segment_length_mm": 500,
        },
    )
    steps, edges, validation = build_pressure_vessel_blueprint(
        joints,
        reqs,
        parts,
        freezes,
        {"segmented": segmented, "skip_weld": skip, "symmetric": symmetric},
        ["CLOSE-VESSEL", "NDE-2", "WELD-2-S003", "WELD-2-S002", "WELD-2-S001"],
        structure,
    )
    assert validation["valid"]
    ranks = {s["step_code"]: s["order_index"] for s in steps}
    assert all(ranks[e["predecessor_code"]] < ranks[e["successor_code"]] for e in edges)
    assert ranks["NDE-2-H1-after-RT"] < ranks["CLOSE-VESSEL"]
    for joint in joints:
        welds = [
            s
            for s in steps
            if s["step_type"] == "weld" and s["weld_joint_id"] == joint.id
        ]
        assert all(s["order_index"] < ranks["NDE-" + joint.id + "-H1-after-RT"] for s in welds)
        if segmented or skip:
            segments = [s["process_parameters"]["segment"] for s in welds]
            assert sum(s["length_mm"] for s in segments) == 1250
            assert sorted((s["start_mm"], s["end_mm"]) for s in segments) == [
                (0, 500),
                (500, 1000),
                (1000, 1250),
            ]
            assert [s["index"] for s in segments] == (
                [1, 3, 2] if skip or symmetric else [1, 2, 3]
            )
        else:
            assert len(welds) == 1


def test_unconfirmed_structure_does_not_infer_vessel_from_part_names():
    joints, reqs, parts, freezes = inputs()
    for p in parts.values():
        p.name = "压力容器筒体封头接管"
    structure = resolve_structure(parts, joints)
    assert structure["template"] == "generic"
    steps, _, _ = build_pressure_vessel_blueprint(
        joints, reqs, parts, freezes, structure=structure
    )
    assert "PREP-GENERAL" in {s["step_code"] for s in steps}
    assert "CLOSE-VESSEL" not in {s["step_code"] for s in steps}


@pytest.mark.parametrize(
    "options",
    [
        {"part_roles": {"foreign": "shell"}},
        {"template": "pressure_vessel"},
        {"closure_joint_ids": ["foreign"]},
        {"part_roles": {"s": "shell", "h": "head"}},
        {"part_roles": {"s": "shell", "h": "head"}, "closure_joint_ids": ["0"]},
    ],
)
def test_ambiguous_or_foreign_structure_is_rejected(options):
    joints, _, parts, _ = inputs()
    with pytest.raises(HTTPException):
        resolve_structure(parts, joints, options)


@pytest.mark.parametrize("length", [None, 0, -1, float("inf"), float("nan")])
def test_segmentation_requires_measured_positive_length(length):
    joints, reqs, parts, freezes = inputs()
    joints[0].length_mm = length
    with pytest.raises(HTTPException):
        build_pressure_vessel_blueprint(
            joints,
            reqs,
            parts,
            freezes,
            {"segmented": True},
            structure=resolve_structure(parts, joints),
        )


@pytest.mark.parametrize("value", [0, -1, float("inf")])
def test_invalid_segment_length(value):
    with pytest.raises(ValidationError):
        SequenceStructure(segment_length_mm=value)


def test_recalculation_rejects_unknown_strategy():
    with pytest.raises(ValidationError):
        SequenceRecalculate(strategies={"unsafe": True})


@pytest.mark.parametrize("value", [True, "ten", float("inf"), -1])
def test_execution_rejects_invalid_current(value):
    with pytest.raises(ValidationError):
        ExecutionRecordRequest(
            idempotency_key="request-1", actual_parameters={"current": value}
        )

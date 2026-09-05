from types import SimpleNamespace as NS
from copy import deepcopy

import pytest
from fastapi import HTTPException

from app.services.sequence_service import build_pressure_vessel_blueprint
from app.services.sequence_treatment_service import validate_treatment_plan


def stage(**values):
    return {
        "code": "H1",
        "scope": "local",
        "temperature_min": 600,
        "temperature_max": 620,
        "hold_minutes": 60,
        "nde_before": ["VT"],
        "nde_after": ["RT"],
        **values,
    }


def graph(plans):
    joints = [
        NS(id=str(i), weld_number=f"W{i}", part_a_id="p", part_b_id="p", length_mm=1200)
        for i in range(len(plans))
    ]
    reqs = {
        j.id: NS(
            pwht_required=True,
            treatment_plan=plan,
            nde_methods=["RT"],
            nde_rate="100%",
            review_status="accepted",
            special_requirements=None,
        )
        for j, plan in zip(joints, plans)
    }
    freezes = {j.id: NS(id="f" + j.id, frozen_snapshot={}) for j in joints}
    return build_pressure_vessel_blueprint(
        joints,
        reqs,
        {"p": NS(id="p", name="Plate")},
        freezes,
        {"segmented": True},
        structure={
            "template": "generic",
            "part_roles": {},
            "closure_joint_ids": [],
            "segment_length_mm": 500,
        },
    )


def test_local_multistage_plan_keeps_each_inspection_and_segment_dependency():
    steps, edges, validation = graph(
        [
            [
                stage(),
                stage(
                    code="H2", temperature_min=610, nde_before=["UT"], nde_after=["MT"]
                ),
            ]
        ]
    )
    assert validation["valid"]
    ranks = {s["step_code"]: s["order_index"] for s in steps}
    assert (
        ranks["NDE-0-H1-before-VT"]
        < ranks["PWHT-LOCAL-0-H1"]
        < ranks["NDE-0-H1-after-RT"]
        < ranks["PWHT-LOCAL-0-H2"]
        < ranks["NDE-0-H2-after-MT"]
    )
    assert all(
        ranks[s["step_code"]] < ranks["NDE-0-H1-before-VT"]
        for s in steps
        if s["step_type"] == "weld"
    )
    assert all(ranks[e["predecessor_code"]] < ranks[e["successor_code"]] for e in edges)
    assert len([s for s in steps if s["step_type"] == "pwht"]) == 2


def test_global_batch_is_shared_and_waits_for_all_welds_and_before_tests():
    plan = [stage(scope="global", group="FURNACE1")]
    steps, edges, validation = graph([plan, deepcopy(plan)])
    assert validation["valid"]
    heat = [s for s in steps if s["step_type"] == "pwht"]
    assert len(heat) == 1
    assert set(heat[0]["process_parameters"]["affected_joint_ids"]) == {"0", "1"}
    incoming = {
        e["predecessor_code"]
        for e in edges
        if e["successor_code"] == heat[0]["step_code"]
    }
    assert {s["step_code"] for s in steps if s["step_type"] == "weld"} <= incoming
    assert {"NDE-0-H1-before-VT", "NDE-1-H1-before-VT"} <= incoming


def test_conflicting_shared_group_and_omitted_mandatory_test_are_rejected():
    with pytest.raises(HTTPException, match="冲突"):
        graph(
            [
                [stage(scope="global", group="G")],
                [stage(scope="global", group="G", hold_minutes=90)],
            ]
        )
    with pytest.raises(HTTPException, match="遗漏"):
        graph([[stage(nde_after=[])]])
    with pytest.raises(HTTPException, match="需要明确"):
        graph([[]])


@pytest.mark.parametrize(
    "value",
    [
        None,
        "bad",
        {"scope": "local"},
        [stage(temperature_min=700)],
        [stage(scope="global")],
        [stage(hold_minutes=-1)],
        [stage(temperature_min=float("nan"))],
        [stage(), stage()],
    ],
)
def test_plan_contract_rejects_ambiguous_values(value):
    if value is None:
        assert validate_treatment_plan(value) == []
    else:
        with pytest.raises(HTTPException):
            validate_treatment_plan(value)

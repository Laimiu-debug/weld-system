from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.matching import (
    WPSCapabilityGap,
    WPSMatchCandidate,
    WPSMatchCriterion,
    WPSMatchFreeze,
    WPSMatchRun,
)
from app.models.wps import WPS
from app.schemas.matching import MatchRunCreate
from app.services.matching_service import (
    DIMENSIONS,
    build_weld_requirement,
    evaluate_candidate,
)


def _wps(**overrides):
    values = {
        "joint_design": "butt",
        "groove_type": "V",
        "filler_material_spec": "NB/T 47018",
        "filler_material_classification": "E5015",
        "wps_number": "WPS-01",
    }
    values.update(overrides)
    return WPS(**values)


def _capability(**scope_overrides):
    scope = {
        "standard": "NB/T 47014—2023",
        "welding_processes": ["GTAW"],
        "material_groups": ["Fe-1"],
        "positions": ["PA"],
        "thickness": {"min_mm": 3, "max_mm": 20},
        "diameter": {"applicable": False},
        "pwht": {"performed": False},
        "impact": {"required": False},
    }
    scope.update(scope_overrides)
    return {
        "link_id": "link-1",
        "rule_pack_version": "1.0.0",
        "supported_processes": ["GTAW"],
        "qualified_scope": scope,
    }


def _requirement(**overrides):
    values = {
        "material_groups": ["Fe-1"],
        "thickness_mm": 10,
        "diameter_applicable": False,
        "diameter_mm": None,
        "joint_type": "butt",
        "groove_type": "V",
        "welding_process": "GTAW",
        "welding_position": "PA",
        "filler_material_spec": "NB/T 47018",
        "filler_material_classification": "E5015",
        "pwht_required": False,
        "impact_required": False,
        "impact_temperature_c": None,
    }
    values.update(overrides)
    return values


def test_complete_coverage_is_eligible_and_explains_every_dimension():
    result = evaluate_candidate(_requirement(), _capability(), _wps())
    assert result["decision"] == "eligible"
    assert result["score"] == 100
    assert {item["dimension"] for item in result["criteria"]} == set(DIMENSIONS)
    assert all(item["status"] == "pass" for item in result["criteria"])


def test_explicit_failure_makes_candidate_ineligible():
    result = evaluate_candidate(
        _requirement(material_groups=["Fe-8"]), _capability(), _wps()
    )
    assert result["decision"] == "not_eligible"
    material = next(x for x in result["criteria"] if x["dimension"] == "material_group")
    assert material["status"] == "fail"


def test_boundary_and_missing_data_require_human_confirmation():
    boundary = evaluate_candidate(_requirement(thickness_mm=20), _capability(), _wps())
    assert boundary["decision"] == "needs_confirmation"
    assert (
        next(x for x in boundary["criteria"] if x["dimension"] == "thickness")["status"]
        == "boundary"
    )
    missing = evaluate_candidate(
        _requirement(welding_process=None), _capability(), _wps()
    )
    assert missing["decision"] == "needs_confirmation"
    assert (
        next(x for x in missing["criteria"] if x["dimension"] == "process")["status"]
        == "insufficient"
    )


def test_joint_aliases_do_not_create_false_mismatch():
    result = evaluate_candidate(
        _requirement(joint_type="对接接头", groove_type="V形"),
        _capability(),
        _wps(joint_design="butt joint", groove_type="V groove"),
    )
    joint = next(x for x in result["criteria"] if x["dimension"] == "joint")
    assert joint["status"] == "pass"


def test_weld_requirement_uses_both_part_materials_and_requires_both_thicknesses():
    joint = SimpleNamespace(
        id="j1",
        weld_number="W1",
        part_a_id="a",
        part_b_id="b",
        joint_type="butt",
        groove_type="V",
        weld_position="PA",
    )
    parts = {
        "a": SimpleNamespace(
            id="a", part_number="A", material_group="Fe-1", thickness_mm=8
        ),
        "b": SimpleNamespace(
            id="b", part_number="B", material_group="Fe-2", thickness_mm=12
        ),
    }
    requirement = SimpleNamespace(
        material_group=None,
        diameter_applicable=False,
        diameter_mm=None,
        welding_process="GTAW",
        filler_material_spec=None,
        filler_material_classification=None,
        pwht_required=False,
        impact_required=False,
        impact_temperature=None,
    )
    result = build_weld_requirement(joint, requirement, parts)
    assert result["material_groups"] == ["Fe-1", "Fe-2"]
    assert result["thickness_mm"] == 12
    parts["b"].thickness_mm = None
    assert build_weld_requirement(joint, requirement, parts)["thickness_mm"] is None


def test_explicit_requirement_material_group_overrides_drawing_inference():
    joint = SimpleNamespace(
        id="j1",
        weld_number="W1",
        part_a_id="a",
        part_b_id="b",
        joint_type="butt",
        groove_type="V",
        weld_position="PA",
    )
    parts = {
        "a": SimpleNamespace(
            id="a", part_number="A", material_group="Fe-1", thickness_mm=8
        ),
        "b": SimpleNamespace(
            id="b", part_number="B", material_group="Fe-2", thickness_mm=12
        ),
    }
    requirement = SimpleNamespace(
        material_group="Fe-8",
        diameter_applicable=False,
        diameter_mm=None,
        welding_process="GTAW",
        filler_material_spec=None,
        filler_material_classification=None,
        pwht_required=False,
        impact_required=False,
        impact_temperature=None,
    )
    assert build_weld_requirement(joint, requirement, parts)["material_groups"] == [
        "Fe-8"
    ]


def test_policy_weights_only_accept_supported_dimensions_and_safe_range():
    assert MatchRunCreate(policy_weights={"thickness": 25}).policy_weights == {
        "thickness": 25
    }
    with pytest.raises(ValidationError):
        MatchRunCreate(policy_weights={"unknown": 1})
    with pytest.raises(ValidationError):
        MatchRunCreate(policy_weights={"thickness": 101})


def test_matching_models_freeze_versions_and_workspace_scope():
    for model in (
        WPSMatchRun,
        WPSMatchCandidate,
        WPSMatchCriterion,
        WPSCapabilityGap,
        WPSMatchFreeze,
    ):
        assert {
            "user_id",
            "workspace_type",
            "company_id",
            "factory_id",
            "access_level",
            "created_by",
        } <= set(model.__table__.columns.keys())
    assert {
        "weld_requirement_hash",
        "wps_snapshot_hash",
        "pqr_snapshot_hash",
        "rule_snapshot_hash",
        "frozen_snapshot",
    } <= set(WPSMatchFreeze.__table__.columns.keys())

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.models.pqr import PQR
from app.models.qualification import PQRQualificationResult, QualificationRulePack
from app.models.wps import WPS
from app.schemas.qualification import WPSPQRSupportCreate
from app.services.qualification_service import (
    QualificationService,
    evaluate_nbt47014_2023,
)


def _facts(**overrides):
    values = {
        "qualification_result": "qualified",
        "approval_status": "approved",
        "welding_processes": "GTAW",
        "material_group": "Fe-1",
        "test_piece_thickness_mm": 10,
        "test_piece_form": "plate",
        "joint_type": "butt",
        "welding_position": "PA",
        "pwht_performed": False,
        "impact_test_performed": False,
    }
    values.update(overrides)
    return values


def test_nbt47014_complete_plate_facts_produce_explainable_scope() -> None:
    result = evaluate_nbt47014_2023(_facts())

    assert result["outcome"] == "qualified"
    assert result["qualification_scope"]["thickness"]["min_mm"] == 5
    assert result["qualification_scope"]["thickness"]["max_mm"] == 20
    assert result["qualification_scope"]["diameter"]["applicable"] is False
    assert result["qualification_scope"]["positions"] == ["PA"]
    assert result["basis"][1]["rule_id"] == "NBT47014-2023-THICKNESS-CONSERVATIVE"


@pytest.mark.parametrize(
    ("thickness", "minimum", "maximum"),
    [(1.0, 1.0, 2.0), (2.0, 1.5, 4.0), (10.0, 5.0, 20.0), (20.0, 5.0, 40.0)],
)
def test_nbt47014_thickness_segments(thickness, minimum, maximum) -> None:
    scope = evaluate_nbt47014_2023(_facts(test_piece_thickness_mm=thickness))[
        "qualification_scope"
    ]["thickness"]
    assert (scope["min_mm"], scope["max_mm"]) == (minimum, maximum)


def test_nbt47014_missing_critical_fact_never_guesses_scope() -> None:
    result = evaluate_nbt47014_2023(_facts(welding_position=None))

    assert result["outcome"] == "insufficient_data"
    assert "welding_position" in result["missing_fields"]
    assert result["qualification_scope"] == {}


def test_nbt47014_missing_qualification_conclusion_is_not_treated_as_failure() -> None:
    result = evaluate_nbt47014_2023(_facts(qualification_result=None))

    assert result["outcome"] == "insufficient_data"
    assert "qualification_result" in result["missing_fields"]
    assert result["qualification_scope"] == {}


def test_nbt47014_combined_process_requires_per_process_deposit() -> None:
    result = evaluate_nbt47014_2023(_facts(welding_processes=["GTAW", "SMAW"]))

    assert result["outcome"] == "insufficient_data"
    assert "deposited_thickness_by_process.GTAW" in result["missing_fields"]
    assert any(
        item["code"] == "COMBINED_PROCESS_REVIEW"
        for item in result["boundary_conditions"]
    )


def test_nbt47014_pipe_diameter_is_not_silently_broadened() -> None:
    result = evaluate_nbt47014_2023(
        _facts(test_piece_form="pipe", test_piece_diameter_mm=168.3)
    )

    assert result["outcome"] == "needs_confirmation"
    assert result["qualification_scope"]["diameter"]["min_mm"] == 168.3
    assert result["requires_human_confirmation"] is True


def test_nbt47014_unapproved_pqr_is_not_qualified() -> None:
    result = evaluate_nbt47014_2023(_facts(approval_status="draft"))
    assert result["outcome"] == "not_qualified"
    assert result["qualification_scope"] == {}


def test_rule_pack_lifecycle_does_not_allow_skipping_review() -> None:
    db = Mock()
    pack = QualificationRulePack(
        id="pack-1",
        status="draft",
        compliance_metadata={
            "contains_standard_text": False,
            "citation_mode": "locator",
        },
    )
    service = QualificationService(db)
    service.get_rule_pack = Mock(return_value=pack)

    with pytest.raises(HTTPException) as exc:
        service.transition_rule_pack("pack-1", "published")
    assert exc.value.status_code == 409

    pack.status = "review"
    published = service.transition_rule_pack("pack-1", "published")
    assert published.status == "published"
    assert published.published_at is not None


def test_explicit_recalculation_creates_new_result_and_preserves_history() -> None:
    now = datetime(2026, 8, 23, 12, 0, 0)
    pqr = PQR(
        id=20,
        user_id=7,
        workspace_type="personal",
        access_level="private",
        pqr_number="PQR-20",
        title="PQR",
        status="approved",
        qualification_result="qualified",
        welding_process="GTAW",
        base_material_group="Fe-1",
        base_material_thickness=10,
        joint_design="butt",
        modules_data={"test_piece_form": "plate", "welding_position": "PA"},
        created_by=7,
        created_at=now,
        updated_at=now,
    )
    pack = QualificationRulePack(
        id="pack-1",
        standard_code="NB/T 47014",
        edition="2023",
        version="1.0.0",
        status="published",
    )
    previous = PQRQualificationResult(
        id="old-result",
        pqr_id=20,
        is_current=True,
        calculated_at=now,
    )
    existing_query = Mock()
    existing_query.filter.return_value.first.return_value = previous
    current_query = Mock()
    current_query.filter.return_value.order_by.return_value.first.return_value = (
        previous
    )
    db = Mock()
    db.query.side_effect = [existing_query, current_query]
    service = QualificationService(db)
    service._get_pqr = Mock(return_value=pqr)
    service.get_rule_pack = Mock(return_value=pack)

    result = service.calculate_pqr(
        20,
        SimpleNamespace(id=7),
        SimpleNamespace(),
        force_recalculate=True,
        fact_overrides={"test_piece_form": "plate"},
    )

    assert previous.is_current is False
    assert result.id != previous.id
    assert result.supersedes_result_id == previous.id
    assert result.is_current is True
    assert result.rule_pack_version == "1.0.0"
    assert result.input_snapshot["pqr"]["id"] == 20


def test_calculation_cannot_override_approval_or_test_facts() -> None:
    service = QualificationService(Mock())
    service._get_pqr = Mock(return_value=SimpleNamespace())
    service.get_rule_pack = Mock(
        return_value=SimpleNamespace(
            standard_code="NB/T 47014", edition="2023", version="1.0.0"
        )
    )
    service._pqr_facts = Mock(return_value={})

    with pytest.raises(HTTPException) as exc:
        service.calculate_pqr(
            20,
            SimpleNamespace(id=7),
            SimpleNamespace(),
            fact_overrides={"approval_status": "approved"},
        )

    assert exc.value.status_code == 422
    assert "approval_status" in exc.value.detail


def test_support_link_freezes_exact_wps_pqr_versions_and_scope() -> None:
    now = datetime(2026, 8, 23, 12, 0, 0)
    wps = WPS(
        id=10,
        user_id=7,
        workspace_type="personal",
        access_level="private",
        wps_number="WPS-10",
        title="WPS",
        revision="B",
        status="approved",
        created_by=7,
        created_at=now,
        updated_at=now,
    )
    pqr = PQR(
        id=20,
        user_id=7,
        workspace_type="personal",
        access_level="private",
        pqr_number="PQR-20",
        title="PQR",
        status="approved",
        qualification_result="qualified",
        created_by=7,
        created_at=now,
        updated_at=now,
    )
    qualification = PQRQualificationResult(
        id="result-1",
        pqr_id=20,
        outcome="qualified",
        pqr_version_key="record@2026-08-23T12:00:00",
        is_current=True,
        result={
            "qualification_scope": {
                "welding_processes": ["GTAW"],
                "thickness": {"min_mm": 5, "max_mm": 20},
            }
        },
    )
    qualification_query = Mock()
    qualification_query.filter.return_value.first.return_value = qualification
    duplicate_query = Mock()
    duplicate_query.filter.return_value.first.return_value = None
    db = Mock()
    db.query.side_effect = [qualification_query, duplicate_query]
    service = QualificationService(db)
    service._get_wps = Mock(return_value=wps)
    service._get_pqr = Mock(return_value=pqr)

    link = service.create_support_link(
        10,
        WPSPQRSupportCreate(
            pqr_id=20,
            qualification_result_id="result-1",
            confirmation_status="confirmed",
        ),
        SimpleNamespace(id=7),
        SimpleNamespace(),
    )

    assert link.wps_version_key.startswith("B@")
    assert link.pqr_version_key.startswith("record@")
    assert len(link.wps_snapshot_hash) == 64
    assert len(link.pqr_snapshot_hash) == 64
    assert link.supported_processes == ["GTAW"]
    assert link.qualified_scope["thickness"]["max_mm"] == 20
    assert link.confirmation_status == "confirmed"

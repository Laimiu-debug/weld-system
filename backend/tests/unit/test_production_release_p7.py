"""P7 conversion, qualification and traceability contract tests."""
from datetime import date, timedelta

from app.models.production import ProductionTask
from app.models.production_release import (
    ProductionExecutionTrace,
    ProductionQualityNode,
    ProductionReleaseBatch,
    ProductionResourceAuthorization,
    ProductionSequenceChangeRequest,
)
from app.models.welder import Welder, WelderCertification
from app.models.wps import WPS
from app.services.production_release_service import (
    canonical_hash,
    evaluate_welder_qualification,
    sequence_step_to_task_kind,
)
from app.services.sequence_service import change_request_allows_recalculation


def _welder(**values):
    defaults = {
        "id": 7,
        "is_active": True,
        "status": "active",
        "certification_status": "valid",
        "qualified_processes": '["GTAW", "SMAW"]',
        "qualified_positions": '["2G", "5G"]',
    }
    defaults.update(values)
    return Welder(**defaults)


def _wps(**values):
    defaults = {
        "id": 9,
        "wps_number": "WPS-09",
        "status": "approved",
        "welding_process": "GTAW",
    }
    defaults.update(values)
    return WPS(**defaults)


def test_all_sequence_step_types_have_stable_task_conversion():
    assert {
        key: sequence_step_to_task_kind(key)
        for key in ("assembly", "weld", "nde", "pwht", "inspection", "closure")
    } == {
        "assembly": "assembly",
        "weld": "welding",
        "nde": "quality_nde",
        "pwht": "process_pwht",
        "inspection": "quality_inspection",
        "closure": "quality_closure",
    }


def test_release_idempotency_hash_is_canonical():
    left = canonical_hash({"sequence_id": "s1", "frozen_hash": "abc"})
    right = canonical_hash({"frozen_hash": "abc", "sequence_id": "s1"})
    assert left == right
    assert len(left) == 64


def test_welder_qualification_accepts_matching_valid_scope():
    cert = WelderCertification(
        id=3,
        welder_id=7,
        is_active=True,
        status="valid",
        expiry_date=date.today() + timedelta(days=30),
        qualified_process="GTAW",
        qualified_position="2G",
    )
    result = evaluate_welder_qualification(_welder(), [cert], _wps(), "2G")
    assert result["qualified"] is True
    assert result["certification_ids"] == [3]


def test_welder_qualification_blocks_expired_or_out_of_scope():
    cert = WelderCertification(
        id=4,
        welder_id=7,
        is_active=True,
        status="valid",
        expiry_date=date.today() - timedelta(days=1),
        qualified_process="SMAW",
        qualified_position="1G",
    )
    result = evaluate_welder_qualification(
        _welder(qualified_processes="[]", qualified_positions="[]"),
        [cert],
        _wps(),
        "6G",
    )
    assert result["qualified"] is False
    assert any("焊接方法资格" in reason for reason in result["reasons"])
    assert any("焊位资格" in reason for reason in result["reasons"])


def test_production_task_keeps_immutable_design_provenance_columns():
    columns = ProductionTask.__table__.columns
    assert {
        "source_product_revision_id",
        "source_sequence_revision_id",
        "source_sequence_step_id",
        "source_weld_joint_id",
        "source_match_freeze_id",
        "production_release_id",
        "consumable_issue_list_id",
        "source_sequence_frozen_hash",
        "source_step_snapshot",
    } <= set(columns.keys())
    assert any(
        item.name == "uq_production_task_sequence_step"
        for item in ProductionTask.__table__.constraints
    )


def test_quality_and_execution_layers_are_separate_from_design_tables():
    assert ProductionQualityNode.__table__.c.sequence_step_id.foreign_keys
    assert ProductionExecutionTrace.__table__.c.design_snapshot_hash.nullable is False
    assert "actual_parameters" in ProductionExecutionTrace.__table__.c
    assert "repair_snapshot" in ProductionExecutionTrace.__table__.c
    assert "quality_snapshot" in ProductionExecutionTrace.__table__.c
    assert "consumable_usage_event_ids" in ProductionExecutionTrace.__table__.c


def test_release_and_execution_have_database_idempotency_guards():
    for model in (ProductionReleaseBatch, ProductionExecutionTrace):
        assert any(
            getattr(constraint, "columns", None) is not None
            and "idempotency_key" in constraint.columns.keys()
            for constraint in model.__table__.constraints
        )


def test_resource_override_and_released_sequence_change_are_auditable():
    assert {
        "qualification_snapshot",
        "override_reason",
        "authorized_by",
        "authorized_at",
    } <= set(ProductionResourceAuthorization.__table__.c.keys())
    assert {
        "source_sequence_revision_id",
        "proposed_sequence_revision_id",
        "approval_instance_id",
        "impact_snapshot",
    } <= set(ProductionSequenceChangeRequest.__table__.c.keys())


def test_released_sequence_recalculation_requires_exact_approved_change():
    approved = ProductionSequenceChangeRequest(
        production_release_id="release-1", status="approved"
    )
    pending = ProductionSequenceChangeRequest(
        production_release_id="release-1", status="pending"
    )
    wrong_release = ProductionSequenceChangeRequest(
        production_release_id="release-2", status="approved"
    )
    assert change_request_allows_recalculation("release-1", approved) is True
    assert change_request_allows_recalculation("release-1", pending) is False
    assert change_request_allows_recalculation("release-1", wrong_release) is False
    assert change_request_allows_recalculation("release-1", None) is False

from copy import deepcopy
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.consumable_calculation import (
    AreaSource,
    ConsumableCalculationError,
    ConsumableOperationInput,
    ConsumableOperationPlan,
    GrooveGeometryInput,
    GrooveType,
    OperationRole,
    calculate_consumable_operation,
    calculate_groove_area,
    calculate_operation_plan,
    summarize_operations,
)
from app.models.consumable import (
    ConsumableGroovePreset,
    ConsumableLegacyMigrationAudit,
    ConsumableMethodParameter,
    ConsumableQuotaOperation,
    ConsumableQuotaOverrideAudit,
    ConsumableQuotaRun,
    ConsumableQuotaSummary,
    ConsumableRuleSet,
    WeldConsumableOperation,
)
from app.models.material import WeldingMaterial
from app.services.consumable_calculation_service import ConsumableCalculationService
from app.services.consumable_quota_service import (
    SYSTEM_TYPICAL_GROOVE_PRESETS,
    apply_manual_override,
    assert_parameter_deletable,
    canonical_hash,
    ensure_rerun_allowed,
    freeze_quota_input,
    legacy_single_operation_payload,
    make_idempotency_key,
    quota_result_diff,
    require_approved_effective_parameter,
    stale_reasons_for_changes,
    validate_material_compatibility,
    validate_frozen_snapshot_for_formal_run,
)


def _geometry():
    return calculate_groove_area(
        GrooveGeometryInput(
            groove_type=GrooveType.V_BUTT,
            thickness_mm=16,
            included_angle_deg=60,
            root_gap_mm=2,
            root_face_mm=2,
            reinforcement_mm=2,
            back_gouge_depth_mm=3,
            back_gouge_opening_width_mm=5,
        )
    )


def _operation(method: str, **values):
    base = {
        "area_mm2": 1,
        "length_mm": 1000,
        "density_g_cm3": 7.85,
        "deposition_efficiency": 0.9,
        "deposition_rate_kg_h": 1.5,
        "arc_time_ratio": 0.5,
        "welding_method": method,
    }
    base.update(values)
    return ConsumableOperationInput(**base)


def test_operation_roles_bind_split_geometry_or_independent_area_strictly():
    geometry = _geometry()
    face = calculate_operation_plan(
        ConsumableOperationPlan(
            role=OperationRole.FACE_FILL,
            area_source=AreaSource.FRONT_FILL,
            area_allocation_ratio=0.25,
            operation=_operation("GTAW"),
        ),
        geometry,
    )
    back = calculate_operation_plan(
        ConsumableOperationPlan(
            role=OperationRole.BACK_GOUGE_FILL,
            area_source=AreaSource.BACK_GOUGE,
            operation=_operation("SMAW"),
        ),
        geometry,
    )
    tack = calculate_operation_plan(
        ConsumableOperationPlan(
            role=OperationRole.TACK,
            area_source=AreaSource.INDEPENDENT,
            operation=_operation("GMAW", area_mm2=12),
        )
    )
    assert face.input_snapshot["area_mm2"] == pytest.approx(
        geometry.front_fill_adjusted_mm2 * 0.25
    )
    assert back.input_snapshot["area_mm2"] == pytest.approx(
        geometry.back_gouge_adjusted_mm2
    )
    assert tack.input_snapshot["area_mm2"] == 12
    with pytest.raises(ConsumableCalculationError, match="不能绑定"):
        calculate_operation_plan(
            ConsumableOperationPlan(
                role=OperationRole.TACK,
                area_source=AreaSource.FRONT_FILL,
                operation=_operation("GMAW"),
            ),
            geometry,
        )


def test_gtaw_saw_combination_uses_distinct_parameters_and_aggregates_every_item():
    geometry = _geometry()
    gtaw = calculate_operation_plan(
        ConsumableOperationPlan(
            role=OperationRole.FACE_FILL,
            area_source=AreaSource.FRONT_FILL,
            area_allocation_ratio=0.2,
            operation=_operation(
                "GTAW",
                deposition_efficiency=0.98,
                deposition_rate_kg_h=0.8,
                gas_flow_l_min=12,
            ),
        ),
        geometry,
    )
    saw = calculate_operation_plan(
        ConsumableOperationPlan(
            role=OperationRole.FACE_FILL,
            area_source=AreaSource.FRONT_FILL,
            area_allocation_ratio=0.8,
            operation=_operation(
                "SAW",
                deposition_efficiency=0.96,
                deposition_rate_kg_h=5,
                flux_wire_ratio=1.1,
            ),
        ),
        geometry,
    )
    summary = summarize_operations([gtaw, saw])
    assert summary.operation_count == 2
    assert summary.deposit_mass_kg == pytest.approx(
        gtaw.deposit_mass_kg + saw.deposit_mass_kg
    )
    assert summary.primary_consumable_kg == pytest.approx(
        gtaw.primary_consumable_kg + saw.primary_consumable_kg
    )
    assert summary.flux_kg == pytest.approx(saw.flux_kg)
    assert summary.gas_volume_l == pytest.approx(gtaw.gas_volume_l)
    assert summary.total_operation_time_h == pytest.approx(
        gtaw.total_operation_time_h + saw.total_operation_time_h
    )


def test_smaw_gmaw_combination_separates_solid_consumable_and_shielding_gas():
    smaw = calculate_operation_plan(
        ConsumableOperationPlan(
            role=OperationRole.CUSTOM,
            area_source=AreaSource.INDEPENDENT,
            operation=_operation("SMAW", area_mm2=30, deposition_efficiency=0.65),
        )
    )
    gmaw = calculate_operation_plan(
        ConsumableOperationPlan(
            role=OperationRole.CUSTOM,
            area_source=AreaSource.INDEPENDENT,
            operation=_operation(
                "GMAW",
                area_mm2=70,
                deposition_efficiency=0.95,
                gas_flow_l_min=18,
            ),
        )
    )
    summary = summarize_operations([smaw, gmaw])
    assert summary.primary_consumable_kg == pytest.approx(
        smaw.primary_consumable_kg + gmaw.primary_consumable_kg
    )
    assert smaw.gas_volume_l is None
    assert summary.gas_volume_l == pytest.approx(gmaw.gas_volume_l)


def test_process_enterprise_and_package_layers_are_separate_and_traceable():
    result = calculate_consumable_operation(
        _operation(
            "SMAW",
            electrode_stub_loss_ratio=0.08,
            spatter_loss_ratio=0.02,
            enterprise_correction_factor=1.05,
            package_size_kg=5,
        )
    )
    assert result.process_primary_consumable_kg == pytest.approx(
        result.primary_consumable_kg * 1.1
    )
    assert result.enterprise_primary_consumable_kg == pytest.approx(
        result.process_primary_consumable_kg * 1.05
    )
    assert result.package_rounded_primary_kg % 5 == 0
    assert result.suggested_primary_issue_kg == result.package_rounded_primary_kg
    assert result.result_sources["deposit_mass_kg"] == "system_calculated"


def _record(order, method, ratio, **extra):
    values = dict(
        id=f"op-{order}",
        operation_order=order,
        operation_role="face_fill",
        area_source="front_fill",
        area_allocation_ratio=ratio,
        status="draft",
        area_mm2=1,
        length_mm=1000,
        density_g_cm3=7.85,
        deposition_efficiency=0.9,
        deposition_rate_kg_h=2,
        arc_time_h=None,
        arc_time_ratio=0.5,
        flux_wire_ratio=None,
        gas_flow_l_min=None,
        electrode_stub_loss_ratio=0,
        spatter_loss_ratio=0,
        flux_loss_ratio=0,
        enterprise_correction_factor=1,
        package_size_kg=None,
        pass_count_description=None,
        welding_method=method,
    )
    values.update(extra)
    return WeldConsumableOperation(**values)


def test_persisted_multi_operation_never_silently_falls_back_and_allocations_close():
    geometry = _geometry()
    rows, summary = ConsumableCalculationService.calculate_operations(
        [_record(2, "SAW", 0.8), _record(1, "GTAW", 0.2)],
        geometry.__dict__,
    )
    assert len(rows) == 2
    assert summary["operation_count"] == 2
    with pytest.raises(ConsumableCalculationError, match="静默回退"):
        ConsumableCalculationService.calculate_operations([], geometry.__dict__)
    with pytest.raises(ConsumableCalculationError, match="合计必须等于1"):
        ConsumableCalculationService.calculate_operations(
            [_record(1, "GTAW", 0.4)], geometry.__dict__
        )
    with pytest.raises(ConsumableCalculationError, match="损坏或不完整"):
        ConsumableCalculationService.calculate_operations(
            [_record(1, "GTAW", 1, density_g_cm3=None)], geometry.__dict__
        )


def test_method_material_compatibility_and_parameter_effectivity_are_explicit():
    validate_material_compatibility("SMAW", "electrode", ["electrode"])
    with pytest.raises(ConsumableCalculationError, match="不适用于"):
        validate_material_compatibility("SMAW", "gas", ["electrode"])
    now = datetime(2026, 8, 23)
    approved = SimpleNamespace(
        approval_status="approved",
        is_active=True,
        effective_from=now - timedelta(days=1),
        effective_to=now + timedelta(days=1),
    )
    require_approved_effective_parameter(approved, now)
    approved.approval_status = "draft"
    with pytest.raises(ConsumableCalculationError, match="已批准"):
        require_approved_effective_parameter(approved, now)
    with pytest.raises(ConsumableCalculationError, match="只能停用"):
        assert_parameter_deletable(1)


def test_material_and_enterprise_parameter_models_are_versioned_and_scoped():
    material_columns = set(WeldingMaterial.__table__.columns.keys())
    assert {
        "density_g_cm3",
        "default_deposition_efficiency",
        "default_deposition_rate_kg_h",
        "consumable_type",
        "applicable_welding_methods",
        "parameter_version",
        "parameter_approval_status",
        "parameter_effective_from",
    } <= material_columns
    assert ConsumableMethodParameter.__tablename__ == "consumable_method_parameters"
    assert ConsumableGroovePreset.__tablename__ == "consumable_groove_presets"
    assert {
        "company_id",
        "factory_id",
        "version_number",
        "approval_status",
        "effective_from",
        "effective_to",
        "supersedes_id",
    } <= set(ConsumableMethodParameter.__table__.columns.keys())
    assert {item["groove_type"] for item in SYSTEM_TYPICAL_GROOVE_PRESETS} == {
        "I",
        "V",
        "X",
        "U",
        "FILLET",
        "LAP",
    }


def test_quota_models_freeze_every_layer_and_keep_override_audit():
    assert ConsumableRuleSet.__tablename__ == "consumable_rule_sets"
    assert ConsumableQuotaRun.__tablename__ == "consumable_quota_runs"
    assert ConsumableQuotaOperation.__tablename__ == "consumable_quota_operations"
    assert ConsumableQuotaSummary.__tablename__ == "consumable_quota_summaries"
    assert (
        ConsumableQuotaOverrideAudit.__tablename__ == "consumable_quota_override_audits"
    )
    assert (
        ConsumableLegacyMigrationAudit.__tablename__
        == "consumable_legacy_migration_audits"
    )
    assert {
        "frozen_input_snapshot",
        "result_snapshot",
        "diff_snapshot",
        "input_version_hash",
        "idempotency_key",
        "stale_reasons",
        "parent_run_id",
    } <= set(ConsumableQuotaRun.__table__.columns.keys())
    assert {
        "theoretical_deposit_kg",
        "process_primary_kg",
        "enterprise_primary_kg",
        "package_rounded_primary_kg",
        "suggested_primary_issue_kg",
        "method_snapshot",
        "material_snapshot",
        "result_sources",
    } <= set(ConsumableQuotaOperation.__table__.columns.keys())


def test_frozen_input_does_not_drift_and_same_versions_are_idempotent():
    operations = [{"method": "GTAW", "efficiency": 0.98}]
    snapshot, input_hash = freeze_quota_input(
        formula_version="P6-CONSUMABLE-1.0.0",
        geometry={"area": 100},
        length={"length": 1000},
        operations=operations,
        methods=[{"version": 2}],
        materials=[{"id": 7, "version": 3}],
        enterprise_rule={"version": 4, "correction": 1.05},
    )
    before = deepcopy(snapshot)
    operations[0]["efficiency"] = 0.5
    assert snapshot == before
    assert canonical_hash(snapshot) == input_hash
    key1 = make_idempotency_key("product", "sequence", input_hash, "rule-hash")
    key2 = make_idempotency_key("product", "sequence", input_hash, "rule-hash")
    assert key1 == key2
    assert make_idempotency_key("product", "sequence", input_hash, "new-rule") != key1


def test_formal_run_rejects_unapproved_parameters_and_unconfirmed_approximation():
    base = {
        "methods": [{"approval_status": "approved"}],
        "materials": [{"parameter_approval_status": "approved"}],
        "enterprise_rule": {"status": "approved"},
        "geometry": {"input_snapshot": {"gouge_strategy": "explicit"}},
    }
    validate_frozen_snapshot_for_formal_run(base)
    unapproved = deepcopy(base)
    unapproved["methods"][0]["approval_status"] = "draft"
    with pytest.raises(ConsumableCalculationError, match="已批准版本"):
        validate_frozen_snapshot_for_formal_run(unapproved)
    approximation = deepcopy(base)
    approximation["geometry"]["input_snapshot"] = {
        "gouge_strategy": "reference_trapezoid",
        "engineer_confirmed": False,
    }
    with pytest.raises(ConsumableCalculationError, match="未经工程校核"):
        validate_frozen_snapshot_for_formal_run(approximation)
    default_coefficients = deepcopy(base)
    default_coefficients["enterprise_rule"].update(
        uses_reference_defaults=True, engineer_validated=False
    )
    with pytest.raises(ConsumableCalculationError, match="默认系数"):
        validate_frozen_snapshot_for_formal_run(default_coefficients)


def test_manual_override_requires_reason_and_creates_pending_review_source():
    result = {
        "suggested_primary_issue_kg": 12.0,
        "result_sources": {"suggested_primary_issue_kg": "system_calculated"},
    }
    overridden, audit = apply_manual_override(
        result, "suggested_primary_issue_kg", 15, "现场包装规格调整"
    )
    assert result["suggested_primary_issue_kg"] == 12
    assert overridden["suggested_primary_issue_kg"] == 15
    assert (
        overridden["result_sources"]["suggested_primary_issue_kg"] == "manual_override"
    )
    assert audit["review_status"] == "pending"
    with pytest.raises(ConsumableCalculationError, match="必须填写原因"):
        apply_manual_override(result, "suggested_primary_issue_kg", 15, " ")


def test_explicit_rerun_diff_and_input_change_staleness_do_not_overwrite_old_result():
    previous = {"suggested_primary_issue_kg": 10, "flux_kg": 2}
    current = {"suggested_primary_issue_kg": 12, "flux_kg": 2}
    before = deepcopy(previous)
    diff = quota_result_diff(previous, current)
    assert previous == before
    assert diff == {"suggested_primary_issue_kg": {"previous": 10, "current": 12}}
    assert stale_reasons_for_changes(
        ["length", "material", "unrelated", "enterprise_coefficient"]
    ) == ["enterprise_coefficient", "length", "material"]
    ensure_rerun_allowed("approved")
    ensure_rerun_allowed("issued")
    with pytest.raises(ConsumableCalculationError, match="不允许重算"):
        ensure_rerun_allowed("superseded")


def test_legacy_single_operation_migration_is_explicit_and_audited():
    source = {
        "source_type": "legacy_quote_task",
        "source_id": "old-1",
        "welding_method": "SMAW",
        "area_mm2": 50,
        "length_mm": 1000,
        "density_g_cm3": 7.85,
        "deposition_efficiency": 0.65,
    }
    operation, audit = legacy_single_operation_payload(source)
    assert operation["operation_role"] == "custom"
    assert operation["area_source"] == "independent"
    assert audit["source_snapshot"] == source
    assert audit["warnings"]
    with pytest.raises(ConsumableCalculationError, match="缺少显式字段"):
        legacy_single_operation_payload({"source_type": "old", "source_id": "1"})

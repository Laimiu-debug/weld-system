import math
import ast
from datetime import datetime
from pathlib import Path

import pytest

from app.consumable_calculation import (
    ConsumableCalculationError,
    ConsumableOperationInput,
    DiameterBasis,
    GougeStrategy,
    GrooveGeometryInput,
    GrooveType,
    LengthType,
    WeldLengthInput,
    calculate_consumable_operation,
    calculate_groove_area,
    calculate_weld_length,
    geometry_warnings,
)
from app.models.consumable import ConsumableGeometryInput, WeldConsumableOperation
from app.services.consumable_calculation_service import ConsumableCalculationService


def test_pure_package_has_no_framework_file_or_network_dependencies():
    package = Path(__file__).parents[2] / "app" / "consumable_calculation"
    forbidden = {
        "fastapi",
        "sqlalchemy",
        "requests",
        "httpx",
        "socket",
        "pathlib",
        "os",
        "io",
        "datetime",
        "time",
    }
    imported = set()
    for source_file in package.glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(forbidden)


def test_i_butt_area_and_explicit_gouge_split():
    result = calculate_groove_area(
        GrooveGeometryInput(
            groove_type=GrooveType.I_BUTT,
            thickness_mm=6,
            root_gap_mm=2,
            reinforcement_mm=1,
            back_gouge_depth_mm=2,
            back_gouge_opening_width_mm=4,
        )
    )
    assert result.front_fill_geometry_mm2 == 13
    assert result.back_gouge_geometry_mm2 == 6
    assert result.back_reinforcement_geometry_mm2 == 2
    assert result.total_area_mm2 == 21
    assert (
        result.front_fill_adjusted_mm2
        + result.back_gouge_adjusted_mm2
        + result.back_reinforcement_adjusted_mm2
        == result.total_area_mm2
    )


def test_v_butt_hand_calculation_with_face_width_and_small_fill_factor():
    value = GrooveGeometryInput(
        groove_type=GrooveType.V_BUTT,
        thickness_mm=12,
        included_angle_deg=60,
        root_gap_mm=2,
        root_face_mm=2,
        reinforcement_mm=2,
        face_extra_each_side_mm=1,
        fill_factor=1.05,
    )
    result = calculate_groove_area(value)
    height = 10
    tan_half = math.tan(math.radians(30))
    width = 2 + 2 * height * tan_half + 2
    expected = 12 * 2 + height * height * tan_half + 0.5 * width * 2
    assert result.front_fill_geometry_mm2 == pytest.approx(expected)
    assert result.total_area_mm2 == pytest.approx(expected * 1.05)


def test_x_butt_has_two_bevels_and_back_reinforcement_without_gouge_double_count():
    result = calculate_groove_area(
        GrooveGeometryInput(
            groove_type=GrooveType.X_BUTT,
            thickness_mm=12,
            included_angle_deg=60,
            root_gap_mm=2,
            root_face_mm=2,
            upper_bevel_height_mm=5,
            lower_bevel_height_mm=5,
            reinforcement_mm=2,
        )
    )
    tan_half = math.tan(math.radians(30))
    face = 2 + 2 * 5 * tan_half
    expected = 12 * 2 + 2 * 25 * tan_half + 2 * (0.5 * face * 2)
    assert result.geometry_total_mm2 == pytest.approx(expected)
    assert result.back_gouge_geometry_mm2 == 0
    assert result.back_reinforcement_geometry_mm2 == pytest.approx(0.5 * face * 2)


def test_u_butt_semicircle_reference_geometry():
    result = calculate_groove_area(
        GrooveGeometryInput(
            groove_type=GrooveType.U_BUTT,
            thickness_mm=16,
            included_angle_deg=20,
            root_gap_mm=2,
            root_face_mm=2,
            radius_mm=5,
            reinforcement_mm=2,
        )
    )
    straight = 9
    tan_half = math.tan(math.radians(10))
    width = 2 + 2 * 5 + 2 * straight * tan_half
    expected = (
        16 * 2
        + 2 * 5 * straight
        + straight**2 * tan_half
        + 0.5 * math.pi * 25
        + 0.5 * width * 2
    )
    assert result.total_area_mm2 == pytest.approx(expected)


@pytest.mark.parametrize("groove_type", [GrooveType.FILLET, GrooveType.LAP])
def test_fillet_and_lap_support_leg_reinforcement_and_extra(groove_type):
    result = calculate_groove_area(
        GrooveGeometryInput(
            groove_type=groove_type,
            leg_size_mm=8,
            reinforcement_mm=1,
            face_extra_each_side_mm=1,
        )
    )
    width = math.sqrt(2) * 8 + 2
    assert result.total_area_mm2 == pytest.approx(0.5 * 64 + 0.5 * width)


def test_reference_gouge_is_opt_in_and_warns_for_engineer_confirmation():
    value = GrooveGeometryInput(
        groove_type=GrooveType.V_BUTT,
        thickness_mm=20,
        included_angle_deg=60,
        root_gap_mm=2,
        root_face_mm=2,
        back_gouge_depth_mm=3,
        gouge_strategy=GougeStrategy.REFERENCE_TRAPEZOID,
    )
    result = calculate_groove_area(value)
    assert result.back_gouge_geometry_mm2 == pytest.approx(3 * (2 + 5) / 2)
    assert any("参考" in warning for warning in result.warnings)


def test_explicit_gouge_requires_width_and_fill_factor_does_not_hide_losses():
    with pytest.raises(ConsumableCalculationError, match="清根槽开口宽度"):
        calculate_groove_area(
            GrooveGeometryInput(
                groove_type=GrooveType.I_BUTT,
                thickness_mm=8,
                root_gap_mm=2,
                back_gouge_depth_mm=2,
            )
        )
    warning = geometry_warnings(
        GrooveGeometryInput(
            groove_type=GrooveType.I_BUTT,
            thickness_mm=8,
            root_gap_mm=2,
            fill_factor=1.3,
        )
    )
    assert any("独立参数" in item for item in warning)


@pytest.mark.parametrize(
    "value,message",
    [
        (GrooveGeometryInput(groove_type=GrooveType.V_BUTT), "板厚"),
        (GrooveGeometryInput(groove_type=GrooveType.FILLET), "焊脚"),
        (
            GrooveGeometryInput(
                groove_type=GrooveType.I_BUTT,
                thickness_mm=8,
                root_gap_mm=2,
                fill_factor=0,
            ),
            "填充系数",
        ),
        (
            GrooveGeometryInput(
                groove_type=GrooveType.I_BUTT,
                thickness_mm=8,
                root_gap_mm=-1,
            ),
            "间隙",
        ),
    ],
)
def test_invalid_geometry_is_explicit(value, message):
    with pytest.raises(ConsumableCalculationError, match=message):
        calculate_groove_area(value)


def test_drawing_geometry_requires_engineer_confirmation():
    with pytest.raises(ConsumableCalculationError, match="工程师确认"):
        calculate_groove_area(
            GrooveGeometryInput(
                groove_type=GrooveType.I_BUTT,
                thickness_mm=8,
                root_gap_mm=2,
                source="drawing",
            )
        )


def test_straight_complete_and_partial_circumferential_lengths():
    straight = calculate_weld_length(
        WeldLengthInput(
            length_type=LengthType.STRAIGHT,
            straight_length_mm=1200,
            count=2,
        )
    )
    assert straight.total_length_mm == 2400
    full = calculate_weld_length(
        WeldLengthInput(
            length_type=LengthType.CIRCUMFERENTIAL,
            diameter_mm=1000,
            diameter_basis=DiameterBasis.MEAN,
        )
    )
    partial = calculate_weld_length(
        WeldLengthInput(
            length_type=LengthType.CIRCUMFERENTIAL,
            diameter_mm=1000,
            diameter_basis=DiameterBasis.INNER,
            included_angle_deg=45,
            count=4,
        )
    )
    assert full.total_length_mm == pytest.approx(math.pi * 1000)
    assert full.diameter_basis == "mean"
    assert partial.total_length_mm == pytest.approx(math.pi * 1000 * 45 / 360 * 4)
    assert partial.diameter_basis == "inner"


def test_manual_length_and_drawing_length_require_confirmation():
    with pytest.raises(ConsumableCalculationError, match="工程师确认"):
        calculate_weld_length(
            WeldLengthInput(
                length_type=LengthType.MANUAL_CONFIRMED,
                manual_confirmed_length_mm=500,
            )
        )
    confirmed = calculate_weld_length(
        WeldLengthInput(
            length_type=LengthType.MANUAL_CONFIRMED,
            manual_confirmed_length_mm=500,
            count=3,
            engineer_confirmed=True,
        )
    )
    assert confirmed.total_length_mm == 1500
    with pytest.raises(ConsumableCalculationError, match="图纸解析长度"):
        calculate_weld_length(
            WeldLengthInput(
                length_type=LengthType.STRAIGHT,
                straight_length_mm=500,
                source="drawing",
            )
        )


def test_circumference_requires_explicit_basis_and_valid_angle_count():
    with pytest.raises(ConsumableCalculationError, match="内径、中径或外径"):
        calculate_weld_length(
            WeldLengthInput(
                length_type=LengthType.CIRCUMFERENTIAL,
                diameter_mm=500,
            )
        )
    with pytest.raises(ConsumableCalculationError, match="包角"):
        calculate_weld_length(
            WeldLengthInput(
                length_type=LengthType.CIRCUMFERENTIAL,
                diameter_mm=500,
                diameter_basis=DiameterBasis.OUTER,
                included_angle_deg=361,
            )
        )
    with pytest.raises(ConsumableCalculationError, match="正整数"):
        calculate_weld_length(
            WeldLengthInput(
                length_type=LengthType.STRAIGHT,
                straight_length_mm=500,
                count=0,
            )
        )


def test_quantity_core_returns_all_intermediates_for_wire_flux_and_gas():
    result = calculate_consumable_operation(
        ConsumableOperationInput(
            area_mm2=100,
            length_mm=1000,
            density_g_cm3=7.85,
            deposition_efficiency=0.95,
            deposition_rate_kg_h=2,
            arc_time_ratio=0.4,
            welding_method="SAW",
            flux_wire_ratio=1.2,
            gas_flow_l_min=15,
            pass_count_description=8,
        )
    )
    assert result.volume_mm3 == 100_000
    assert result.deposit_mass_kg == pytest.approx(0.785)
    assert result.primary_consumable_kg == pytest.approx(0.785 / 0.95)
    assert result.flux_kg == pytest.approx((0.785 / 0.95) * 1.2)
    assert result.arc_time_h == pytest.approx(0.785 / 2)
    assert result.total_operation_time_h == pytest.approx((0.785 / 2) / 0.4)
    assert result.gas_volume_l == pytest.approx(15 * (0.785 / 2) * 60)
    assert result.pass_count_description == 8
    assert result.pass_count_mass_multiplier == 1.0


def test_pass_count_is_description_only_and_deterministic():
    base = dict(
        area_mm2=50,
        length_mm=2000,
        density_g_cm3=7.85,
        deposition_efficiency=0.9,
        welding_method="SMAW",
    )
    one = calculate_consumable_operation(
        ConsumableOperationInput(**base, pass_count_description=1)
    )
    twelve = calculate_consumable_operation(
        ConsumableOperationInput(**base, pass_count_description=12)
    )
    repeat = calculate_consumable_operation(
        ConsumableOperationInput(**base, pass_count_description=12)
    )
    assert one.deposit_mass_kg == twelve.deposit_mass_kg
    assert one.primary_consumable_kg == twelve.primary_consumable_kg
    assert twelve == repeat


@pytest.mark.parametrize(
    "overrides,message",
    [
        ({"area_mm2": 0}, "截面积"),
        ({"length_mm": -1}, "焊缝长度"),
        ({"density_g_cm3": 0}, "密度"),
        ({"deposition_efficiency": None}, "熔敷效率"),
        ({"deposition_efficiency": 0}, "熔敷效率"),
        ({"deposition_efficiency": 1.01}, "不能大于1"),
        ({"area_unit": "cm2"}, "非法单位"),
        ({"gas_flow_l_min": 15}, "电弧时间"),
        ({"flux_wire_ratio": 0}, "配比"),
    ],
)
def test_quantity_core_rejects_zero_negative_missing_and_illegal_units(
    overrides, message
):
    values = {
        "area_mm2": 100,
        "length_mm": 1000,
        "density_g_cm3": 7.85,
        "deposition_efficiency": 0.9,
        "welding_method": "SMAW",
    }
    values.update(overrides)
    with pytest.raises(ConsumableCalculationError, match=message):
        calculate_consumable_operation(ConsumableOperationInput(**values))


def test_explicit_and_derived_arc_time_must_agree():
    with pytest.raises(ConsumableCalculationError, match="不一致"):
        calculate_consumable_operation(
            ConsumableOperationInput(
                area_mm2=100,
                length_mm=1000,
                density_g_cm3=7.85,
                deposition_efficiency=0.9,
                deposition_rate_kg_h=2,
                arc_time_h=1,
                welding_method="GMAW",
            )
        )


def test_relational_models_trace_product_joint_sequence_step_and_keep_prices_out():
    geometry_columns = set(ConsumableGeometryInput.__table__.columns.keys())
    operation_columns = set(WeldConsumableOperation.__table__.columns.keys())
    assert {
        "product_revision_id",
        "weld_joint_id",
        "sequence_revision_id",
        "sequence_step_id",
        "geometry_input_snapshot",
        "length_input_snapshot",
    } <= geometry_columns
    assert {
        "geometry_input_id",
        "product_revision_id",
        "weld_joint_id",
        "sequence_revision_id",
        "sequence_step_id",
        "operation_order",
        "welding_method",
        "material_id",
        "input_snapshot",
        "result_snapshot",
    } <= operation_columns
    assert all(
        not any(
            token in name.casefold() for token in ("price", "cost", "profit", "tax")
        )
        for name in geometry_columns | operation_columns
    )


def test_service_only_maps_relational_records_to_pure_inputs():
    geometry = ConsumableGeometryInput(
        status="confirmed",
        confirmed_at=datetime(2026, 1, 1),
        source="drawing",
        groove_type="V",
        thickness_mm=12,
        included_angle_deg=60,
        root_gap_mm=2,
        root_face_mm=2,
        radius_mm=0,
        upper_bevel_height_mm=0,
        lower_bevel_height_mm=0,
        leg_size_mm=0,
        reinforcement_mm=2,
        face_extra_each_side_mm=1,
        fill_factor=1.05,
        back_gouge_depth_mm=0,
        back_gouge_opening_width_mm=None,
        gouge_strategy="explicit",
        reference_gouge_flare_ratio=0.5,
        length_type="circumferential",
        weld_count=1,
        straight_length_mm=None,
        diameter_mm=1000,
        diameter_basis="mean",
        included_length_angle_deg=180,
        manual_confirmed_length_mm=None,
    )
    geometry_result, length_result = ConsumableCalculationService.calculate_geometry(
        geometry
    )
    assert geometry_result["total_area_mm2"] > 0
    assert length_result["total_length_mm"] == pytest.approx(math.pi * 1000 / 2)

    operation = WeldConsumableOperation(
        area_mm2=geometry_result["total_area_mm2"],
        length_mm=length_result["total_length_mm"],
        density_g_cm3=7.85,
        deposition_efficiency=0.95,
        welding_method="SAW",
        pass_count_description=6,
        deposition_rate_kg_h=4,
        arc_time_h=None,
        arc_time_ratio=0.5,
        flux_wire_ratio=1.2,
        gas_flow_l_min=None,
    )
    result = ConsumableCalculationService.calculate_operation(operation)
    assert result["deposit_mass_kg"] > 0
    assert result["flux_kg"] > 0
    assert result["pass_count_mass_multiplier"] == 1.0

"""Pure material-quantity calculation, deliberately excluding all prices."""
from __future__ import annotations

import math
from dataclasses import asdict

from .errors import ConsumableCalculationError
from .models import ConsumableOperationInput, ConsumableOperationResult


EXPECTED_UNITS = {
    "area_unit": "mm2",
    "length_unit": "mm",
    "density_unit": "g/cm3",
    "mass_unit": "kg",
    "time_unit": "h",
}


def _positive(value: float | None, label: str, required: bool = True) -> None:
    if value is None and not required:
        return
    if value is None or not math.isfinite(value) or value <= 0:
        raise ConsumableCalculationError(f"{label}必须大于0")


def calculate_consumable_operation(
    value: ConsumableOperationInput,
) -> ConsumableOperationResult:
    for field_name, expected in EXPECTED_UNITS.items():
        actual = getattr(value, field_name)
        if actual != expected:
            raise ConsumableCalculationError(f"非法单位：{field_name}={actual}，要求{expected}")
    _positive(value.area_mm2, "截面积")
    _positive(value.length_mm, "焊缝长度")
    _positive(value.density_g_cm3, "密度")
    _positive(value.deposition_efficiency, "熔敷效率")
    if value.deposition_efficiency > 1:
        raise ConsumableCalculationError("熔敷效率不能大于1")
    if not value.welding_method.strip():
        raise ConsumableCalculationError("焊接方法不能为空")
    if value.pass_count_description is not None:
        if (
            not isinstance(value.pass_count_description, int)
            or isinstance(value.pass_count_description, bool)
            or value.pass_count_description <= 0
        ):
            raise ConsumableCalculationError("焊道数描述必须是正整数")
    _positive(value.deposition_rate_kg_h, "熔敷速度", required=False)
    _positive(value.arc_time_h, "电弧时间", required=False)
    _positive(value.arc_time_ratio, "燃弧系数", required=False)
    if value.arc_time_ratio is not None and value.arc_time_ratio > 1:
        raise ConsumableCalculationError("燃弧系数不能大于1")
    _positive(value.flux_wire_ratio, "焊剂/焊丝配比", required=False)
    _positive(value.gas_flow_l_min, "气体流量", required=False)

    volume = value.area_mm2 * value.length_mm
    deposit_mass = volume * value.density_g_cm3 / 1_000_000.0
    primary = deposit_mass / value.deposition_efficiency
    flux = (
        primary * value.flux_wire_ratio if value.flux_wire_ratio is not None else None
    )
    derived_arc = (
        deposit_mass / value.deposition_rate_kg_h
        if value.deposition_rate_kg_h is not None
        else None
    )
    if value.arc_time_h is not None and derived_arc is not None:
        if not math.isclose(value.arc_time_h, derived_arc, rel_tol=1e-6, abs_tol=1e-9):
            raise ConsumableCalculationError("显式电弧时间与熔敷速度推导结果不一致")
    arc_time = value.arc_time_h if value.arc_time_h is not None else derived_arc
    total_time = (
        arc_time / value.arc_time_ratio
        if arc_time is not None and value.arc_time_ratio is not None
        else None
    )
    if value.gas_flow_l_min is not None and arc_time is None:
        raise ConsumableCalculationError("计算气体用量必须提供电弧时间或熔敷速度")
    gas = value.gas_flow_l_min * arc_time * 60 if value.gas_flow_l_min else None
    return ConsumableOperationResult(
        volume_mm3=volume,
        density_g_cm3=value.density_g_cm3,
        deposit_mass_kg=deposit_mass,
        deposition_efficiency=value.deposition_efficiency,
        primary_consumable_kg=primary,
        flux_wire_ratio=value.flux_wire_ratio,
        flux_kg=flux,
        deposition_rate_kg_h=value.deposition_rate_kg_h,
        arc_time_h=arc_time,
        arc_time_ratio=value.arc_time_ratio,
        total_operation_time_h=total_time,
        gas_flow_l_min=value.gas_flow_l_min,
        gas_volume_l=gas,
        pass_count_description=value.pass_count_description,
        pass_count_mass_multiplier=1.0,
        input_snapshot=asdict(value),
    )

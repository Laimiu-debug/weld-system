"""Strict multi-operation composition and aggregation."""
from __future__ import annotations

from dataclasses import replace
import math

from .calculation import calculate_consumable_operation
from .errors import ConsumableCalculationError
from .models import (
    AreaSource,
    ConsumableOperationPlan,
    ConsumableOperationResult,
    ConsumableOperationsSummary,
    GrooveAreaResult,
    OperationRole,
)


ROLE_AREA_SOURCES = {
    OperationRole.FACE_FILL: {AreaSource.FRONT_FILL},
    OperationRole.BACK_GOUGE_FILL: {AreaSource.BACK_GOUGE},
    OperationRole.TACK: {AreaSource.INDEPENDENT},
    OperationRole.CUSTOM: {AreaSource.INDEPENDENT},
}


def calculate_operation_plan(
    plan: ConsumableOperationPlan,
    geometry: GrooveAreaResult | None = None,
) -> ConsumableOperationResult:
    if plan.area_source not in ROLE_AREA_SOURCES[plan.role]:
        raise ConsumableCalculationError(
            f"工序角色{plan.role.value}不能绑定面积来源{plan.area_source.value}"
        )
    operation = plan.operation
    if (
        not math.isfinite(plan.area_allocation_ratio)
        or plan.area_allocation_ratio <= 0
        or plan.area_allocation_ratio > 1
    ):
        raise ConsumableCalculationError("坡口面积分配比例必须大于0且不大于1")
    if plan.area_source == AreaSource.INDEPENDENT and plan.area_allocation_ratio != 1:
        raise ConsumableCalculationError("独立录入面积不能再应用坡口面积分配比例")
    if plan.area_source != AreaSource.INDEPENDENT:
        if geometry is None:
            raise ConsumableCalculationError("绑定坡口面积的工序必须提供几何计算结果")
        area = (
            geometry.front_fill_adjusted_mm2
            if plan.area_source == AreaSource.FRONT_FILL
            else geometry.back_gouge_adjusted_mm2
        )
        if area <= 0:
            raise ConsumableCalculationError("绑定的坡口面积必须大于0")
        operation = replace(operation, area_mm2=area * plan.area_allocation_ratio)
    return calculate_consumable_operation(operation)


def summarize_operations(
    results: list[ConsumableOperationResult] | tuple[ConsumableOperationResult, ...],
) -> ConsumableOperationsSummary:
    if not results:
        raise ConsumableCalculationError("多工序定额至少需要一道完整工序")

    def total(name: str) -> float:
        return sum(float(getattr(item, name) or 0) for item in results)

    return ConsumableOperationsSummary(
        operation_count=len(results),
        deposit_mass_kg=total("deposit_mass_kg"),
        primary_consumable_kg=total("primary_consumable_kg"),
        process_primary_consumable_kg=total("process_primary_consumable_kg"),
        enterprise_primary_consumable_kg=total("enterprise_primary_consumable_kg"),
        package_rounded_primary_kg=total("package_rounded_primary_kg"),
        suggested_primary_issue_kg=total("suggested_primary_issue_kg"),
        flux_kg=total("flux_kg"),
        process_flux_kg=total("process_flux_kg"),
        enterprise_flux_kg=total("enterprise_flux_kg"),
        gas_volume_l=total("gas_volume_l"),
        arc_time_h=total("arc_time_h"),
        total_operation_time_h=total("total_operation_time_h"),
    )

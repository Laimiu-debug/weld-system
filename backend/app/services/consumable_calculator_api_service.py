"""Stateless weld consumable calculator + weldmoney-style cost quote."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.consumable_calculation import (
    ConsumableCalculationError,
    ConsumableOperationInput,
    GougeStrategy,
    GrooveGeometryInput,
    GrooveType,
    calculate_consumable_operation,
    calculate_groove_area,
)
from app.schemas.consumable_calculator import (
    CalculatorJointIn,
    CalculatorOperationIn,
    CalculatorQuoteRequest,
    CostParamsIn,
)

_GROOVE_MAP: dict[str, GrooveType] = {
    "I": GrooveType.I_BUTT,
    "V": GrooveType.V_BUTT,
    "X": GrooveType.X_BUTT,
    "U": GrooveType.U_BUTT,
    "FILLET": GrooveType.FILLET,
    "LAP": GrooveType.LAP,
    "BACK_GOUGE": GrooveType.BACK_GOUGE,
    "TP_V": GrooveType.TP_V,
    "TP_X": GrooveType.TP_X,
}


def _groove_input(joint: CalculatorJointIn) -> GrooveGeometryInput:
    groove = _GROOVE_MAP.get(joint.groove.upper(), GrooveType.V_BUTT)
    strategy = GougeStrategy.EXPLICIT
    opening = joint.gouge_opening_width_mm
    if groove not in {
        GrooveType.I_BUTT,
        GrooveType.V_BUTT,
        GrooveType.X_BUTT,
        GrooveType.U_BUTT,
        GrooveType.BACK_GOUGE,
        GrooveType.TP_V,
        GrooveType.TP_X,
    }:
        strategy = GougeStrategy.REFERENCE_TRAPEZOID
        opening = None
    elif opening <= 0:
        strategy = GougeStrategy.REFERENCE_TRAPEZOID
        opening = None
    return GrooveGeometryInput(
        groove_type=groove,
        thickness_mm=joint.thickness_mm,
        included_angle_deg=joint.included_angle_deg,
        root_gap_mm=joint.root_gap_mm,
        root_face_mm=joint.root_face_mm,
        radius_mm=joint.radius_mm,
        upper_bevel_height_mm=joint.upper_bevel_height_mm,
        lower_bevel_height_mm=0.0,
        leg_size_mm=joint.leg_size_mm,
        reinforcement_mm=joint.reinforcement_mm,
        face_extra_each_side_mm=joint.face_extra_each_side_mm,
        fill_factor=joint.fill_factor,
        back_gouge_depth_mm=joint.back_gouge_depth_mm,
        back_gouge_opening_width_mm=opening,
        gouge_strategy=strategy,
        engineer_confirmed=True,
        source="calculator",
    )


def _operation_area(
    role: str, geometry: dict[str, Any], operation: CalculatorOperationIn
) -> float:
    if role == "face":
        return float(geometry["front_fill_adjusted_mm2"])
    if role == "gouge":
        return float(geometry["back_gouge_adjusted_mm2"]) + float(
            geometry["back_reinforcement_adjusted_mm2"]
        )
    return max(operation.custom_area_mm2, 0.0)


def _operation_cost(
    result: dict[str, Any],
    operation: CalculatorOperationIn,
    cost: CostParamsIn,
) -> dict[str, float]:
    suggested_kg = float(result["suggested_primary_issue_kg"])
    flux_kg = float(result["enterprise_flux_kg"] or 0.0)
    arc_time = float(result["arc_time_h"] or 0.0)
    total_time = float(result["total_operation_time_h"] or 0.0)
    gas_l = float(result["gas_volume_l"] or 0.0)

    material_cost = suggested_kg * operation.unit_price
    if flux_kg > 0 and operation.flux_unit_price > 0:
        material_cost += flux_kg * operation.flux_unit_price
    elif flux_kg > 0 and operation.flux_wire_ratio > 0:
        material_cost += flux_kg * operation.unit_price

    aux_cost = gas_l * cost.gas_price_per_l
    labor_cost = total_time * cost.labor_rate_per_hour * (1 + cost.overhead_rate)
    power_cost = cost.machine_power_kw * arc_time * cost.electricity_price
    depreciation = (
        cost.daily_depreciation * (arc_time / cost.daily_work_hours)
        if cost.daily_work_hours > 0
        else 0.0
    )
    equipment_cost = power_cost + depreciation
    subtotal = material_cost + aux_cost + labor_cost + equipment_cost
    return {
        "material_cost": material_cost,
        "aux_cost": aux_cost,
        "labor_cost": labor_cost,
        "equipment_cost": equipment_cost,
        "subtotal_cost": subtotal,
    }


def calculate_joint_quote(joint: CalculatorJointIn, cost: CostParamsIn) -> dict[str, Any]:
    groove = calculate_groove_area(_groove_input(joint))
    geometry_dict = asdict(groove)
    operation_rows: list[dict[str, Any]] = []
    totals = {
        "deposit_kg": 0.0,
        "suggested_primary_kg": 0.0,
        "enterprise_flux_kg": 0.0,
        "gas_volume_l": 0.0,
        "arc_time_h": 0.0,
        "total_time_h": 0.0,
        "material_cost": 0.0,
        "aux_cost": 0.0,
        "labor_cost": 0.0,
        "equipment_cost": 0.0,
    }

    for operation in joint.operations:
        area = _operation_area(operation.role, geometry_dict, operation)
        op_input = ConsumableOperationInput(
            area_mm2=area,
            length_mm=joint.length_mm,
            density_g_cm3=operation.density_g_cm3,
            deposition_efficiency=operation.deposition_efficiency,
            welding_method=operation.method,
            deposition_rate_kg_h=operation.deposition_rate_kg_h,
            arc_time_ratio=operation.arc_time_ratio,
            flux_wire_ratio=operation.flux_wire_ratio or None,
            gas_flow_l_min=operation.gas_flow_l_min,
            electrode_stub_loss_ratio=operation.stub_loss_ratio,
            spatter_loss_ratio=operation.spatter_loss_ratio,
            flux_loss_ratio=operation.flux_loss_ratio,
            enterprise_correction_factor=operation.enterprise_correction_factor,
            package_size_kg=operation.package_size_kg,
        )
        op_result = calculate_consumable_operation(op_input)
        op_dict = asdict(op_result)
        costs = _operation_cost(op_dict, operation, cost)
        row = {
            "operation": operation.model_dump(),
            "area_mm2": area,
            "result": op_dict,
            "costs": costs,
        }
        operation_rows.append(row)
        totals["deposit_kg"] += op_dict["deposit_mass_kg"]
        totals["suggested_primary_kg"] += op_dict["suggested_primary_issue_kg"]
        totals["enterprise_flux_kg"] += float(op_dict["enterprise_flux_kg"] or 0.0)
        totals["gas_volume_l"] += float(op_dict["gas_volume_l"] or 0.0)
        totals["arc_time_h"] += float(op_dict["arc_time_h"] or 0.0)
        totals["total_time_h"] += float(op_dict["total_operation_time_h"] or 0.0)
        for key in ("material_cost", "aux_cost", "labor_cost", "equipment_cost"):
            totals[key] += costs[key]

    direct_cost = (
        totals["material_cost"]
        + totals["aux_cost"]
        + totals["labor_cost"]
        + totals["equipment_cost"]
    )
    with_profit = direct_cost * (1 + cost.profit_margin)
    with_tax = with_profit * (1 + cost.tax_rate)
    return {
        "joint": joint.model_dump(),
        "geometry": geometry_dict,
        "operations": operation_rows,
        "totals": {
            **totals,
            "direct_cost": direct_cost,
            "profit_margin": cost.profit_margin,
            "tax_rate": cost.tax_rate,
            "quoted_price": with_tax,
            "price_before_tax": with_profit,
        },
    }


class ConsumableCalculatorApiService:
    @staticmethod
    def quote(payload: CalculatorQuoteRequest) -> dict[str, Any]:
        try:
            joint_rows = [
                calculate_joint_quote(joint, payload.cost_params)
                for joint in payload.joints
            ]
        except ConsumableCalculationError as exc:
            raise ValueError(str(exc)) from exc

        summary = {
            "deposit_kg": 0.0,
            "suggested_primary_kg": 0.0,
            "enterprise_flux_kg": 0.0,
            "gas_volume_l": 0.0,
            "arc_time_h": 0.0,
            "total_time_h": 0.0,
            "material_cost": 0.0,
            "aux_cost": 0.0,
            "labor_cost": 0.0,
            "equipment_cost": 0.0,
            "direct_cost": 0.0,
            "quoted_price": 0.0,
            "price_before_tax": 0.0,
        }
        for row in joint_rows:
            totals = row["totals"]
            for key in summary:
                if key in totals:
                    summary[key] += totals[key]

        summary["profit_margin"] = payload.cost_params.profit_margin
        summary["tax_rate"] = payload.cost_params.tax_rate
        summary["direct_cost"] = (
            summary["material_cost"]
            + summary["aux_cost"]
            + summary["labor_cost"]
            + summary["equipment_cost"]
        )
        summary["price_before_tax"] = summary["direct_cost"] * (
            1 + payload.cost_params.profit_margin
        )
        summary["quoted_price"] = summary["price_before_tax"] * (
            1 + payload.cost_params.tax_rate
        )

        return {
            "project_name": payload.project_name,
            "customer": payload.customer,
            "cost_params": payload.cost_params.model_dump(),
            "joints": joint_rows,
            "summary": summary,
        }

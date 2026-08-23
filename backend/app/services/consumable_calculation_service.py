"""SQLAlchemy orchestration boundary around the pure P6 calculation package."""
from __future__ import annotations

from dataclasses import asdict

from app.consumable_calculation import (
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
)
from app.models.consumable import ConsumableGeometryInput, WeldConsumableOperation


class ConsumableCalculationService:
    """Maps relational records to immutable inputs; contains no formulas or prices."""

    @staticmethod
    def calculate_geometry(record: ConsumableGeometryInput) -> tuple[dict, dict]:
        confirmed = record.status == "confirmed" and record.confirmed_at is not None
        geometry = calculate_groove_area(
            GrooveGeometryInput(
                groove_type=GrooveType(record.groove_type),
                thickness_mm=record.thickness_mm,
                included_angle_deg=record.included_angle_deg,
                root_gap_mm=record.root_gap_mm,
                root_face_mm=record.root_face_mm,
                radius_mm=record.radius_mm,
                upper_bevel_height_mm=record.upper_bevel_height_mm,
                lower_bevel_height_mm=record.lower_bevel_height_mm,
                leg_size_mm=record.leg_size_mm,
                reinforcement_mm=record.reinforcement_mm,
                face_extra_each_side_mm=record.face_extra_each_side_mm,
                fill_factor=record.fill_factor,
                back_gouge_depth_mm=record.back_gouge_depth_mm,
                back_gouge_opening_width_mm=record.back_gouge_opening_width_mm,
                gouge_strategy=GougeStrategy(record.gouge_strategy),
                reference_gouge_flare_ratio=record.reference_gouge_flare_ratio,
                engineer_confirmed=confirmed,
                source=record.source,
            )
        )
        length = calculate_weld_length(
            WeldLengthInput(
                length_type=LengthType(record.length_type),
                count=record.weld_count,
                straight_length_mm=record.straight_length_mm,
                diameter_mm=record.diameter_mm,
                diameter_basis=(
                    DiameterBasis(record.diameter_basis)
                    if record.diameter_basis
                    else None
                ),
                included_angle_deg=record.included_length_angle_deg,
                manual_confirmed_length_mm=record.manual_confirmed_length_mm,
                engineer_confirmed=confirmed,
                source=record.source,
            )
        )
        return asdict(geometry), asdict(length)

    @staticmethod
    def calculate_operation(record: WeldConsumableOperation) -> dict:
        result = calculate_consumable_operation(
            ConsumableOperationInput(
                area_mm2=record.area_mm2,
                length_mm=record.length_mm,
                density_g_cm3=record.density_g_cm3,
                deposition_efficiency=record.deposition_efficiency,
                welding_method=record.welding_method,
                pass_count_description=record.pass_count_description,
                deposition_rate_kg_h=record.deposition_rate_kg_h,
                arc_time_h=record.arc_time_h,
                arc_time_ratio=record.arc_time_ratio,
                flux_wire_ratio=record.flux_wire_ratio,
                gas_flow_l_min=record.gas_flow_l_min,
            )
        )
        return asdict(result)

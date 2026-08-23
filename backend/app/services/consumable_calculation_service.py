"""SQLAlchemy orchestration boundary around the pure P6 calculation package."""
from __future__ import annotations

from dataclasses import asdict

from app.consumable_calculation import (
    AreaSource,
    ConsumableCalculationError,
    ConsumableOperationInput,
    ConsumableOperationPlan,
    DiameterBasis,
    GougeStrategy,
    GrooveGeometryInput,
    GrooveType,
    LengthType,
    OperationRole,
    WeldLengthInput,
    calculate_consumable_operation,
    calculate_operation_plan,
    calculate_groove_area,
    calculate_weld_length,
    summarize_operations,
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
                electrode_stub_loss_ratio=record.electrode_stub_loss_ratio or 0,
                spatter_loss_ratio=record.spatter_loss_ratio or 0,
                flux_loss_ratio=record.flux_loss_ratio or 0,
                enterprise_correction_factor=(record.enterprise_correction_factor or 1),
                package_size_kg=record.package_size_kg,
            )
        )
        return asdict(result)

    @classmethod
    def calculate_operations(
        cls,
        records: list[WeldConsumableOperation],
        geometry_result: dict,
    ) -> tuple[list[dict], dict]:
        """Calculate every persisted operation or fail; never collapse to one row."""
        if not records:
            raise ConsumableCalculationError("未配置焊材工序，不能静默回退为单工序")
        required = (
            "operation_role",
            "area_source",
            "welding_method",
            "area_mm2",
            "length_mm",
            "density_g_cm3",
            "deposition_efficiency",
        )
        calculated = []
        from app.consumable_calculation.models import GrooveAreaResult

        geometry = GrooveAreaResult(**geometry_result)
        allocation_totals: dict[str, float] = {}
        for record in records:
            if record.area_source != "independent":
                allocation_totals[record.area_source] = allocation_totals.get(
                    record.area_source, 0
                ) + float(record.area_allocation_ratio or 0)
        invalid_sources = [
            source
            for source, ratio in allocation_totals.items()
            if abs(ratio - 1.0) > 1e-9
        ]
        if invalid_sources:
            raise ConsumableCalculationError(
                "坡口面积分配比例合计必须等于1：" + ",".join(invalid_sources)
            )
        for record in sorted(records, key=lambda item: item.operation_order or 0):
            if record.status == "superseded" or any(
                getattr(record, name, None) is None for name in required
            ):
                raise ConsumableCalculationError(
                    f"持久化工序{getattr(record, 'id', None) or record.operation_order}损坏或不完整"
                )
            base = ConsumableOperationInput(
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
                electrode_stub_loss_ratio=record.electrode_stub_loss_ratio or 0,
                spatter_loss_ratio=record.spatter_loss_ratio or 0,
                flux_loss_ratio=record.flux_loss_ratio or 0,
                enterprise_correction_factor=record.enterprise_correction_factor or 1,
                package_size_kg=record.package_size_kg,
            )
            calculated.append(
                calculate_operation_plan(
                    ConsumableOperationPlan(
                        role=OperationRole(record.operation_role),
                        area_source=AreaSource(record.area_source),
                        operation=base,
                        area_allocation_ratio=record.area_allocation_ratio or 0,
                    ),
                    geometry,
                )
            )
        return [asdict(item) for item in calculated], asdict(
            summarize_operations(calculated)
        )

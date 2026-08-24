"""Immutable inputs and outputs. Field names carry the canonical units."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


FORMULA_VERSION = "P6-CONSUMABLE-1.0.0"


class GrooveType(str, Enum):
    I_BUTT = "I"
    V_BUTT = "V"
    X_BUTT = "X"
    U_BUTT = "U"
    FILLET = "FILLET"
    LAP = "LAP"
    BACK_GOUGE = "BACK_GOUGE"
    TP_V = "TP_V"
    TP_X = "TP_X"


class GougeStrategy(str, Enum):
    EXPLICIT = "explicit"
    REFERENCE_TRAPEZOID = "reference_trapezoid"


class LengthType(str, Enum):
    STRAIGHT = "straight"
    CIRCUMFERENTIAL = "circumferential"
    MANUAL_CONFIRMED = "manual_confirmed"


class DiameterBasis(str, Enum):
    INNER = "inner"
    MEAN = "mean"
    OUTER = "outer"


class OperationRole(str, Enum):
    FACE_FILL = "face_fill"
    BACK_GOUGE_FILL = "back_gouge_fill"
    TACK = "tack"
    CUSTOM = "custom"


class AreaSource(str, Enum):
    FRONT_FILL = "front_fill"
    BACK_GOUGE = "back_gouge"
    INDEPENDENT = "independent"


@dataclass(frozen=True)
class GrooveGeometryInput:
    groove_type: GrooveType
    thickness_mm: float = 0.0
    included_angle_deg: float = 0.0
    root_gap_mm: float = 0.0
    root_face_mm: float = 0.0
    radius_mm: float = 0.0
    upper_bevel_height_mm: float = 0.0
    lower_bevel_height_mm: float = 0.0
    leg_size_mm: float = 0.0
    reinforcement_mm: float = 0.0
    face_extra_each_side_mm: float = 0.0
    fill_factor: float = 1.0
    back_gouge_depth_mm: float = 0.0
    back_gouge_opening_width_mm: float | None = None
    gouge_strategy: GougeStrategy = GougeStrategy.EXPLICIT
    reference_gouge_flare_ratio: float = 0.5
    engineer_confirmed: bool = False
    source: str = "manual"


@dataclass(frozen=True)
class GrooveAreaResult:
    front_fill_geometry_mm2: float
    back_gouge_geometry_mm2: float
    back_reinforcement_geometry_mm2: float
    geometry_total_mm2: float
    fill_factor: float
    front_fill_adjusted_mm2: float
    back_gouge_adjusted_mm2: float
    back_reinforcement_adjusted_mm2: float
    total_area_mm2: float
    front_face_width_mm: float
    back_face_width_mm: float
    warnings: tuple[str, ...]
    formula_version: str = FORMULA_VERSION
    input_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WeldLengthInput:
    length_type: LengthType
    count: int = 1
    straight_length_mm: float | None = None
    diameter_mm: float | None = None
    diameter_basis: DiameterBasis | None = None
    included_angle_deg: float = 360.0
    manual_confirmed_length_mm: float | None = None
    engineer_confirmed: bool = False
    source: str = "manual"


@dataclass(frozen=True)
class WeldLengthResult:
    single_length_mm: float
    count: int
    total_length_mm: float
    diameter_basis: str | None
    included_angle_deg: float | None
    formula_version: str = FORMULA_VERSION
    input_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConsumableOperationInput:
    area_mm2: float
    length_mm: float
    density_g_cm3: float
    deposition_efficiency: float
    welding_method: str
    pass_count_description: int | None = None
    deposition_rate_kg_h: float | None = None
    arc_time_h: float | None = None
    arc_time_ratio: float | None = None
    flux_wire_ratio: float | None = None
    gas_flow_l_min: float | None = None
    electrode_stub_loss_ratio: float = 0.0
    spatter_loss_ratio: float = 0.0
    flux_loss_ratio: float = 0.0
    enterprise_correction_factor: float = 1.0
    package_size_kg: float | None = None
    area_unit: str = "mm2"
    length_unit: str = "mm"
    density_unit: str = "g/cm3"
    mass_unit: str = "kg"
    time_unit: str = "h"


@dataclass(frozen=True)
class ConsumableOperationResult:
    volume_mm3: float
    density_g_cm3: float
    deposit_mass_kg: float
    deposition_efficiency: float
    primary_consumable_kg: float
    process_primary_consumable_kg: float
    enterprise_primary_consumable_kg: float
    package_rounded_primary_kg: float
    suggested_primary_issue_kg: float
    flux_wire_ratio: float | None
    flux_kg: float | None
    process_flux_kg: float | None
    enterprise_flux_kg: float | None
    deposition_rate_kg_h: float | None
    arc_time_h: float | None
    arc_time_ratio: float | None
    total_operation_time_h: float | None
    gas_flow_l_min: float | None
    gas_volume_l: float | None
    pass_count_description: int | None
    pass_count_mass_multiplier: float
    result_sources: dict[str, str] = field(default_factory=dict)
    formula_version: str = FORMULA_VERSION
    input_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConsumableOperationPlan:
    role: OperationRole
    area_source: AreaSource
    operation: ConsumableOperationInput
    area_allocation_ratio: float = 1.0


@dataclass(frozen=True)
class ConsumableOperationsSummary:
    operation_count: int
    deposit_mass_kg: float
    primary_consumable_kg: float
    process_primary_consumable_kg: float
    enterprise_primary_consumable_kg: float
    package_rounded_primary_kg: float
    suggested_primary_issue_kg: float
    flux_kg: float
    process_flux_kg: float
    enterprise_flux_kg: float
    gas_volume_l: float
    arc_time_h: float
    total_operation_time_h: float
    formula_version: str = FORMULA_VERSION

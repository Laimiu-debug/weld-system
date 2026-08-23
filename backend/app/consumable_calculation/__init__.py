"""Framework-independent P6 consumable calculation API."""
from .calculation import calculate_consumable_operation
from .errors import ConsumableCalculationError
from .geometry import calculate_groove_area, geometry_warnings
from .length import calculate_weld_length
from .issue_list import (
    build_calibration_suggestion,
    build_consumable_issue_items,
    summarize_issue_items,
)
from .operations import calculate_operation_plan, summarize_operations
from .models import (
    AreaSource,
    FORMULA_VERSION,
    ConsumableOperationInput,
    ConsumableOperationResult,
    ConsumableOperationPlan,
    ConsumableOperationsSummary,
    DiameterBasis,
    GougeStrategy,
    GrooveAreaResult,
    GrooveGeometryInput,
    GrooveType,
    LengthType,
    OperationRole,
    WeldLengthInput,
    WeldLengthResult,
)

__all__ = [
    "FORMULA_VERSION",
    "AreaSource",
    "ConsumableCalculationError",
    "ConsumableOperationInput",
    "ConsumableOperationResult",
    "ConsumableOperationPlan",
    "ConsumableOperationsSummary",
    "DiameterBasis",
    "GougeStrategy",
    "GrooveAreaResult",
    "GrooveGeometryInput",
    "GrooveType",
    "LengthType",
    "OperationRole",
    "WeldLengthInput",
    "WeldLengthResult",
    "calculate_consumable_operation",
    "calculate_operation_plan",
    "calculate_groove_area",
    "calculate_weld_length",
    "geometry_warnings",
    "build_calibration_suggestion",
    "build_consumable_issue_items",
    "summarize_issue_items",
    "summarize_operations",
]

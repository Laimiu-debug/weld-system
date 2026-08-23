"""Framework-independent P6 consumable calculation API."""
from .calculation import calculate_consumable_operation
from .errors import ConsumableCalculationError
from .geometry import calculate_groove_area, geometry_warnings
from .length import calculate_weld_length
from .models import (
    FORMULA_VERSION,
    ConsumableOperationInput,
    ConsumableOperationResult,
    DiameterBasis,
    GougeStrategy,
    GrooveAreaResult,
    GrooveGeometryInput,
    GrooveType,
    LengthType,
    WeldLengthInput,
    WeldLengthResult,
)

__all__ = [
    "FORMULA_VERSION",
    "ConsumableCalculationError",
    "ConsumableOperationInput",
    "ConsumableOperationResult",
    "DiameterBasis",
    "GougeStrategy",
    "GrooveAreaResult",
    "GrooveGeometryInput",
    "GrooveType",
    "LengthType",
    "WeldLengthInput",
    "WeldLengthResult",
    "calculate_consumable_operation",
    "calculate_groove_area",
    "calculate_weld_length",
    "geometry_warnings",
]

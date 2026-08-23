"""Pure weld length calculations with explicit diameter basis."""
from __future__ import annotations

import math
from dataclasses import asdict

from .errors import ConsumableCalculationError
from .models import LengthType, WeldLengthInput, WeldLengthResult


def calculate_weld_length(value: WeldLengthInput) -> WeldLengthResult:
    if (
        not isinstance(value.count, int)
        or isinstance(value.count, bool)
        or value.count <= 0
    ):
        raise ConsumableCalculationError("焊缝数量必须是正整数")
    if value.source == "drawing" and not value.engineer_confirmed:
        raise ConsumableCalculationError("图纸解析长度必须经工程师确认后才能计算")
    angle: float | None = None
    basis: str | None = None
    if value.length_type == LengthType.STRAIGHT:
        length = value.straight_length_mm
        if length is None or not math.isfinite(length) or length <= 0:
            raise ConsumableCalculationError("直缝单条长度必须大于0")
    elif value.length_type == LengthType.CIRCUMFERENTIAL:
        diameter = value.diameter_mm
        if diameter is None or not math.isfinite(diameter) or diameter <= 0:
            raise ConsumableCalculationError("环缝直径必须大于0")
        if value.diameter_basis is None:
            raise ConsumableCalculationError("环缝必须明确采用内径、中径或外径")
        angle = value.included_angle_deg
        if not math.isfinite(angle) or not 0 < angle <= 360:
            raise ConsumableCalculationError("环缝包角必须大于0且不超过360度")
        length = math.pi * diameter * angle / 360.0
        basis = value.diameter_basis.value
    elif value.length_type == LengthType.MANUAL_CONFIRMED:
        length = value.manual_confirmed_length_mm
        if not value.engineer_confirmed:
            raise ConsumableCalculationError("手工长度必须经工程师确认")
        if length is None or not math.isfinite(length) or length <= 0:
            raise ConsumableCalculationError("手工确认长度必须大于0")
    else:
        raise ConsumableCalculationError(f"不支持的长度类型：{value.length_type}")
    return WeldLengthResult(
        single_length_mm=length,
        count=value.count,
        total_length_mm=length * value.count,
        diameter_basis=basis,
        included_angle_deg=angle,
        input_snapshot=asdict(value),
    )

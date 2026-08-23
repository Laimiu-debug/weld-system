"""Pure groove geometry functions; no persistence, clocks, files, or network."""
from __future__ import annotations

import math
from dataclasses import asdict

from .errors import ConsumableCalculationError
from .models import (
    GougeStrategy,
    GrooveAreaResult,
    GrooveGeometryInput,
    GrooveType,
)


BUTT_TYPES = {
    GrooveType.I_BUTT,
    GrooveType.V_BUTT,
    GrooveType.X_BUTT,
    GrooveType.U_BUTT,
}


def _finite_nonnegative(value: float, label: str) -> None:
    if not math.isfinite(value) or value < 0:
        raise ConsumableCalculationError(f"{label}必须是有限的非负数")


def _triangle(width: float, height: float) -> float:
    return 0.5 * max(width, 0.0) * max(height, 0.0)


def _half_tan(angle_deg: float) -> float:
    return math.tan(math.radians(angle_deg / 2.0))


def geometry_warnings(value: GrooveGeometryInput) -> tuple[str, ...]:
    warnings: list[str] = []
    if value.source == "drawing" and not value.engineer_confirmed:
        warnings.append("图纸解析几何尚未由工程师确认，不能作为正式定额输入")
    if value.fill_factor < 1.0:
        warnings.append("填充系数小于1.0，计算量低于理论几何量")
    elif value.fill_factor > 1.15:
        warnings.append("填充系数偏大；清根、展宽和损耗应使用独立参数")
    if value.groove_type in BUTT_TYPES:
        if value.root_face_mm > value.thickness_mm:
            warnings.append("钝边大于板厚")
        if value.back_gouge_depth_mm >= value.thickness_mm > 0:
            warnings.append("清根深度不应达到或超过板厚")
    if value.groove_type in {GrooveType.V_BUTT, GrooveType.X_BUTT, GrooveType.U_BUTT}:
        if not 0 < value.included_angle_deg < 180:
            warnings.append("坡口夹角应处于0到180度之间")
    available = max(value.thickness_mm - value.root_face_mm, 0.0)
    if value.groove_type == GrooveType.X_BUTT:
        upper = value.upper_bevel_height_mm
        lower = value.lower_bevel_height_mm
        if (
            upper > available
            or lower > available
            or (upper and lower and upper + lower > available)
        ):
            warnings.append("X形上下坡口高度超过可用板厚")
    if value.groove_type == GrooveType.U_BUTT and value.radius_mm >= available:
        warnings.append("U形坡口半径应小于板厚减钝边")
    if (
        value.gouge_strategy == GougeStrategy.REFERENCE_TRAPEZOID
        and value.back_gouge_depth_mm > 0
    ):
        warnings.append("清根槽采用参考三角/梯形近似，生产使用前必须由焊接工程师确认")
    return tuple(warnings)


def _validate(value: GrooveGeometryInput) -> None:
    for field_name, label in (
        ("thickness_mm", "板厚"),
        ("included_angle_deg", "坡口夹角"),
        ("root_gap_mm", "间隙"),
        ("root_face_mm", "钝边"),
        ("radius_mm", "半径"),
        ("upper_bevel_height_mm", "上坡口高度"),
        ("lower_bevel_height_mm", "下坡口高度"),
        ("leg_size_mm", "焊脚"),
        ("reinforcement_mm", "余高"),
        ("face_extra_each_side_mm", "单侧展宽"),
        ("back_gouge_depth_mm", "清根深度"),
    ):
        _finite_nonnegative(getattr(value, field_name), label)
    if not math.isfinite(value.fill_factor) or value.fill_factor <= 0:
        raise ConsumableCalculationError("填充系数必须大于0")
    if value.groove_type in BUTT_TYPES and value.thickness_mm <= 0:
        raise ConsumableCalculationError("对接焊板厚必须大于0")
    if (
        value.groove_type in {GrooveType.FILLET, GrooveType.LAP}
        and value.leg_size_mm <= 0
    ):
        raise ConsumableCalculationError("角焊或搭接焊焊脚必须大于0")
    if value.source == "drawing" and not value.engineer_confirmed:
        raise ConsumableCalculationError("图纸解析几何必须经工程师确认后才能计算")
    if value.back_gouge_depth_mm > 0 and value.gouge_strategy == GougeStrategy.EXPLICIT:
        width = value.back_gouge_opening_width_mm
        if width is None or not math.isfinite(width) or width <= 0:
            raise ConsumableCalculationError("显式清根策略必须提供大于0的清根槽开口宽度")
    if value.back_gouge_opening_width_mm is not None:
        _finite_nonnegative(value.back_gouge_opening_width_mm, "清根槽开口宽度")
    if value.reference_gouge_flare_ratio < 0 or not math.isfinite(
        value.reference_gouge_flare_ratio
    ):
        raise ConsumableCalculationError("清根参考张开系数必须是有限的非负数")


def _gouge(value: GrooveGeometryInput) -> tuple[float, float]:
    depth = value.back_gouge_depth_mm
    if depth <= 0 or value.groove_type not in BUTT_TYPES:
        return 0.0, 0.0
    if value.gouge_strategy == GougeStrategy.EXPLICIT:
        opening = float(value.back_gouge_opening_width_mm or 0.0)
    else:
        opening = value.root_gap_mm + 2 * value.reference_gouge_flare_ratio * depth
    cavity = depth * (max(value.root_gap_mm, 0.0) + opening) / 2.0
    return cavity, opening


def calculate_groove_area(value: GrooveGeometryInput) -> GrooveAreaResult:
    _validate(value)
    tan_half = _half_tan(value.included_angle_deg)
    extra = value.face_extra_each_side_mm
    front_width = 0.0
    back_width = 0.0
    front = 0.0
    back_reinforcement = 0.0

    if value.groove_type == GrooveType.I_BUTT:
        front_width = value.root_gap_mm + 2 * extra
        front = value.thickness_mm * value.root_gap_mm + _triangle(
            front_width, value.reinforcement_mm
        )
    elif value.groove_type == GrooveType.V_BUTT:
        height = max(value.thickness_mm - value.root_face_mm, 0.0)
        front_width = value.root_gap_mm + 2 * height * tan_half + 2 * extra
        front = (
            value.thickness_mm * value.root_gap_mm
            + height * height * tan_half
            + _triangle(front_width, value.reinforcement_mm)
        )
    elif value.groove_type == GrooveType.X_BUTT:
        available = max(value.thickness_mm - value.root_face_mm, 0.0)
        upper = value.upper_bevel_height_mm or available / 2.0
        lower = value.lower_bevel_height_mm or max(available - upper, 0.0)
        front_width = value.root_gap_mm + 2 * upper * tan_half + 2 * extra
        back_width = value.root_gap_mm + 2 * lower * tan_half + 2 * extra
        front = (
            value.thickness_mm * value.root_gap_mm
            + upper * upper * tan_half
            + lower * lower * tan_half
            + _triangle(front_width, value.reinforcement_mm)
        )
        back_reinforcement = _triangle(back_width, value.reinforcement_mm)
    elif value.groove_type == GrooveType.U_BUTT:
        radius = value.radius_mm
        straight = max(value.thickness_mm - value.root_face_mm - radius, 0.0)
        front_width = (
            value.root_gap_mm + 2 * radius + 2 * straight * tan_half + 2 * extra
        )
        front = (
            value.thickness_mm * value.root_gap_mm
            + 2 * radius * straight
            + straight * straight * tan_half
            + 0.5 * math.pi * radius * radius
            + _triangle(front_width, value.reinforcement_mm)
        )
    elif value.groove_type in {GrooveType.FILLET, GrooveType.LAP}:
        front_width = math.sqrt(2.0) * value.leg_size_mm + 2 * extra
        front = 0.5 * value.leg_size_mm**2 + _triangle(
            front_width, value.reinforcement_mm
        )
    else:
        raise ConsumableCalculationError(f"不支持的坡口形式：{value.groove_type}")

    gouge, gouge_width = _gouge(value)
    if gouge > 0 and value.groove_type != GrooveType.X_BUTT:
        back_width = gouge_width + 2 * extra
        back_reinforcement = _triangle(back_width, value.reinforcement_mm)
    geometry_total = front + gouge + back_reinforcement
    factor = value.fill_factor
    return GrooveAreaResult(
        front_fill_geometry_mm2=front,
        back_gouge_geometry_mm2=gouge,
        back_reinforcement_geometry_mm2=back_reinforcement,
        geometry_total_mm2=geometry_total,
        fill_factor=factor,
        front_fill_adjusted_mm2=front * factor,
        back_gouge_adjusted_mm2=gouge * factor,
        back_reinforcement_adjusted_mm2=back_reinforcement * factor,
        total_area_mm2=geometry_total * factor,
        front_face_width_mm=front_width,
        back_face_width_mm=back_width,
        warnings=geometry_warnings(value),
        input_snapshot=asdict(value),
    )

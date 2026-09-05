"""Validate observations against the released WPS; never infer missing limits."""
import math
import re


def _number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def parse_range(value, unit):
    if _number(value):
        return float(value), float(value)
    if not isinstance(value, str):
        raise ValueError("范围格式无效")
    text = value.strip().replace("℃", "°C").replace("～", "~").replace("至", "~")
    number = r"(?:\d+(?:\.\d+)?)"
    suffix = rf"\s*(?:{re.escape(unit)})?\s*"
    match = re.fullmatch(
        rf"({number}){suffix}[-~–—]{{1}}\s*({number}){suffix}", text, re.I
    )
    if match:
        low, high = map(float, match.groups())
        if low > high:
            raise ValueError("上下限倒置")
        return low, high
    match = re.fullmatch(rf"(>=|<=|≥|≤)\s*({number}){suffix}", text, re.I)
    if match:
        value = float(match[2])
        return (value, None) if match[1] in {">=", "≥"} else (None, value)
    match = re.fullmatch(rf"({number}){suffix}", text, re.I)
    if match:
        return float(match[1]), float(match[1])
    raise ValueError("范围或单位无法可靠解析")


def parameter_report(wps, actual):
    """Actual units: A, V, mm/min, kJ/mm and degrees Celsius."""
    limits, issues = {}, []
    for name, field, unit in (
        ("current", "current_range", "A"),
        ("voltage", "voltage_range", "V"),
        ("travel_speed", "travel_speed", "mm/min"),
        ("travel_speed", "welding_speed", "mm/min"),
    ):
        value = wps.get(field)
        if value in (None, ""):
            continue
        try:
            low, high = parse_range(value, unit)
            if name in limits:
                old_low, old_high = limits[name]
                low = (
                    max(x for x in (low, old_low) if x is not None)
                    if low is not None or old_low is not None
                    else None
                )
                high = (
                    min(x for x in (high, old_high) if x is not None)
                    if high is not None or old_high is not None
                    else None
                )
            if low is not None and high is not None and low > high:
                raise ValueError("冻结范围互相冲突")
            limits[name] = (low, high)
        except ValueError as exc:
            issues.append(f"冻结 WPS 的 {field} {exc}")
    for name, lower, upper in (
        ("heat_input", "heat_input_min", "heat_input_max"),
        ("preheat_temperature", "preheat_temp_min", "preheat_temp_max"),
        ("interpass_temperature", None, "interpass_temp_max"),
    ):
        low, high = wps.get(lower), wps.get(upper)
        if low is None and high is None:
            continue
        if any(v is not None and not _number(v) for v in (low, high)) or (
            low is not None and high is not None and low > high
        ):
            issues.append(f"冻结 WPS 的 {name} 范围无效")
        else:
            limits[name] = (low, high)
    if not limits:
        issues.append("冻结 WPS 缺少可校验的工艺参数范围，请完善工艺并重新冻结放行")
    for name, value in actual.items():
        if not _number(value):
            issues.append(f"{name} 必须是有限数值")
    for name, (low, high) in limits.items():
        value = actual.get(name)
        if value is None:
            issues.append(f"缺少实测参数 {name}")
        elif _number(value) and (
            (low is not None and value < low) or (high is not None and value > high)
        ):
            issues.append(
                f"{name}={value} 超出冻结范围 {low if low is not None else '不限'}～{high if high is not None else '不限'}"
            )
    return {
        "source": "released_wps",
        "limits": limits,
        "issues": issues,
        "passed": not issues,
    }


def inspection_closed(inspection):
    if inspection is None:
        return False
    requires_followup = (
        any(
            getattr(inspection, key, False)
            for key in (
                "repair_required",
                "reinspection_required",
                "corrective_action_required",
            )
        )
        or inspection.inspection_result == "fail"
    )
    if not requires_followup:
        return inspection.inspection_result == "pass"
    if (
        getattr(inspection, "repair_required", False)
        and not (getattr(inspection, "repair_description", None) or "").strip()
    ):
        return False
    inspected = getattr(inspection, "inspection_date", None)
    reinspected = getattr(inspection, "reinspection_date", None)
    return bool(
        getattr(inspection, "reinspection_result", None) == "pass"
        and reinspected
        and (not inspected or reinspected >= inspected)
        and getattr(inspection, "reinspection_inspector_id", None)
        and (getattr(inspection, "reinspection_notes", None) or "").strip()
    )

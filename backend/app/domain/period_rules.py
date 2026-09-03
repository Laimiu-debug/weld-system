"""Shared period calculation for certification and maintenance due dates."""
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta


def calculate_next_due(base_date: date, period: int, unit: str = "days") -> date:
    if period <= 0:
        raise ValueError("周期必须大于 0")
    if unit == "days":
        return base_date + timedelta(days=period)
    if unit == "months":
        month_index = base_date.month - 1 + period
        year = base_date.year + month_index // 12
        month = month_index % 12 + 1
        return date(year, month, min(base_date.day, monthrange(year, month)[1]))
    raise ValueError("周期单位仅支持 days 或 months")

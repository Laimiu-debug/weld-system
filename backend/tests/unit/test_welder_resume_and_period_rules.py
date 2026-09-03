from datetime import date
from types import SimpleNamespace

from app.domain.period_rules import calculate_next_due
from app.services.welder_resume_service import _build_reportlab_pdf


def test_period_rule_supports_days_and_end_of_month() -> None:
    assert calculate_next_due(date(2026, 9, 3), 30) == date(2026, 10, 3)
    assert calculate_next_due(date(2025, 1, 31), 1, "months") == date(2025, 2, 28)


def test_reportlab_resume_fallback_generates_chinese_pdf() -> None:
    welder = SimpleNamespace(
        full_name="张三",
        welder_code="W-001",
        department="焊接部",
        position="焊工",
        phone="13800000000",
        status="active",
    )
    result = _build_reportlab_pdf(welder, [], [])
    assert result.startswith(b"%PDF")
    assert len(result) > 1000

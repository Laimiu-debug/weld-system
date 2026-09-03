from datetime import date
from types import SimpleNamespace

from app.domain.period_rules import calculate_next_due
from app.services.welder_resume_service import _build_reportlab_pdf
from app.services import welder_resume_service


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


def test_resume_uses_reportlab_when_weasyprint_rendering_fails(monkeypatch) -> None:
    class BrokenHTML:
        def __init__(self, **_kwargs) -> None:
            pass

        def write_pdf(self) -> bytes:
            raise TypeError("incompatible pydyf")

    welder = SimpleNamespace(
        full_name="张三",
        welder_code="W-001",
        department="焊接部",
        position="焊工",
        phone="13800000000",
        status="active",
    )
    monkeypatch.setattr(welder_resume_service, "HTML", BrokenHTML)
    monkeypatch.setattr(
        welder_resume_service.WelderService,
        "get_welder_by_id",
        lambda *_args, **_kwargs: welder,
    )
    monkeypatch.setattr(
        welder_resume_service.WelderService,
        "get_certifications",
        lambda *_args, **_kwargs: ([], 0),
    )
    monkeypatch.setattr(
        welder_resume_service.WelderService,
        "get_work_histories",
        lambda *_args, **_kwargs: ([], 0),
    )

    result, _filename = welder_resume_service.build_welder_resume_pdf(
        db=None,
        welder_id=1,
        current_user=SimpleNamespace(id=1),
        workspace=SimpleNamespace(),
    )
    assert result.startswith(b"%PDF")

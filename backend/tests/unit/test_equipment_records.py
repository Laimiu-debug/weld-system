"""Equipment maintenance/usage helpers."""
from unittest.mock import MagicMock

from app.services.equipment_service import EquipmentService


def test_parse_datetime_accepts_date_and_iso():
    service = EquipmentService(MagicMock())
    assert service._parse_datetime(None) is None
    parsed_date = service._parse_datetime("2026-08-19")
    assert parsed_date is not None
    assert parsed_date.date().isoformat() == "2026-08-19"
    parsed_iso = service._parse_datetime("2026-08-19T10:30:00")
    assert parsed_iso is not None
    assert parsed_iso.hour == 10
    assert parsed_iso.minute == 30


def test_parse_date_from_datetime_string():
    service = EquipmentService(MagicMock())
    parsed = service._parse_date("2026-08-19T08:00:00")
    assert parsed is not None
    assert parsed.isoformat() == "2026-08-19"

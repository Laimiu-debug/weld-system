from datetime import date, timedelta
from types import SimpleNamespace

from app.services.welder_import_service import (
    _date_value,
    _expiry_status,
    WelderImportService,
)


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


def test_welder_import_expiry_states_cover_expired_soon_and_valid() -> None:
    assert _expiry_status(date.today() - timedelta(days=1)) == "expired"
    assert _expiry_status(date.today() + timedelta(days=10)) == "expiring_soon"
    assert _expiry_status(date.today() + timedelta(days=100)) == "valid"
    assert _date_value("2028/06/30") == date(2028, 6, 30)


def test_project_name_contains_all_qualification_dimensions() -> None:
    name = WelderImportService._project_name(
        {
            "welding_process": "GTAW",
            "welding_position": "6G",
            "material_group": "Fe IV",
            "thickness_range": "3-12 mm",
            "diameter_range": ">= 25 mm",
        }
    )

    assert name == "GTAW / 6G / Fe IV / 3-12 mm / >= 25 mm"


def test_roster_rows_for_same_certificate_become_multiple_projects() -> None:
    fields = [
        SimpleNamespace(
            field_key="welder_records",
            review_status="accepted",
            normalized_value=[
                {
                    "full_name": "张三",
                    "welder_code": "W-1",
                    "certification_number": "C-1",
                    "certification_type": "ISO 9606",
                    "welding_process": "GTAW",
                    "welding_position": "6G",
                },
                {
                    "full_name": "张三",
                    "welder_code": "W-1",
                    "certification_number": "C-1",
                    "certification_type": "ISO 9606",
                    "welding_process": "SMAW",
                    "welding_position": "3G",
                },
            ],
        )
    ]
    service = WelderImportService.__new__(WelderImportService)
    service.db = SimpleNamespace(query=lambda model: _Query(fields))

    records = service._records(SimpleNamespace(id="entity-1", draft_data={}))

    assert len(records) == 1
    assert [item["welding_process"] for item in records[0]["qualified_projects"]] == [
        "GTAW",
        "SMAW",
    ]


def test_identity_review_marks_renewal_and_same_name_ambiguity() -> None:
    welder = SimpleNamespace(id=7, welder_code="W-7", full_name="李四", id_number="ID-7")
    cert = SimpleNamespace(id=9, welder_id=7, expiry_date=date(2027, 1, 1))
    service = WelderImportService.__new__(WelderImportService)
    service._welder_query = lambda context: _Query([welder])
    service.db = SimpleNamespace(query=lambda model: _Query([cert]))

    renewal = service._review_record(
        {
            "full_name": "李四",
            "welder_code": "W-7",
            "certification_number": "C-7",
            "certification_type": "ISO 9606",
            "expiry_date": "2028-01-01",
        },
        SimpleNamespace(),
    )
    service.db = SimpleNamespace(query=lambda model: _Query([]))
    same_name = service._review_record(
        {"full_name": "李四", "certification_number": "", "certification_type": ""},
        SimpleNamespace(),
    )

    assert renewal["identity_status"] == "matched"
    assert renewal["certificate_status"] == "renewal"
    assert same_name["identity_status"] == "ambiguous"

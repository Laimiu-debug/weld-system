from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from app.models.pqr import PQR
from app.models.qualification import PQRQualificationResult, WPSPQRSupportLink
from app.models.wps import WPS
from app.services.capability_service import (
    CapabilityLibraryService,
    _health,
    _link_stale,
    scope_covers_requirement,
    welder_covers_requirement,
)
from app.services.qualification_service import (
    _hash,
    _legacy_record_hash,
    _record_snapshot,
    _version_key,
)


def _scope(**overrides):
    scope = {
        "welding_processes": ["GTAW"],
        "material_groups": ["Fe-1"],
        "positions": ["PA"],
        "thickness": {"min_mm": 5, "max_mm": 20},
        "diameter": {"applicable": False},
        "pwht": {"performed": False},
        "impact": {"required": False},
    }
    scope.update(overrides)
    return scope


def _requirement(**overrides):
    values = {
        "welding_process": "GTAW",
        "material_group": "Fe-1",
        "welding_position": "PA",
        "thickness_mm": 10,
        "diameter_mm": None,
        "pwht_required": False,
        "impact_required": False,
        "impact_temperature_c": None,
    }
    values.update(overrides)
    return values


def test_scope_match_accepts_only_complete_coverage() -> None:
    assert scope_covers_requirement(_scope(), _requirement()) is True


def test_scope_match_rejects_thickness_outside_range() -> None:
    assert scope_covers_requirement(_scope(), _requirement(thickness_mm=25)) is False


def test_scope_match_does_not_guess_missing_position() -> None:
    assert scope_covers_requirement(_scope(positions=[]), _requirement()) is False


def test_scope_match_requires_explicit_pipe_diameter_coverage() -> None:
    assert scope_covers_requirement(_scope(), _requirement(diameter_mm=168.3)) is False
    assert (
        scope_covers_requirement(
            _scope(
                diameter={
                    "applicable": True,
                    "min_mm": 168.3,
                    "max_mm": 168.3,
                }
            ),
            _requirement(diameter_mm=168.3),
        )
        is True
    )


def test_scope_match_enforces_pwht_and_impact_temperature() -> None:
    assert scope_covers_requirement(_scope(), _requirement(pwht_required=True)) is False
    scope = _scope(
        impact={
            "required": True,
            "tested_temperature_c": -20,
        }
    )
    assert (
        scope_covers_requirement(
            scope,
            _requirement(impact_required=True, impact_temperature_c=-10),
        )
        is True
    )
    assert (
        scope_covers_requirement(
            scope,
            _requirement(impact_required=True, impact_temperature_c=-40),
        )
        is False
    )


def test_welder_match_requires_process_material_position_and_thickness() -> None:
    welder = {
        "qualifications": [
            {
                "process": "GTAW",
                "material_group": "Fe-1",
                "position": "PA,PB",
                "thickness_range": "3-18 mm",
            }
        ]
    }
    assert welder_covers_requirement(welder, _requirement()) is True
    assert (
        welder_covers_requirement(welder, _requirement(welding_position="PC")) is False
    )
    assert welder_covers_requirement(welder, _requirement(thickness_mm=20)) is False


def test_versioned_link_is_stale_after_wps_change() -> None:
    now = datetime(2026, 8, 23, 12, 0, 0)
    wps = WPS(
        id=1,
        user_id=7,
        workspace_type="personal",
        access_level="private",
        wps_number="WPS-1",
        title="WPS",
        revision="A",
        status="approved",
        created_by=7,
        created_at=now,
        updated_at=now,
    )
    pqr = PQR(
        id=2,
        user_id=7,
        workspace_type="personal",
        access_level="private",
        pqr_number="PQR-2",
        title="PQR",
        status="approved",
        created_by=7,
        created_at=now,
        updated_at=now,
    )
    link = WPSPQRSupportLink(
        wps_snapshot_hash=_hash(_record_snapshot(wps)),
        pqr_snapshot_hash=_hash(_record_snapshot(pqr)),
    )
    assert _link_stale(link, wps, pqr) is False
    wps.revision = "B"
    assert _link_stale(link, wps, pqr) is True


def test_legacy_link_fingerprint_detects_record_change() -> None:
    now = datetime(2026, 8, 23, 12, 0, 0)
    wps = SimpleNamespace(id=1, updated_at=now)
    pqr = SimpleNamespace(id=2, updated_at=now)
    link = SimpleNamespace(
        wps_snapshot_hash=_legacy_record_hash(wps),
        pqr_snapshot_hash=_legacy_record_hash(pqr),
    )
    assert _link_stale(link, wps, pqr) is False
    pqr.updated_at = now + timedelta(seconds=1)
    assert _link_stale(link, wps, pqr) is True


def test_valid_capability_requires_current_qualified_exact_result() -> None:
    now = datetime(2026, 8, 23, 12, 0, 0)
    wps = WPS(
        id=1,
        user_id=7,
        workspace_type="personal",
        access_level="private",
        wps_number="WPS-1",
        title="WPS",
        revision="A",
        status="approved",
        is_active=True,
        created_by=7,
        created_at=now,
        updated_at=now,
    )
    pqr = PQR(
        id=2,
        user_id=7,
        workspace_type="personal",
        access_level="private",
        pqr_number="PQR-2",
        title="PQR",
        status="approved",
        is_active=True,
        created_by=7,
        created_at=now,
        updated_at=now,
    )
    pqr_version = _version_key(pqr, "pqr")
    result = PQRQualificationResult(
        id="result-1",
        pqr_id=2,
        pqr_version_key=pqr_version,
        rule_pack_id="pack-1",
        rule_pack_version="1.0.0",
        outcome="qualified",
        is_current=True,
        requires_human_confirmation=False,
        result={"qualification_scope": _scope()},
        basis=[],
    )
    link = WPSPQRSupportLink(
        id="link-1",
        wps_id=1,
        pqr_id=2,
        qualification_result_id="result-1",
        wps_snapshot_hash=_hash(_record_snapshot(wps)),
        pqr_snapshot_hash=_hash(_record_snapshot(pqr)),
        wps_version_key=_version_key(wps, "wps"),
        pqr_version_key=pqr_version,
        supported_processes=["GTAW"],
        qualified_scope=_scope(),
        source="manual",
        confirmation_status="confirmed",
        is_active=True,
    )
    service = CapabilityLibraryService(Mock())
    entries, state = service._valid_capabilities(
        [link], {1: wps}, {2: pqr}, {"result-1": result}, {}
    )
    assert len(entries) == 1
    assert state["valid"] == 1

    result.requires_human_confirmation = True
    entries, state = service._valid_capabilities(
        [link], {1: wps}, {2: pqr}, {"result-1": result}, {}
    )
    assert entries == []
    assert state["stale"] == 1


def test_health_never_hides_blocking_gaps() -> None:
    issues = [
        {
            "severity": "blocking",
            "code": "WPS_WITHOUT_VALID_PQR",
        }
    ]
    health = _health(issues, [SimpleNamespace()], [], [])
    assert health["score"] < 85
    assert health["status"] != "healthy"


def test_empty_library_is_reported_as_blocking_gap() -> None:
    issues = CapabilityLibraryService._issues(
        [], [], [], [], [], {"pending": 0, "stale": 0}, []
    )
    assert any(item["code"] == "NO_VALID_CAPABILITY_DATA" for item in issues)

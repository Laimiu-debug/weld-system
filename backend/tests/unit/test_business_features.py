"""Unit tests for newly completed production / quality / pPQR / report helpers."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import deps
from app.api.v1.endpoints import reports
from app.services.ppqr_service import generate_pqr_number_from_ppqr, map_ppqr_to_pqr_fields
from app.services.report_service import ReportService


def test_map_ppqr_to_pqr_copies_process_and_conclusion():
    ppqr = SimpleNamespace(
        title="试验工艺",
        ppqr_number="PPQR-001",
        welding_process="GMAW",
        actual_current=180,
        actual_voltage=24,
        test_conclusion="qualified",
        actual_test_date=None,
        planned_test_date=None,
        module_data={"joint": {}},
        welder_name="张三",
    )
    payload = map_ppqr_to_pqr_fields(ppqr)
    assert payload["title"] == "试验工艺"
    assert payload["welding_process"] == "GMAW"
    assert payload["current_actual"] == 180
    assert payload["voltage_actual"] == 24
    assert payload["qualification_result"] == "qualified"
    assert payload["modules_data"] == {"joint": {}}
    assert payload["welding_operator"] == "张三"
    assert payload["status"] == "draft"


def test_generate_pqr_number_from_ppqr_adds_suffix_and_truncates():
    assert generate_pqr_number_from_ppqr("A1") == "PQR-A1"
    assert generate_pqr_number_from_ppqr("A1", 2) == "PQR-A1-2"
    long_number = "X" * 80
    assert len(generate_pqr_number_from_ppqr(long_number)) <= 50


def test_reports_catalog_returns_available_reports():
    app = FastAPI()
    app.include_router(reports.router, prefix="/reports")
    app.dependency_overrides[deps.get_current_active_user] = lambda: SimpleNamespace(id=1)
    client = TestClient(app)
    response = client.get("/reports/")
    assert response.status_code == 200
    body = response.json()
    keys = {item["key"] for item in body["data"]["items"]}
    assert {"wps", "pqr", "quality", "usage", "production"} <= keys
    assert ReportService.get_catalog()[0]["path"].startswith("/reports")


def test_progress_clamped_by_update_task_progress():
    from app.services.production_service import ProductionService

    task = SimpleNamespace(
        production_release_id=None,
        progress_percentage=0,
        status="pending",
        actual_start_date=None,
        actual_end_date=None,
        notes=None,
        updated_by=None,
        updated_at=None,
    )
    service = ProductionService(MagicMock())
    service.get_production_task_by_id = lambda *args, **kwargs: task
    service.data_access.check_access = lambda *args, **kwargs: True
    service.db.commit = MagicMock()
    service.db.refresh = MagicMock()

    updated = service.update_task_progress(
        task_id=1,
        current_user=SimpleNamespace(id=9),
        workspace_context=SimpleNamespace(),
        progress_percentage=150,
    )
    assert updated.progress_percentage == 100
    assert updated.status == "completed"

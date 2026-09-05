"""Ensure named material routes are not captured by the numeric detail route."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.routing import Match

from app.api import deps
from app.api.v1.endpoints import materials


def test_transaction_list_reaches_service_with_material_and_pagination(monkeypatch):
    service = MagicMock()
    service.get_transaction_list.return_value = {"items": [], "total": 0}
    monkeypatch.setattr(materials, "MaterialService", lambda db: service)
    app = FastAPI()
    app.include_router(materials.router, prefix="/materials")
    user = SimpleNamespace(id=17)
    app.dependency_overrides[deps.get_current_active_user] = lambda: user
    app.dependency_overrides[deps.get_db] = lambda: MagicMock()
    response = TestClient(app).get(
        "/materials/transactions",
        params={"workspace_type": "personal", "material_id": 42, "skip": 20, "limit": 10},
    )
    assert response.status_code == 200
    assert response.json()["data"] == {"items": [], "total": 0}
    args = service.get_transaction_list.call_args.kwargs
    assert args["current_user"] is user
    assert args["material_id"] == 42
    assert args["skip"] == 20
    assert args["limit"] == 10


def test_numeric_material_detail_still_routes_to_detail():
    scope = {"type": "http", "path": "/42", "method": "GET"}
    matches = [route for route in materials.router.routes if route.matches(scope)[0] == Match.FULL]
    assert len(matches) == 1
    assert matches[0].endpoint.__name__ == "get_material_detail"

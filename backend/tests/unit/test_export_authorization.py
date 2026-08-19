"""HTTP-level tests: export endpoints enforce access before generating files."""
import io
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.v1.endpoints import ppqr_export, pqr_export, wps_export
from app.core.database import get_db


def _client_for(router, prefix: str, user_id: int = 1) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix=prefix)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=user_id, is_active=True
    )
    app.dependency_overrides[get_db] = lambda: MagicMock()
    return TestClient(app)


def _unauthorized_client(router, prefix: str) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix=prefix)
    app.dependency_overrides[get_db] = lambda: MagicMock()
    return TestClient(app)


EXPORT_CASES = [
    (wps_export, "/api/v1/wps", "/api/v1/wps/1/export/word", "/api/v1/wps/1/export/pdf"),
    (pqr_export, "/api/v1/pqr", "/api/v1/pqr/1/export/word", "/api/v1/pqr/1/export/pdf"),
    (ppqr_export, "/api/v1/ppqr", "/api/v1/ppqr/1/export/word", "/api/v1/ppqr/1/export/pdf"),
]


@pytest.mark.parametrize("module, prefix, word_path, pdf_path", EXPORT_CASES)
@pytest.mark.parametrize("path_attr", ["word_path", "pdf_path"])
def test_unauthenticated_export_is_rejected(module, prefix, word_path, pdf_path, path_attr):
    client = _unauthorized_client(module.router, prefix)
    path = word_path if path_attr == "word_path" else pdf_path
    response = client.post(path)
    assert response.status_code in (401, 403)


@pytest.mark.parametrize("module, prefix, word_path, pdf_path", EXPORT_CASES)
def test_cross_tenant_export_returns_403(module, prefix, word_path, pdf_path):
    client = _client_for(module.router, prefix, user_id=2)
    patch_target = f"{module.__name__}.require_document_access"
    with patch(patch_target, side_effect=HTTPException(status_code=403, detail="权限不足")):
        word = client.post(word_path)
        pdf = client.post(pdf_path)
    assert word.status_code == 403
    assert pdf.status_code == 403
    assert "权限" in (word.json().get("detail") or "")


@pytest.mark.parametrize("module, prefix, word_path, pdf_path", EXPORT_CASES)
def test_missing_document_export_returns_404(module, prefix, word_path, pdf_path):
    client = _client_for(module.router, prefix, user_id=1)
    patch_target = f"{module.__name__}.require_document_access"
    with patch(patch_target, side_effect=HTTPException(status_code=404, detail="不存在")):
        response = client.post(word_path)
    assert response.status_code == 404


@pytest.mark.parametrize(
    "module, prefix, word_path, export_method, number_attr",
    [
        (wps_export, "/api/v1/wps", "/api/v1/wps/7/export/word", "export_wps_to_word", "wps_number"),
        (pqr_export, "/api/v1/pqr", "/api/v1/pqr/7/export/word", "export_pqr_to_word", "pqr_number"),
        (ppqr_export, "/api/v1/ppqr", "/api/v1/ppqr/7/export/word", "export_ppqr_to_word", "ppqr_number"),
    ],
)
def test_same_tenant_export_returns_file(module, prefix, word_path, export_method, number_attr):
    client = _client_for(module.router, prefix, user_id=1)
    document = SimpleNamespace(**{number_attr: "DOC-7"})
    patch_access = f"{module.__name__}.require_document_access"
    patch_service = f"{module.__name__}.DocumentExportService"
    with patch(patch_access, return_value=document), patch(patch_service) as service_cls:
        getattr(service_cls.return_value, export_method).return_value = io.BytesIO(b"file-bytes")
        response = client.post(word_path)
    assert response.status_code == 200
    assert response.content == b"file-bytes"
    getattr(service_cls.return_value, export_method).assert_called_once()


def _pqr_id_client(user_id: int = 1) -> TestClient:
    from app.api import deps
    from app.api.v1.endpoints import pqr as pqr_endpoints

    app = FastAPI()
    app.include_router(pqr_endpoints.router, prefix="/api/v1/pqr")
    app.dependency_overrides[deps.get_current_active_user] = lambda: SimpleNamespace(
        id=user_id, is_active=True, membership_type="personal", is_superuser=False
    )
    app.dependency_overrides[deps.get_db] = lambda: MagicMock()
    return TestClient(app)


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/api/v1/pqr/1/export/pdf"),
        ("get", "/api/v1/pqr/1/export/excel"),
        ("get", "/api/v1/pqr/1/specimens/"),
        ("post", "/api/v1/pqr/export"),
    ],
)
def test_pqr_id_routes_reject_cross_tenant(method, path):
    client = _pqr_id_client(user_id=2)
    with patch(
        "app.api.v1.endpoints.pqr.require_document_access",
        side_effect=HTTPException(status_code=403, detail="权限不足"),
    ):
        if method == "get":
            response = client.get(path)
        else:
            response = client.post(path, json={"pqr_ids": [1], "export_format": "pdf"})
    assert response.status_code == 403


def test_pqr_id_export_pdf_same_tenant_ok():
    client = _pqr_id_client(user_id=1)
    document = SimpleNamespace(pqr_number="PQR-1")
    with patch(
        "app.api.v1.endpoints.pqr.require_document_access",
        return_value=document,
    ), patch("app.api.v1.endpoints.pqr.DocumentExportService") as service_cls:
        service_cls.return_value.export_pqr_to_pdf.return_value = io.BytesIO(b"%PDF-fake")
        response = client.get("/api/v1/pqr/1/export/pdf")
    assert response.status_code == 200
    assert response.content == b"%PDF-fake"
    service_cls.return_value.export_pqr_to_pdf.assert_called_once()

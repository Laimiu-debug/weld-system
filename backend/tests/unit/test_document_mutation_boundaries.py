from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Query, Session

from app.api import deps
from app.api.v1.endpoints import pqr, wps
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.schemas.wps import WPSUpdate
from app.services.pqr_service import PQRService
from app.services.ppqr_service import PPQRService
from app.services.wps_service import WPSService, validate_direct_wps_write


@pytest.mark.parametrize("workspace_type,company", [(WorkspaceType.PERSONAL, None), (WorkspaceType.ENTERPRISE, 8)])
def test_advanced_search_always_scopes_sql_even_with_owner_filter(workspace_type, company):
    session = Session()
    user = NS(id=7)
    context = WorkspaceContext(7, workspace_type, company_id=company)
    service = PQRService(session)
    membership_db = Mock()
    membership_db.query.return_value.filter.return_value.first.return_value = NS(owner_id=7)
    service.data_access.db = membership_db
    with patch.object(Query, "all", autospec=True, return_value=[]) as execute:
        service.search_pqr(session, search_params={"owner_id": 99}, current_user=user, workspace_context=context)
    statement = str(execute.call_args.args[0].statement.compile(compile_kwargs={"literal_binds": True}))
    where = statement.split("WHERE", 1)[1]
    assert f"workspace_type = '{workspace_type}'" in where
    assert "owner_id = 99" in where
    assert ("user_id = 7" if company is None else "company_id = 8") in where
    session.close()


def test_search_endpoint_checks_permission_and_passes_workspace(monkeypatch):
    app = FastAPI()
    app.include_router(pqr.router, prefix="/pqr")
    user, db = NS(id=7), Mock()
    context = WorkspaceContext(7, WorkspaceType.PERSONAL)
    app.dependency_overrides[deps.get_current_active_user] = lambda: user
    app.dependency_overrides[deps.get_db] = lambda: db
    resolve, permission, service = Mock(return_value=context), Mock(), Mock()
    service.search_pqr.return_value = []
    monkeypatch.setattr(pqr, "get_workspace_context", resolve)
    monkeypatch.setattr(pqr, "ensure_module_permission", permission)
    monkeypatch.setattr(pqr, "PQRService", lambda db: service)
    client = TestClient(app)
    assert client.post("/pqr/search", json={}, headers={"X-Workspace-ID": "personal_7"}).status_code == 200
    resolve.assert_called_once_with(db, user, "personal_7")
    assert service.search_pqr.call_args.kwargs["workspace_context"] is context
    permission.assert_called_once_with(db, user, "pqr", "read")
    permission.side_effect = HTTPException(403, "无读取权限")
    service.search_pqr.reset_mock()
    assert client.post("/pqr/search", json={}).status_code == 403
    service.search_pqr.assert_not_called()


@pytest.mark.parametrize("payload", [
    {"status": "approved"}, {"status": "reviewed"}, {"approved_by": 99}, {"reviewed_by": 99},
])
def test_wps_status_api_cannot_bypass_approval(monkeypatch, payload):
    app = FastAPI()
    app.include_router(wps.router, prefix="/wps")
    db, user = Mock(), NS(id=7)
    context = WorkspaceContext(7, WorkspaceType.PERSONAL)
    app.dependency_overrides[deps.get_current_active_user] = lambda: user
    app.dependency_overrides[deps.get_db] = lambda: db
    service = WPSService(db)
    service.get = Mock(return_value=NS(id=1, status="draft"))
    service.data_access = Mock()
    monkeypatch.setattr(wps, "get_workspace_context", Mock(return_value=context))
    monkeypatch.setattr(wps, "ensure_module_permission", Mock())
    monkeypatch.setattr(wps, "WPSService", lambda db: service)
    response = TestClient(app).put("/wps/1/status/", json={"status": "draft", **payload})
    assert response.status_code == 409
    db.commit.assert_not_called()


def test_wps_regular_update_cannot_be_used_as_an_alternative_approval_path():
    db = Mock()
    service = WPSService(db)
    service._check_update_permission = Mock(return_value=True)
    with pytest.raises(HTTPException) as exc:
        service.update(db, db_obj=NS(status="draft"), obj_in=WPSUpdate(status="approved"),
                       current_user=NS(id=7), workspace_context=WorkspaceContext(7, WorkspaceType.PERSONAL))
    assert exc.value.status_code == 409
    db.commit.assert_not_called()


def test_manual_wps_transitions_preserve_signed_and_pending_states():
    validate_direct_wps_write({"status": "draft"})
    validate_direct_wps_write({"status": "obsolete"}, "approved")
    for current in ["approved", "obsolete", "pending", "in_progress"]:
        with pytest.raises(HTTPException):
            validate_direct_wps_write({"status": "draft"}, current)
    with pytest.raises(HTTPException):
        validate_direct_wps_write({"status": "approved"})
    for payload in [{"status": None}, {"approved_by": None}, {"reviewed_by": None}]:
        with pytest.raises(HTTPException):
            validate_direct_wps_write(payload, "approved")


@pytest.mark.parametrize("field", ["id", "user_id", "company_id", "factory_id", "access_level", "converted_to_pqr_id", "approved_by"])
def test_ppqr_update_rejects_server_owned_fields(field):
    db = Mock()
    service = PPQRService(db)
    service.get = Mock(return_value=NS(id=1, status="draft", title="original"))
    service.data_access = Mock()
    with pytest.raises(HTTPException) as exc:
        service.update(db, id=1, ppqr_data={field: 99, "title": "changed"},
                       current_user=NS(id=7), workspace_context=WorkspaceContext(7, WorkspaceType.PERSONAL))
    assert exc.value.status_code == 422
    assert service.get.return_value.title == "original"
    db.commit.assert_not_called()


def test_ppqr_edit_requires_edit_access_and_keeps_module_alias():
    db, user = Mock(), NS(id=7)
    context = WorkspaceContext(7, WorkspaceType.PERSONAL)
    item = NS(id=1, status="draft", module_data={})
    service = PPQRService(db)
    service.get = Mock(return_value=item)
    service.data_access = Mock()
    service.data_access.check_access.side_effect = HTTPException(403, "只读")
    with pytest.raises(HTTPException):
        service.update(db, id=1, ppqr_data={"modules_data": {"field": 12}}, current_user=user, workspace_context=context)
    db.commit.assert_not_called()
    service.data_access.check_access.side_effect = None
    service.update(db, id=1, ppqr_data={"modules_data": {"field": 12}}, current_user=user, workspace_context=context)
    assert item.module_data == {"field": 12}
    service.data_access.check_access.assert_called_with(user, item, "edit", context)

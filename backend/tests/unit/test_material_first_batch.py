"""Regression coverage for material forms, stock boundaries and real ORM responses."""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api import deps
from app.api.v1.endpoints import materials
from app.core.data_access import WorkspaceContext
from app.core.errors import register_exception_handlers
from app.models.material import MaterialTransaction, WeldingMaterial
from app.schemas.material import MaterialCreate, MaterialUpdate
from app.services.material_service import MaterialService


@pytest.fixture
def api(monkeypatch):
    db = MagicMock()
    service = MaterialService(db)
    service.data_access = MagicMock()
    service.data_access.apply_workspace_filter.side_effect = lambda query, *args: query
    monkeypatch.setattr(materials, 'MaterialService', lambda session: service)
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(materials.router, prefix='/materials')
    app.dependency_overrides[deps.get_db] = lambda: db
    app.dependency_overrides[deps.get_current_active_user] = lambda: SimpleNamespace(id=7, username='tester')
    return TestClient(app), service, db


@pytest.mark.parametrize('payload', [{'current_stock': 100}, {'unit': 'L'}, {'material_name': None}, {'unit_price': -1}])
def test_invalid_edit_returns_422_without_serialization_failure_or_writes(api, payload):
    client, service, db = api
    response = client.put('/materials/42?workspace_type=personal', json=payload)
    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'VALIDATION_ERROR'
    db.commit.assert_not_called()


@pytest.mark.parametrize('field,value', [('current_stock', -1), ('current_stock', float('inf')),
                                        ('unit_price', float('nan')), ('min_stock_level', -2),
                                        ('material_code', '  '), ('material_name', '')])
def test_invalid_create_data_is_rejected(field, value):
    payload = dict(material_code='M1', material_name='wire', material_type='wire')
    payload[field] = value
    with pytest.raises(ValidationError):
        MaterialCreate(**payload)


def test_optional_metadata_can_be_cleared_without_touching_stock(api):
    _, service, db = api
    material = WeldingMaterial(id=42, current_stock=12, unit='kg', notes='old', material_code='M1')
    db.query.return_value.filter.return_value.first.return_value = material
    service.update_material(42, SimpleNamespace(id=7), MaterialUpdate(notes=None).model_dump(exclude_unset=True), WorkspaceContext(7))
    assert material.notes is None
    assert material.current_stock == 12 and material.unit == 'kg'


def test_service_also_rejects_direct_stock_overwrite(api):
    _, service, db = api
    material = WeldingMaterial(id=42, current_stock=12, unit='kg')
    db.query.return_value.filter.return_value.first.return_value = material
    with pytest.raises(HTTPException) as error:
        service.update_material(42, SimpleNamespace(id=7), {'current_stock': 99}, WorkspaceContext(7))
    assert error.value.status_code == 422
    assert material.current_stock == 12
    db.commit.assert_not_called()


@pytest.mark.parametrize('action', ['stock_in', 'stock_out'])
@pytest.mark.parametrize('quantity', [0, -1, float('nan'), float('inf')])
def test_invalid_stock_transactions_never_write(api, action, quantity):
    _, service, db = api
    with pytest.raises(HTTPException) as error:
        getattr(service, action)(SimpleNamespace(id=7), 42, quantity, WorkspaceContext(7))
    assert error.value.status_code == 422
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_transaction_endpoint_serializes_real_orm_rows_and_zero_amount(api):
    client, service, db = api
    service.get_material_by_id = MagicMock()
    now = datetime.now()
    row = MaterialTransaction(id=1, material_id=42, user_id=7, workspace_type='personal',
                              company_id=None, factory_id=None, transaction_type='out',
                              transaction_number='OUT-1', transaction_date=now,
                              quantity=-3, unit='kg', stock_before=15, stock_after=12,
                              total_price=0, currency='USD', is_active=True, is_cancelled=False,
                              created_at=now, updated_at=now, created_by=7)
    query = db.query.return_value.filter.return_value
    query.filter.return_value = query
    query.count.return_value = 1
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [row]
    response = client.get('/materials/transactions?workspace_type=personal&material_id=42&skip=0&limit=1')
    assert response.status_code == 200
    data = response.json()['data']
    assert data['total'] == 1
    assert data['items'][0]['quantity'] == -3
    assert data['items'][0]['total_price'] == data['items'][0]['total_amount'] == 0
    assert data['items'][0]['currency'] == 'USD'


def test_denied_transaction_read_stays_403(api):
    client, service, _ = api
    service.get_material_by_id = MagicMock(side_effect=HTTPException(403, '权限不足'))
    response = client.get('/materials/transactions?workspace_type=personal&material_id=42')
    assert response.status_code == 403

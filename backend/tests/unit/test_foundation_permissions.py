"""T01/T03: exercise real permission checks, including ignored return-value callers."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.models.company import Company, CompanyEmployee, CompanyRole
from app.models.production import ProductionPlan
from app.models.quality import QualityStandard
from app.models.business_extensions import EmployeePerformance, ReportTemplate
from app.services.workspace_entity_service import WorkspaceEntityService

MODELS = [ProductionPlan, QualityStandard, EmployeePerformance, ReportTemplate]


def setup_access(model, *, factory_id=None, role=None, owner=99):
    item = model(id=1, user_id=owner, workspace_type="enterprise", company_id=5, factory_id=factory_id, is_active=True)
    employee = SimpleNamespace(user_id=2, company_id=5, factory_id=10, role="employee",
                               company_role_id=7 if role else None, data_access_scope="factory")
    db = MagicMock()
    def query(cls):
        q = MagicMock()
        q.filter.return_value = q
        q.with_for_update.return_value = q
        q.first.return_value = {Company: SimpleNamespace(owner_id=1), CompanyEmployee: employee,
                               CompanyRole: role, model: item}.get(cls)
        return q
    db.query.side_effect = query
    return db, item


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("action", ["edit", "EDIT", " delete ", "DELETE", "share"])
def test_employee_cannot_mutate_another_creators_record(model, action):
    db, item = setup_access(model)
    with pytest.raises(HTTPException) as exc:
        DataAccessMiddleware(db).check_access(SimpleNamespace(id=2), item, action)
    assert exc.value.status_code == 403
    db.commit.assert_not_called()


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("factory_id,allowed", [(None, True), (10, True), (20, False)])
def test_business_models_have_access_contract_for_regular_members(model, factory_id, allowed):
    db, item = setup_access(model, factory_id=factory_id)
    access = DataAccessMiddleware(db)
    assert item.access_level == ("factory" if factory_id else "company")
    if allowed:
        assert access.check_access(SimpleNamespace(id=2), item, "VIEW")
    else:
        with pytest.raises(HTTPException) as exc:
            access.check_access(SimpleNamespace(id=2), item, "VIEW")
        assert exc.value.status_code == 403


@pytest.mark.parametrize("model", MODELS)
def test_generic_update_and_delete_stop_before_mutation(model):
    db, item = setup_access(model)
    service = WorkspaceEntityService(db, model)
    context = WorkspaceContext(2, "enterprise", 5)
    for call in [lambda: service.update_item(1, {"is_active": False}, SimpleNamespace(id=2), context),
                 lambda: service.delete_item(1, SimpleNamespace(id=2), context)]:
        with pytest.raises(HTTPException) as exc:
            call()
        assert exc.value.status_code == 403
        assert item.is_active is True
    db.commit.assert_not_called()


@pytest.mark.parametrize("action", ["EDIT", "delete"])
def test_creator_can_edit_own_enterprise_record(action):
    db, item = setup_access(ProductionPlan, owner=2)
    assert DataAccessMiddleware(db).check_access(SimpleNamespace(id=2), item, action)


@pytest.mark.parametrize("action", ["unknown", "", None])
def test_invalid_action_is_denied_even_to_owner(action):
    item = ProductionPlan(user_id=2, workspace_type="personal")
    with pytest.raises(HTTPException) as exc:
        DataAccessMiddleware(MagicMock()).check_access(SimpleNamespace(id=2), item, action)
    assert exc.value.status_code == 403

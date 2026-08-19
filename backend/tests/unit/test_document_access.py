"""Authorization tests for document IDOR on export and by-id access."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.data_access import DataAccessAction, DataAccessMiddleware
from app.core.document_access import require_document_access
from app.models.company import Company, CompanyEmployee


def _query_returning(first_value):
    query = MagicMock()
    query.filter.return_value.first.return_value = first_value
    return query


class TestPersonalDocumentAccess:
    def test_owner_can_view(self):
        user = SimpleNamespace(id=1)
        resource = SimpleNamespace(workspace_type="personal", user_id=1)
        middleware = DataAccessMiddleware(MagicMock())

        assert middleware.check_access(user, resource, DataAccessAction.VIEW) is True

    def test_other_user_is_forbidden(self):
        user = SimpleNamespace(id=2)
        resource = SimpleNamespace(workspace_type="personal", user_id=1)
        middleware = DataAccessMiddleware(MagicMock())

        with pytest.raises(HTTPException) as exc:
            middleware.check_access(user, resource, DataAccessAction.VIEW)

        assert exc.value.status_code == 403


class TestEnterpriseDocumentAccess:
    def test_company_owner_can_view(self):
        user = SimpleNamespace(id=10)
        resource = SimpleNamespace(
            workspace_type="enterprise",
            company_id=5,
            user_id=99,
            access_level="company",
        )
        db = MagicMock()
        db.query.side_effect = lambda model: _query_returning(
            SimpleNamespace(owner_id=10) if model is Company else None
        )
        middleware = DataAccessMiddleware(db)

        assert middleware.check_access(user, resource, DataAccessAction.VIEW) is True

    def test_cross_tenant_member_is_forbidden(self):
        user = SimpleNamespace(id=3)
        resource = SimpleNamespace(
            workspace_type="enterprise",
            company_id=5,
            user_id=1,
            access_level="company",
        )
        db = MagicMock()

        def query(model):
            if model is Company:
                return _query_returning(SimpleNamespace(owner_id=1))
            if model is CompanyEmployee:
                return _query_returning(None)
            return _query_returning(None)

        db.query.side_effect = query
        middleware = DataAccessMiddleware(db)

        with pytest.raises(HTTPException) as exc:
            middleware.check_access(user, resource, DataAccessAction.VIEW)

        assert exc.value.status_code == 403

    def test_role_without_module_permission_is_forbidden(self):
        user = SimpleNamespace(id=4)
        resource = SimpleNamespace(
            workspace_type="enterprise",
            company_id=5,
            user_id=1,
            access_level="company",
        )
        employee = SimpleNamespace(
            user_id=4,
            company_id=5,
            role="member",
            company_role_id=8,
            factory_id=1,
            data_access_scope="factory",
        )
        role = SimpleNamespace(
            id=8,
            is_active=True,
            permissions={"wps_management": {"view": False}},
        )
        db = MagicMock()

        def query(model):
            name = getattr(model, "__name__", "")
            if model is Company or name == "Company":
                return _query_returning(SimpleNamespace(owner_id=1))
            if model is CompanyEmployee or name == "CompanyEmployee":
                return _query_returning(employee)
            return _query_returning(role)

        db.query.side_effect = query
        middleware = DataAccessMiddleware(db)

        with pytest.raises(HTTPException) as exc:
            middleware.check_access(user, resource, DataAccessAction.VIEW)

        assert exc.value.status_code == 403


class TestRequireDocumentAccess:
    def test_missing_document_returns_404(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        user = SimpleNamespace(id=1)
        model = MagicMock()
        model.id = MagicMock()

        with pytest.raises(HTTPException) as exc:
            require_document_access(db, model, 99, user, "WPS不存在")

        assert exc.value.status_code == 404

    def test_cross_tenant_returns_403(self):
        user = SimpleNamespace(id=2)
        document = SimpleNamespace(workspace_type="personal", user_id=1)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = document
        model = MagicMock()
        model.id = MagicMock()

        with pytest.raises(HTTPException) as exc:
            require_document_access(db, model, 1, user, "WPS不存在")

        assert exc.value.status_code == 403
        assert exc.value.detail != document

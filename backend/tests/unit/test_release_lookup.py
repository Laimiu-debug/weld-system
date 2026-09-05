from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.production_release import sequence_release_detail
from app.models.sequence import WeldSequenceRevision
from app.services.production_release_service import ProductionReleaseService


def test_lookup_checks_sequence_access_before_querying_batch():
    service = ProductionReleaseService(Mock())
    service._get = Mock(side_effect=HTTPException(403, "forbidden"))
    with pytest.raises(HTTPException):
        service.for_sequence("s1", NS(id=7), NS())
    service.db.query.assert_not_called()


def test_no_release_returns_none_without_creating_tasks():
    service = ProductionReleaseService(Mock())
    service._get = Mock()
    service.db.query.return_value.filter.return_value.first.return_value = None
    user, context = NS(id=7), NS()
    assert service.for_sequence("s1", user, context) is None
    service._get.assert_called_once_with(WeldSequenceRevision, "s1", user, context)
    service.db.add.assert_not_called()
    service.db.commit.assert_not_called()


def test_existing_release_uses_permission_checked_detail():
    service = ProductionReleaseService(Mock())
    service._get = Mock()
    service.db.query.return_value.filter.return_value.first.return_value = NS(id="r1")
    service.detail = Mock(return_value={"release": {"id": "r1"}, "tasks": []})
    user, context = NS(id=7), NS()
    assert service.for_sequence("s1", user, context)["release"]["id"] == "r1"
    service.detail.assert_called_once_with("r1", user, context)


def test_lookup_route_resolves_workspace_and_checks_module_permission():
    user, context, db = NS(id=7), NS(), Mock()
    with patch("app.api.v1.endpoints.production_release.resolve_workspace", return_value=context) as resolve, \
         patch("app.api.v1.endpoints.production_release._permission") as permission, \
         patch("app.api.v1.endpoints.production_release.ProductionReleaseService") as service:
        service.return_value.for_sequence.return_value = None
        assert sequence_release_detail("s1", db, user, "enterprise_2") is None
        resolve.assert_called_once_with(db, user, "enterprise_2")
        permission.assert_called_once_with(db, user, context)
        service.return_value.for_sequence.assert_called_once_with("s1", user, context)

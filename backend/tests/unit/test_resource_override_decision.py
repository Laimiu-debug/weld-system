from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.models.production import ProductionTask
from app.models.production_release import ProductionResourceAuthorization, ProductionReleaseBatch
from app.services.production_release_service import ProductionReleaseService


def setup():
    item = ProductionResourceAuthorization(id="a1", production_task_id=1, welder_id=7, equipment_id=8,
        wps_id=9, qualification_status="pending_override", qualification_snapshot={"reasons": ["焊位不符"]})
    task = ProductionTask(id=1, production_release_id="r1", is_active=True, status="pending",
        wps_id=9, assigned_welder_id=2, assigned_equipment_id=3, source_step_snapshot={})
    batch = ProductionReleaseBatch(id="r1", status="released")
    db = Mock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = item
    service = ProductionReleaseService(db)
    service._get = Mock(side_effect=lambda model, *args: {ProductionResourceAuthorization: item, ProductionTask: task, ProductionReleaseBatch: batch}[model])
    service._recheck_execution_resources = Mock()
    return service, item, task, batch


@pytest.mark.parametrize("problem", ["completed", "cancelled", "inactive", "superseded", "old_request", "resource_changed"])
def test_stale_override_cannot_change_assignment(problem):
    service, item, task, batch = setup()
    if problem in {"completed", "cancelled"}: task.status = problem
    if problem == "inactive": task.is_active = False
    if problem == "superseded": batch.status = "superseded"
    if problem == "old_request":
        service.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = NS(id="a2")
    if problem == "resource_changed": service._recheck_execution_resources.side_effect = HTTPException(409, "设备不可用")
    with pytest.raises(HTTPException) as error:
        service.authorize_override("a1", True, NS(id=5), NS())
    assert error.value.status_code == 409
    assert item.qualification_status == "pending_override"
    assert item.authorized_by is None
    assert task.assigned_welder_id == 2
    service.db.commit.assert_not_called()


def test_override_rechecks_requested_resources_and_records_decision():
    service, item, task, _ = setup()
    result = service.authorize_override("a1", True, NS(id=5), NS())
    proposed, authorization, *_ = service._recheck_execution_resources.call_args.args
    assert proposed.assigned_welder_id == 7 and proposed.assigned_equipment_id == 8
    assert authorization.qualification_snapshot == item.qualification_snapshot
    assert task.assigned_welder_id == 7 and task.assigned_equipment_id == 8
    assert result.qualification_status == "authorized" and result.authorized_by == 5
    service.db.commit.assert_called_once()


def test_rejecting_request_does_not_replace_assignment_or_require_available_resources():
    service, item, task, _ = setup()
    service.authorize_override("a1", False, NS(id=5), NS())
    assert item.qualification_status == "rejected"
    assert task.assigned_welder_id == 2
    service._recheck_execution_resources.assert_not_called()

from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.models.production import ProductionTask
from app.services.production_service import ProductionService


def setup(released=True):
    task = ProductionTask(id=1, production_release_id="r1" if released else None,
        status="pending", progress_percentage=0, is_active=True, notes="before")
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = task
    service = ProductionService(db)
    service.data_access = Mock()
    service.get_production_task_by_id = Mock(return_value=task)
    return service, task, NS(id=7), Mock()


@pytest.mark.parametrize("payload", [
    {"status": "completed"}, {"progress_percentage": 100}, {"assigned_welder_id": 7},
    {"assigned_equipment_id": 8}, {"wps_id": 9}, {"quality_inspection_required": False},
    {"production_release_id": ""}, {"source_step_snapshot": {}},
])
def test_general_update_cannot_bypass_release_controls(payload):
    service, task, user, context = setup()
    with pytest.raises(HTTPException) as error:
        service.update_production_task(1, user, {"notes": "after", **payload}, context)
    assert error.value.status_code == 409
    assert task.notes == "before" and task.status == "pending"
    service.db.commit.assert_not_called()


@pytest.mark.parametrize("action", ["progress", "record", "delete"])
def test_other_general_write_paths_reject_released_tasks(action):
    service, task, user, context = setup()
    with pytest.raises(HTTPException) as error:
        if action == "progress":
            service.update_task_progress(1, user, context, 100)
        elif action == "record":
            service.create_production_record(1, user, {"progress_percentage": 100}, context)
        else:
            service.delete_production_task(1, user, context)
    assert error.value.status_code == 409
    assert task.is_active and task.progress_percentage == 0
    service.db.add.assert_not_called()
    service.db.commit.assert_not_called()


def test_released_task_notes_and_unchanged_form_fields_remain_editable():
    service, task, user, context = setup()
    service.update_production_task(1, user, {"notes": "after", "status": "pending"}, context)
    assert task.notes == "after" and task.status == "pending"
    service.db.commit.assert_called_once()


def test_manual_tasks_keep_existing_progress_workflow():
    service, task, user, context = setup(released=False)
    service.update_task_progress(1, user, context, 100)
    assert task.status == "completed" and task.progress_percentage == 100
    service.db.commit.assert_called_once()

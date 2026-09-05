"""Execution must satisfy the released graph and current resource availability."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.models.production import ProductionTask
from app.models.production_release import ProductionExecutionTrace, ProductionQualityNode, ProductionReleaseBatch
from app.models.quality import QualityInspection
from app.models.equipment import Equipment
from app.models.welder import Welder, WelderCertification
from app.models.wps import WPS
from app.services.production_release_service import ProductionReleaseService, evaluate_welder_qualification


def service_for(rows):
    db = Mock()
    def query(model):
        query = Mock()
        query.filter.return_value = query
        query.order_by.return_value = query
        values = rows.get(model, [])
        query.all.return_value = values
        query.first.return_value = values[0] if values else None
        return query
    db.query.side_effect = query
    service = ProductionReleaseService(db)
    service.access = Mock()
    return service


def graph():
    previous = ProductionTask(id=1, production_release_id="r", is_active=True,
        status="completed", quality_inspection_required=True, source_step_snapshot={"step_code": "NDE"})
    task = ProductionTask(id=2, production_release_id="r", is_active=True,
        task_type="quality_closure", status="pending", quality_inspection_required=False,
        source_step_snapshot={"step_code": "CLOSE"})
    batch = ProductionReleaseBatch(id="r", status="released", source_snapshot={"sequence": {
        "steps": [{"step_code": "NDE"}, {"step_code": "CLOSE"}],
        "dependencies": [{"predecessor_code": "NDE", "successor_code": "CLOSE", "is_mandatory": True}]}})
    rows = {ProductionTask: [task, previous], ProductionReleaseBatch: [batch],
        ProductionQualityNode: [ProductionQualityNode(quality_inspection_id=3)],
        QualityInspection: [QualityInspection(id=3, production_task_id=1, inspection_result="pass")]}
    return service_for(rows), rows, task, previous, batch


@pytest.mark.parametrize("problem", ["pending", "missing", "inactive", "failed_quality", "missing_quality", "cancelled", "missing_graph"])
def test_execution_rejects_unfinished_or_unverified_predecessors(problem):
    service, rows, task, previous, batch = graph()
    if problem == "pending": previous.status = "in_progress"
    if problem == "missing": rows[ProductionTask].remove(previous)
    if problem == "inactive": previous.is_active = False
    if problem == "failed_quality": rows[QualityInspection][0].inspection_result = "fail"
    if problem == "missing_quality": rows[ProductionQualityNode].clear()
    if problem == "cancelled": batch.status = "cancelled"
    if problem == "missing_graph": batch.source_snapshot = {}
    with pytest.raises(HTTPException) as error:
        service.record_execution(task.id, {"idempotency_key": "attempt", "status": "completed"}, NS(id=7), NS())
    assert error.value.status_code == 409
    assert task.status == "pending"
    service.db.add.assert_not_called()
    service.db.commit.assert_not_called()


def test_completed_predecessor_with_passed_inspection_allows_execution():
    service, rows, task, previous, batch = graph()
    batch.user_id, batch.workspace_type, batch.access_level = 7, "personal", "private"
    task.source_sequence_revision_id, task.source_sequence_step_id = "s", "close"
    task.source_sequence_frozen_hash = "frozen"
    trace, created = service.record_execution(2, {"idempotency_key": "attempt", "status": "completed"}, NS(id=7), NS())
    assert created and trace.status == "completed"
    assert task.status == "completed" and task.progress_percentage == 100
    service.db.commit.assert_called_once()


def test_repeated_execution_returns_original_without_mutation():
    service, rows, task, previous, batch = graph()
    original = ProductionExecutionTrace(id="original")
    rows[ProductionExecutionTrace] = [original]
    batch.status = "cancelled"
    assert service.record_execution(2, {"idempotency_key": "attempt"}, NS(id=7), NS()) == (original, False)
    service.db.commit.assert_not_called()


def test_quality_task_cannot_complete_using_only_client_supplied_pass():
    service, rows, task, previous, batch = graph()
    task.quality_inspection_required = True
    rows[QualityInspection][0].inspection_result = "pending"
    batch.source_snapshot["sequence"]["dependencies"] = []
    with pytest.raises(HTTPException, match="尚未合格"):
        service.record_execution(2, {"idempotency_key": "attempt", "status": "completed",
            "quality_snapshot": {"result": "pass"}}, NS(id=7), NS())
    service.db.commit.assert_not_called()


def resources():
    wps = WPS(id=9, status="approved", wps_number="W9", welding_process="GTAW")
    welder = Welder(id=7, is_active=True, status="active", qualified_processes="GTAW", qualified_positions="2G")
    cert = WelderCertification(id=4, is_active=True, status="valid", expiry_date=date.today()+timedelta(days=1), qualified_process="GTAW", qualified_position="2G")
    equipment = Equipment(id=8, is_active=True, status="operational", calibration_due_date=date.today())
    task = ProductionTask(wps_id=9, assigned_welder_id=7, assigned_equipment_id=8,
        source_step_snapshot={"process_parameters": {"requirement": {"weld_position": "2G"}}})
    auth = NS(wps_id=9, qualification_status="qualified", qualification_snapshot=evaluate_welder_qualification(welder, [cert], wps, "2G"))
    rows = {WPS: [wps], Welder: [welder], Equipment: [equipment], WelderCertification: [cert]}
    return service_for(rows), rows, task, auth


@pytest.mark.parametrize("problem", ["expired_cert", "revoked_cert", "inactive_welder", "equipment_maintenance", "equipment_expired", "wps_obsolete", "wps_changed"])
def test_current_resource_changes_block_old_qualification(problem):
    service, rows, task, auth = resources()
    if problem == "expired_cert": rows[WelderCertification][0].expiry_date = date.today()-timedelta(days=1)
    if problem == "revoked_cert": rows[WelderCertification][0].is_active = False
    if problem == "inactive_welder": rows[Welder][0].is_active = False
    if problem == "equipment_maintenance": rows[Equipment][0].status = "maintenance"
    if problem == "equipment_expired": rows[Equipment][0].calibration_due_date = date.today()-timedelta(days=1)
    if problem == "wps_obsolete": rows[WPS][0].status = "obsolete"
    if problem == "wps_changed": auth.wps_id = 10
    with pytest.raises(HTTPException) as error:
        service._recheck_execution_resources(task, auth, NS(id=7), NS())
    assert error.value.status_code == 409


def test_valid_resources_and_calibration_due_today_are_allowed():
    service, rows, task, auth = resources()
    service._recheck_execution_resources(task, auth, NS(id=7), NS())


def test_deleted_certificates_cannot_fall_back_to_stale_profile_scope():
    service, rows, task, auth = resources()
    rows[WelderCertification].clear()
    with pytest.raises(HTTPException, match="证书记录已不存在"):
        service._recheck_execution_resources(task, auth, NS(id=7), NS())


def test_override_only_covers_unchanged_reviewed_exception():
    service, rows, task, auth = resources()
    rows[WelderCertification][0].qualified_position = "1G"
    auth.qualification_status = "authorized"
    auth.authorized_by, auth.authorized_at = 5, datetime.utcnow()
    auth.qualification_snapshot = evaluate_welder_qualification(rows[Welder][0], rows[WelderCertification], rows[WPS][0], "2G")
    service._recheck_execution_resources(task, auth, NS(id=7), NS())
    rows[WelderCertification][0].expiry_date = date.today()-timedelta(days=1)
    with pytest.raises(HTTPException):
        service._recheck_execution_resources(task, auth, NS(id=7), NS())

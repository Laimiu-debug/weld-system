"""Real local database: generation, release, execution and approved changes."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
from copy import deepcopy
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from test_foundation_integrity import sessions, db, user
from test_ai_input_integrity import drawing
from app.models.engineering import Part, WeldJoint, WeldRequirement
from app.models.matching import WPSMatchRun, WPSMatchCandidate, WPSMatchFreeze
from app.models.qualification import WPSPQRSupportLink
from app.services.qualification_service import _record_snapshot
from app.models.wps import WPS
from app.models.pqr import PQR
from app.models.welder import Welder, WelderCertification
from app.models.user import User
from app.models.production import ProductionTask
from app.models.production_release import (
    ProductionSequenceChangeRequest,
    ProductionReleaseBatch,
    ProductionExecutionTrace,
)
from app.models.quality import QualityInspection
from app.models.consumable import (
    ConsumableRuleSet,
    ConsumableQuotaRun,
    ConsumableIssueList,
)
from app.services.sequence_service import WeldSequenceService
from app.services.production_release_service import ProductionReleaseService
from app.models.approval import ApprovalWorkflowDefinition, ApprovalInstance
from app.core.security import create_access_token
from app.api import deps
from app.api.v1.endpoints.production_release import router
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LOCAL_DB_TESTS") != "1", reason="local PostgreSQL opt-in"
)


def seed_workflow(db, tmp_path):
    owner, ctx, revision, _ = drawing(db, tmp_path)
    scope = {
        "user_id": owner.id,
        "workspace_type": "personal",
        "created_by": owner.id,
        "access_level": "private",
    }
    part = Part(revision_id=revision.id, name="Plate", **scope)
    db.add(part)
    db.flush()
    joint = WeldJoint(
        revision_id=revision.id,
        weld_number="W1",
        part_a_id=part.id,
        part_b_id=part.id,
        length_mm=1200,
        **scope,
    )
    db.add(joint)
    db.flush()
    db.add(
        WeldRequirement(
            revision_id=revision.id, weld_joint_id=joint.id, nde_methods=["RT"], **scope
        )
    )
    wps = WPS(
        wps_number=uuid4().hex,
        title="QA",
        welding_process="GTAW",
        current_range="90-130 A",
        status="approved",
        **scope,
    )
    pqr = PQR(pqr_number=uuid4().hex, title="QA", status="approved", **scope)
    db.add_all([wps, pqr])
    db.flush()
    link = WPSPQRSupportLink(
        wps_id=wps.id,
        pqr_id=pqr.id,
        wps_version_key="1",
        pqr_version_key="1",
        wps_snapshot_hash="x",
        pqr_snapshot_hash="x",
        **scope,
    )
    run = WPSMatchRun(
        revision_id=revision.id,
        status="approved",
        source_data_version=revision.data_version,
        rule_pack_version="1",
        capability_snapshot_hash="x",
        **scope,
    )
    db.add_all([link, run])
    db.flush()
    candidate = WPSMatchCandidate(
        run_id=run.id,
        weld_joint_id=joint.id,
        support_link_id=link.id,
        wps_id=wps.id,
        pqr_id=pqr.id,
        rank=1,
        decision="eligible",
        **scope,
    )
    db.add(candidate)
    db.flush()
    freeze = WPSMatchFreeze(
        run_id=run.id,
        candidate_id=candidate.id,
        revision_id=revision.id,
        weld_joint_id=joint.id,
        weld_requirement_hash="x",
        wps_snapshot_hash="x",
        pqr_snapshot_hash="x",
        rule_snapshot_hash="x",
        frozen_snapshot={
            "wps": _record_snapshot(wps),
            "pqr": _record_snapshot(pqr),
        },
        **scope,
    )
    welder = Welder(
        welder_code=uuid4().hex,
        full_name="QA",
        is_active=True,
        status="active",
        **scope,
    )
    db.add_all([freeze, welder])
    db.flush()
    cert = WelderCertification(
        certification_type="GTAW",
        user_id=owner.id,
        created_by=owner.id,
        welder_id=welder.id,
        certification_number=uuid4().hex,
        is_active=True,
        status="valid",
        expiry_date=date.today() + timedelta(days=30),
        qualified_process="GTAW",
    )
    db.add(cert)
    revision.status = "approved"
    db.commit()
    seq = WeldSequenceService(db)
    sequence = seq.generate(
        revision.id, {"segmented": True, "skip_weld": True}, None, None, owner, ctx
    )
    seq.submit(sequence.id, None, "normal", None, owner, ctx)
    return owner, ctx, revision, sequence, welder, cert


def test_full_release_execution_and_change_preserves_old_history(db, tmp_path):
    owner, ctx, revision, sequence, welder, cert = seed_workflow(db, tmp_path)
    svc = ProductionReleaseService(db)
    batch, created = svc.release(sequence.id, None, owner, ctx)
    assert created
    detail = svc.detail(batch.id, owner, ctx)
    assert len([t for t in detail["tasks"] if t["task_type"] == "welding"]) == 3
    tasks = sorted(
        detail["tasks"], key=lambda t: t["source_step_snapshot"]["order_index"]
    )
    for task in tasks:
        if task["task_type"] == "welding":
            svc.assign(task["id"], welder.id, None, None, owner, ctx)
        if task["quality_inspection_required"]:
            with pytest.raises(HTTPException):
                svc.record_execution(
                    task["id"],
                    {"idempotency_key": "attempt-early", "status": "completed"},
                    owner,
                    ctx,
                )
            inspection = (
                db.query(QualityInspection)
                .filter_by(production_task_id=task["id"])
                .one()
            )
            inspection.inspection_result = "pass"
            db.commit()
        trace, created = svc.record_execution(
            task["id"],
            {
                "idempotency_key": "record-0001",
                "status": "completed",
                "actual_parameters": {"current": 100}
                if task["task_type"] == "welding"
                else {},
            },
            owner,
            ctx,
        )
        assert created
        repeated, created = svc.record_execution(
            task["id"],
            {"idempotency_key": "record-0001", "status": "completed"},
            owner,
            ctx,
        )
        assert not created and trace.id == repeated.id
    frozen = deepcopy(batch.source_snapshot)
    with pytest.raises(HTTPException):
        svc.assign(
            next(t["id"] for t in tasks if t["task_type"] == "welding"),
            welder.id,
            None,
            None,
            owner,
            ctx,
        )
    old_history = [
        r.id
        for r in db.query(ProductionExecutionTrace)
        .filter_by(production_release_id=batch.id)
        .all()
    ]
    change = svc.request_change(batch.id, "调整分段施工顺序", {}, None, owner, ctx)
    assert change.status == "approved"
    with pytest.raises(HTTPException):
        svc.request_change(batch.id, "重复变更申请测试", {}, None, owner, ctx)
    with pytest.raises(HTTPException):
        WeldSequenceService(db).generate(revision.id, {}, None, None, owner, ctx)
    child = WeldSequenceService(db).generate(
        revision.id,
        {"segmented": True},
        None,
        None,
        owner,
        ctx,
        parent_id=sequence.id,
        change_request_id=change.id,
    )
    assert (
        change.status == "approved" and change.proposed_sequence_revision_id == child.id
    )
    with pytest.raises(HTTPException):
        svc.apply_change(change.id, child.id, owner, ctx)
    WeldSequenceService(db).submit(child.id, None, "normal", None, owner, ctx)
    with pytest.raises(HTTPException):
        svc.release(child.id, None, owner, ctx)
    svc.apply_change(change.id, child.id, owner, ctx)
    assert change.status == "applied" and batch.status == "superseded"
    assert batch.source_snapshot == frozen
    assert [
        r.id
        for r in db.query(ProductionExecutionTrace)
        .filter_by(production_release_id=batch.id)
        .all()
    ] == old_history
    svc.apply_change(change.id, child.id, owner, ctx)
    new_batch, created = svc.release(child.id, None, owner, ctx)
    assert created and new_batch.id != batch.id
    assert all(
        t["status"] == "pending" for t in svc.detail(new_batch.id, owner, ctx)["tasks"]
    )
    stranger = user(db)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        svc.detail(
            batch.id,
            stranger,
            type(ctx)(user_id=stranger.id, workspace_type="personal"),
        )
    assert exc.value.status_code == 403


def test_execution_rechecks_expired_certificate_and_dependency(db, tmp_path):
    owner, ctx, revision, sequence, welder, cert = seed_workflow(db, tmp_path)
    svc = ProductionReleaseService(db)
    batch, _ = svc.release(sequence.id, None, owner, ctx)
    tasks = sorted(
        svc.detail(batch.id, owner, ctx)["tasks"],
        key=lambda t: t["source_step_snapshot"]["order_index"],
    )
    weld = next(t for t in tasks if t["task_type"] == "welding")
    svc.assign(weld["id"], welder.id, None, None, owner, ctx)
    with pytest.raises(HTTPException, match="前置"):
        svc.record_execution(
            weld["id"],
            {"idempotency_key": "early-weld", "status": "completed"},
            owner,
            ctx,
        )
    for task in tasks:
        if task["id"] == weld["id"]:
            break
        svc.record_execution(
            task["id"],
            {"idempotency_key": "prerequisite", "status": "completed"},
            owner,
            ctx,
        )
    cert.expiry_date = date.today() - timedelta(days=1)
    db.commit()
    with pytest.raises(HTTPException):
        svc.record_execution(
            weld["id"],
            {"idempotency_key": "expired-cert", "status": "completed"},
            owner,
            ctx,
        )
    assert db.get(ProductionTask, weld["id"]).status == "pending"


def test_release_links_only_approved_matching_issue_list(db, tmp_path):
    owner, ctx, revision, sequence, _, _ = seed_workflow(db, tmp_path)
    scope = {"user_id": owner.id, "workspace_type": "personal", "created_by": owner.id}
    rule = ConsumableRuleSet(
        rule_code=uuid4().hex,
        name="QA",
        formula_version="1",
        snapshot_hash="x",
        **scope,
    )
    db.add(rule)
    db.flush()
    quota = ConsumableQuotaRun(
        product_revision_id=revision.id,
        sequence_revision_id=sequence.id,
        rule_set_id=rule.id,
        input_version_hash="x",
        idempotency_key=uuid4().hex,
        formula_version="1",
        **scope,
    )
    db.add(quota)
    db.flush()
    issue = ConsumableIssueList(
        quota_run_id=quota.id,
        product_revision_id=revision.id,
        sequence_revision_id=sequence.id,
        document_number=uuid4().hex,
        snapshot_hash="x",
        status="suggested",
        **scope,
    )
    db.add(issue)
    db.commit()
    svc = ProductionReleaseService(db)
    assert svc.issue_lists(sequence.id, owner, ctx) == []
    with pytest.raises(HTTPException):
        svc.release(sequence.id, issue.id, owner, ctx)
    issue.status = "approved"
    db.commit()
    assert svc.issue_lists(sequence.id, owner, ctx)[0]["id"] == issue.id
    batch, _ = svc.release(sequence.id, issue.id, owner, ctx)
    assert all(
        t["consumable_issue_list_id"] == issue.id
        for t in svc.detail(batch.id, owner, ctx)["tasks"]
    )
    with pytest.raises(HTTPException):
        svc.release(sequence.id, None, owner, ctx)


def test_workflow_approval_is_synchronized_before_recalculation(db, tmp_path):
    owner, ctx, revision, sequence, _, _ = seed_workflow(db, tmp_path)
    svc = ProductionReleaseService(db)
    batch, _ = svc.release(sequence.id, None, owner, ctx)
    change = svc.request_change(batch.id, "工作流同步验收变更", {}, None, owner, ctx)
    workflow = ApprovalWorkflowDefinition(
        name="QA", code=uuid4().hex, document_type="production", steps=[]
    )
    db.add(workflow)
    db.flush()
    instance = ApprovalInstance(
        workflow_id=workflow.id,
        document_type="production",
        document_ref=change.id,
        version_key=change.id + ":v1",
        version_snapshot={},
        snapshot_hash="x",
        status="pending",
        workspace_type="personal",
        submitter_id=owner.id,
    )
    db.add(instance)
    db.flush()
    change.approval_instance_id, change.status = instance.id, "pending"
    db.commit()
    service = WeldSequenceService(db)
    with pytest.raises(HTTPException):
        service.generate(
            revision.id,
            {},
            None,
            None,
            owner,
            ctx,
            parent_id=sequence.id,
            change_request_id=change.id,
        )
    instance.status = "approved"
    instance.final_approver_id = owner.id
    db.commit()
    child = service.generate(
        revision.id,
        {},
        None,
        None,
        owner,
        ctx,
        parent_id=sequence.id,
        change_request_id=change.id,
    )
    assert (
        change.status == "approved" and change.proposed_sequence_revision_id == child.id
    )
    assert batch.status == "released"
    service.submit(child.id, None, "normal", None, owner, ctx)
    svc.apply_change(change.id, child.id, owner, ctx)
    first = min(
        svc.detail(batch.id, owner, ctx)["tasks"],
        key=lambda t: t["source_step_snapshot"]["order_index"],
    )
    assert first["status"] == "pending"
    with pytest.raises(HTTPException, match="发布批次"):
        svc.record_execution(
            first["id"],
            {"idempotency_key": "old-batch-execution", "status": "completed"},
            owner,
            ctx,
        )


def test_authenticated_http_release_detail_and_cross_account_denial(db, tmp_path):
    owner, ctx, revision, sequence, _, _ = seed_workflow(db, tmp_path)
    stranger = user(db)
    db.commit()
    app = FastAPI()
    app.include_router(router, prefix="/production-release")
    app.dependency_overrides[deps.get_db] = lambda: db
    headers = {
        "Authorization": "Bearer " + create_access_token(owner.id, timedelta(minutes=1))
    }
    with TestClient(app) as client:
        url = f"/production-release/sequences/{sequence.id}/release"
        assert client.get(url).status_code in {401, 403}
        response = client.post(url, json={}, headers=headers)
        assert response.status_code == 201
        response = client.get(url, headers=headers)
        assert response.status_code == 200 and response.json()["tasks"]
        assert {
            "change_requests",
            "executions",
            "quality_nodes",
            "usage_events",
        } <= response.json().keys()
        denied = client.get(
            url,
            headers={
                "Authorization": "Bearer "
                + create_access_token(stranger.id, timedelta(minutes=1))
            },
        )
        assert denied.status_code == 403
        assert (
            client.get(
                f"/production-release/sequences/{sequence.id}/issue-lists",
                headers=headers,
            ).status_code
            == 200
        )


def test_concurrent_execution_uses_one_trace(db, sessions, tmp_path):
    owner, ctx, _, sequence, _, _ = seed_workflow(db, tmp_path)
    svc = ProductionReleaseService(db)
    batch, _ = svc.release(sequence.id, None, owner, ctx)
    task = min(
        svc.detail(batch.id, owner, ctx)["tasks"],
        key=lambda t: t["source_step_snapshot"]["order_index"],
    )
    owner_id, task_id = owner.id, task["id"]
    db.commit()
    barrier = Barrier(2)

    def execute():
        with sessions() as session:
            actor = session.get(User, owner_id)
            barrier.wait(timeout=10)
            trace, created = ProductionReleaseService(session).record_execution(
                task_id,
                {"idempotency_key": "concurrent-execution", "status": "completed"},
                actor,
                ctx,
            )
            return trace.id, created

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(execute) for _ in range(2)]
        results = [f.result(timeout=20) for f in futures]
    assert sorted(created for _, created in results) == [False, True]
    assert len({trace_id for trace_id, _ in results}) == 1
    assert (
        db.query(ProductionExecutionTrace).filter_by(production_task_id=task_id).count()
        == 1
    )


def test_frozen_parameters_and_repair_records_gate_completion(db, tmp_path):
    owner, ctx, revision, sequence, welder, cert = seed_workflow(db, tmp_path)
    svc = ProductionReleaseService(db)
    batch, _ = svc.release(sequence.id, None, owner, ctx)
    tasks = sorted(
        svc.detail(batch.id, owner, ctx)["tasks"],
        key=lambda t: t["source_step_snapshot"]["order_index"],
    )
    for task in tasks:
        if task["task_type"] != "welding":
            svc.record_execution(
                task["id"],
                {"idempotency_key": "setup", "status": "completed"},
                owner,
                ctx,
            )
            continue
        svc.assign(task["id"], welder.id, None, None, owner, ctx)
        # Changing today's WPS cannot widen the released range.
        db.get(WPS, task["wps_id"]).current_range = "1-999 A"
        db.commit()
        for values in ({}, {"current": 200}):
            with pytest.raises(HTTPException, match="执行条件"):
                svc.record_execution(
                    task["id"],
                    {
                        "idempotency_key": "invalid",
                        "status": "completed",
                        "actual_parameters": values,
                    },
                    owner,
                    ctx,
                )
            db.rollback()
        trace, _ = svc.record_execution(
            task["id"],
            {"idempotency_key": "observation", "actual_parameters": {"current": 200}},
            owner,
            ctx,
        )
        assert not trace.quality_snapshot["parameter_validation"]["passed"]
        inspection = QualityInspection(
            owner_id=owner.id,
            inspection_number=str(uuid4()),
            production_task_id=task["id"],
            inspection_result="pass",
            repair_required=True,
        )
        db.add(inspection)
        db.commit()
        with pytest.raises(HTTPException, match="返修未闭合"):
            svc.record_execution(
                task["id"],
                {
                    "idempotency_key": "repair-open",
                    "status": "completed",
                    "actual_parameters": {"current": 100},
                    "repair_snapshot": {"closed": True},
                },
                owner,
                ctx,
            )
        db.rollback()
        from app.services.quality_service import QualityService

        QualityService(db).update_quality_inspection(
            inspection.id,
            owner,
            {
                "repair_description": "按批准工艺完成返修",
                "reinspection_date": date.today(),
                "reinspection_result": "pass",
                "reinspection_notes": "复验合格",
                "reinspection_inspector_id": 999999,
            },
            ctx,
        )
        db.refresh(inspection)
        assert inspection.reinspection_inspector_id == owner.id
        trace, _ = svc.record_execution(
            task["id"],
            {
                "idempotency_key": "valid",
                "status": "completed",
                "actual_parameters": {"current": 100},
            },
            owner,
            ctx,
        )
        assert trace.quality_snapshot["parameter_validation"]["passed"]
        assert trace.repair_snapshot["inspections"][0]["closed"]
        break

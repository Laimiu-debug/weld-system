"""SQ16–21 regression checks against an isolated PostgreSQL schema."""
import os
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException

from test_foundation_integrity import sessions, db, user
from test_sequence_workflow import seed_workflow
from app.models.engineering import Part, WeldJoint, WeldRequirement
from app.models.welder import Welder, WelderCertification
from app.models.quality import QualityInspection
from app.models.matching import WPSMatchFreeze
from app.models.qualification import QualificationRulePack
from app.models.production import ProductionTask
from app.models.production_release import ProductionResourceAuthorization
from app.models.wps import WPS
from app.models.pqr import PQR
from app.services.engineering_service import EngineeringService
from app.services.production_service import ProductionService
from app.services.production_release_service import ProductionReleaseService
from app.services.sequence_service import WeldSequenceService
from app.services.sequence_source_service import source_impact
from app.services.sequence_delivery_service import delivery_package

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LOCAL_DB_TESTS") != "1", reason="local PostgreSQL opt-in"
)


@pytest.mark.parametrize("released", [True, False])
@pytest.mark.parametrize("kind", ["drawing", "wps", "pqr", "rule_pack", "match_freeze"])
def test_source_changes_block_new_release_and_preserve_delivery(
    db, tmp_path, kind, released
):
    owner, ctx, revision, sequence, *_ = seed_workflow(db, tmp_path)
    if kind == "rule_pack":
        pack = QualificationRulePack(
            code=uuid4().hex,
            name="QA",
            standard_code="QA",
            edition="1",
            version="1",
            status="published",
        )
        db.add(pack)
        db.flush()
        freeze = db.query(WPSMatchFreeze).filter_by(revision_id=revision.id).one()
        freeze.frozen_snapshot = {
            **freeze.frozen_snapshot,
            "rule": {"rule_pack_id": pack.id, "rule_pack_version": "1"},
        }
        db.commit()
        seq_service = WeldSequenceService(db)
        sequence = seq_service.generate(revision.id, {}, None, None, owner, ctx)
        seq_service.submit(sequence.id, None, "normal", None, owner, ctx)
    assert not source_impact(db, sequence)["stale"]
    service = ProductionReleaseService(db)
    batch = service.release(sequence.id, None, owner, ctx)[0] if released else None
    original = deepcopy(batch.source_snapshot) if batch else None
    frozen = sequence.source_match_snapshot[0]["snapshot"]
    if kind == "drawing":
        revision.data_version += 1
    elif kind == "wps":
        db.get(WPS, frozen["wps"]["id"]).current_range = "200-250 A"
    elif kind == "pqr":
        db.get(PQR, frozen["pqr"]["id"]).title = "Changed"
    elif kind == "rule_pack":
        pack.rules = [{"changed": True}]
    else:
        freeze = db.query(WPSMatchFreeze).filter_by(revision_id=revision.id).one()
        freeze.frozen_snapshot = {**freeze.frozen_snapshot, "changed": True}
    db.commit()
    impact = source_impact(db, sequence)
    assert kind in {item["source_type"] for item in impact["issues"]}
    assert impact["affected_joint_ids"] == [
        sequence.source_match_snapshot[0]["joint_id"]
    ]
    assert not WeldSequenceService(db).production_release(revision.id, owner, ctx)[
        "eligible"
    ]
    if not released:
        with pytest.raises(HTTPException) as error:
            service.release(sequence.id, None, owner, ctx)
        assert error.value.status_code == 409
        return
    package = delivery_package(db, sequence.id, owner, ctx)
    assert package["source_impact"]["stale"]
    assert package["frozen_sequence"] == original["sequence"]
    assert package["drawing"] == original["drawing"]
    assert batch.source_snapshot == original


def test_delivery_requires_release_and_workspace_access(db, tmp_path):
    owner, ctx, revision, sequence, *_ = seed_workflow(db, tmp_path)
    with pytest.raises(HTTPException) as error:
        delivery_package(db, sequence.id, owner, ctx)
    assert error.value.status_code == 409
    ProductionReleaseService(db).release(sequence.id, None, owner, ctx)
    outsider = user(db)
    db.commit()
    with pytest.raises(HTTPException) as error:
        delivery_package(db, sequence.id, outsider, ctx)
    assert error.value.status_code in {403, 404}
    package = delivery_package(db, sequence.id, owner, ctx)
    assert package["drawing"]["revision_id"] == revision.id
    assert package["drawing"]["weld_joints"][0]["weld_number"] == "W1"
    assert {item["production_task_id"] for item in package["inspections"]} <= {
        task["id"] for task in package["tasks"]
    }


def test_concurrent_parent_edits_cannot_create_cycle(db, sessions, tmp_path):
    owner, ctx, revision, *_ = seed_workflow(db, tmp_path)
    revision.status = "draft"
    first = db.query(Part).filter_by(revision_id=revision.id).one()
    second = Part(
        revision_id=revision.id,
        name="Second",
        user_id=owner.id,
        workspace_type="personal",
        created_by=owner.id,
        access_level="private",
    )
    db.add(second)
    db.commit()
    gate = Barrier(2)

    def patch(part_id, parent_id):
        with sessions() as session:
            # Both sessions have read old parent state before either writes.
            retained_parent = session.get(Part, parent_id)
            gate.wait(timeout=10)
            try:
                EngineeringService(session).patch_entity(
                    Part, part_id, {"parent_part_id": parent_id}, "QA", owner, ctx
                )
                return 200
            except HTTPException as exc:
                session.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda pair: patch(*pair),
                [(first.id, second.id), (second.id, first.id)],
            )
        )
    assert sorted(results) == [200, 422]
    db.expire_all()
    assert not (first.parent_part_id == second.id and second.parent_part_id == first.id)


def test_approved_clone_remaps_part_links(db, tmp_path):
    owner, ctx, revision, *_ = seed_workflow(db, tmp_path)
    joint = db.query(WeldJoint).filter_by(revision_id=revision.id).one()
    old_part = joint.part_a_id
    EngineeringService(db).patch_entity(
        WeldJoint,
        joint.id,
        {"part_b_id": old_part, "weld_number": "W2"},
        "QA",
        owner,
        ctx,
    )
    new_joint = (
        db.query(WeldJoint)
        .filter(WeldJoint.weld_number == "W2", WeldJoint.user_id == owner.id)
        .one()
    )
    assert new_joint.revision_id != revision.id
    assert new_joint.part_b_id != old_part
    assert db.get(Part, new_joint.part_b_id).revision_id == new_joint.revision_id
    assert joint.part_b_id == old_part


def test_stale_ordinary_update_cannot_revert_completed_release_task(
    db, sessions, tmp_path
):
    owner, ctx, _, sequence, *_ = seed_workflow(db, tmp_path)
    batch, _ = ProductionReleaseService(db).release(sequence.id, None, owner, ctx)
    task = db.query(ProductionTask).filter_by(production_release_id=batch.id).first()
    with sessions() as other:
        live = other.get(ProductionTask, task.id)
        live.status = "completed"
        live.progress_percentage = 100
        other.commit()
    assert task.status != "completed"
    with pytest.raises(HTTPException) as error:
        ProductionService(db).update_production_task(
            task.id, owner, {"status": "pending", "progress_percentage": 0}, ctx
        )
    assert error.value.status_code == 409
    db.rollback()
    db.refresh(task)
    assert task.status == "completed" and task.progress_percentage == 100


def test_old_override_after_new_assignment_preserves_current_welder(db, tmp_path):
    owner, ctx, _, sequence, welder, cert = seed_workflow(db, tmp_path)
    service = ProductionReleaseService(db)
    batch, _ = service.release(sequence.id, None, owner, ctx)
    task = (
        db.query(ProductionTask)
        .filter_by(production_release_id=batch.id, task_type="welding")
        .first()
    )
    cert.qualified_process = "SMAW"
    db.commit()
    old = service.assign(task.id, welder.id, None, "QA override", owner, ctx)
    assert old.qualification_status == "pending_override"
    cert.qualified_process = "GTAW"
    db.commit()
    current = service.assign(task.id, welder.id, None, None, owner, ctx)
    assert current.qualification_status == "qualified"
    with pytest.raises(HTTPException) as error:
        service.authorize_override(old.id, True, owner, ctx)
    assert error.value.status_code == 409
    db.rollback()
    assert task.assigned_welder_id == welder.id
    assert old.qualification_status == "pending_override"


def test_override_racing_new_assignment_always_preserves_new_welder(
    db, sessions, tmp_path
):
    owner, ctx, _, sequence, welder, cert = seed_workflow(db, tmp_path)
    service = ProductionReleaseService(db)
    batch, _ = service.release(sequence.id, None, owner, ctx)
    task = (
        db.query(ProductionTask)
        .filter_by(production_release_id=batch.id, task_type="welding")
        .first()
    )
    cert.qualified_process = "SMAW"
    newer = Welder(
        welder_code=uuid4().hex,
        full_name="New qualified welder",
        is_active=True,
        status="active",
        user_id=owner.id,
        workspace_type="personal",
        created_by=owner.id,
        access_level="private",
    )
    db.add(newer)
    db.flush()
    db.add(
        WelderCertification(
            welder_id=newer.id,
            certification_type="GTAW",
            certification_number=uuid4().hex,
            qualified_process="GTAW",
            is_active=True,
            status="valid",
            expiry_date=cert.expiry_date,
            user_id=owner.id,
            created_by=owner.id,
        )
    )
    db.commit()
    pending = service.assign(task.id, welder.id, None, "QA override", owner, ctx)
    gate = Barrier(2)

    def operation(approve):
        with sessions() as session:
            retained = session.get(ProductionResourceAuthorization, pending.id)
            gate.wait(timeout=10)
            try:
                svc = ProductionReleaseService(session)
                if approve:
                    svc.authorize_override(pending.id, True, owner, ctx)
                else:
                    svc.assign(task.id, newer.id, None, None, owner, ctx)
                return 200
            except HTTPException as exc:
                session.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(operation, [True, False]))
    assert results[0] in {200, 409} and results[1] == 200
    db.refresh(task)
    assert task.assigned_welder_id == newer.id


def test_reviewed_treatment_stages_release_and_enforce_execution_order(db, tmp_path):
    owner, ctx, revision, _, welder, _ = seed_workflow(db, tmp_path)
    requirement = db.query(WeldRequirement).filter_by(revision_id=revision.id).one()
    requirement.pwht_required = True
    requirement.review_status = "accepted"
    requirement.treatment_plan = [
        {
            "code": "H1",
            "scope": "local",
            "temperature_min": 600,
            "temperature_max": 620,
            "hold_minutes": 60,
            "nde_before": ["VT"],
            "nde_after": ["RT"],
        }
    ]
    db.commit()
    seq = WeldSequenceService(db)
    sequence = seq.generate(revision.id, {}, None, None, owner, ctx)
    seq.submit(sequence.id, None, "normal", None, owner, ctx)
    svc = ProductionReleaseService(db)
    batch, _ = svc.release(sequence.id, None, owner, ctx)
    tasks = sorted(
        svc.detail(batch.id, owner, ctx)["tasks"],
        key=lambda t: t["source_step_snapshot"]["order_index"],
    )
    heat = next(t for t in tasks if t["source_step_snapshot"]["step_type"] == "pwht")
    with pytest.raises(HTTPException) as exc:
        svc.record_execution(
            heat["id"],
            {"idempotency_key": "too-early", "status": "completed"},
            owner,
            ctx,
        )
    assert exc.value.status_code == 409
    db.rollback()
    for task in tasks:
        if task["task_type"] == "welding":
            svc.assign(task["id"], welder.id, None, None, owner, ctx)
        for inspection in (
            db.query(QualityInspection).filter_by(production_task_id=task["id"]).all()
        ):
            inspection.inspection_result = "pass"
        db.commit()
        svc.record_execution(
            task["id"],
            {
                "idempotency_key": "done",
                "status": "completed",
                "actual_parameters": {"current": 100}
                if task["task_type"] == "welding"
                else {},
            },
            owner,
            ctx,
        )
    package = delivery_package(db, sequence.id, owner, ctx)
    assert len(package["executions"]) == len(tasks)
    assert (
        package["drawing"]["requirements"][0]["treatment_plan"]
        == requirement.treatment_plan
    )


def test_matching_position_is_checked_during_assignment_and_execution(db, tmp_path):
    owner, ctx, revision, _, welder, cert = seed_workflow(db, tmp_path)
    freeze = db.query(WPSMatchFreeze).filter_by(revision_id=revision.id).one()
    freeze.frozen_snapshot = {
        **freeze.frozen_snapshot,
        "requirement": {"welding_position": "3G"},
    }
    cert.qualified_position = "2G"
    db.commit()
    seq = WeldSequenceService(db)
    sequence = seq.generate(revision.id, {}, None, None, owner, ctx)
    seq.submit(sequence.id, None, "normal", None, owner, ctx)
    svc = ProductionReleaseService(db)
    batch, _ = svc.release(sequence.id, None, owner, ctx)
    task = (
        db.query(ProductionTask)
        .filter_by(production_release_id=batch.id, task_type="welding")
        .first()
    )
    with pytest.raises(HTTPException) as exc:
        svc.assign(task.id, welder.id, None, None, owner, ctx)
    assert exc.value.status_code == 409
    db.rollback()
    cert.qualified_position = "3G"
    db.commit()
    authorization = svc.assign(task.id, welder.id, None, None, owner, ctx)
    assert authorization.qualification_snapshot["welding_position"] == "3G"
    cert.qualified_position = "2G"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        svc._recheck_execution_resources(task, authorization, owner, ctx)
    assert exc.value.status_code == 409
    assert "3G 焊位资格" in str(exc.value.detail)

"""Authorized release package built from frozen design and current execution rows."""
from datetime import datetime, timezone

from fastapi import HTTPException
from app.models.engineering import Part, WeldJoint, WeldRequirement
from app.models.consumable import ConsumableIssueItem
from app.models.quality import QualityInspection
from app.services.qualification_service import _record_snapshot


def capture_drawing(db, revision):
    return {
        "revision_id": revision.id,
        "filename": revision.drawing_filename,
        "document_id": revision.drawing_document_id,
        "page_count": revision.drawing_page_count,
        "data_version": revision.data_version,
        "product": revision.drawing_metadata or {},
        "parts": [
            _record_snapshot(p)
            for p in db.query(Part)
            .filter(Part.revision_id == revision.id, Part.is_deleted.is_(False))
            .all()
        ],
        "weld_joints": [
            _record_snapshot(j)
            for j in db.query(WeldJoint)
            .filter(
                WeldJoint.revision_id == revision.id, WeldJoint.is_deleted.is_(False)
            )
            .all()
        ],
        "requirements": [
            _record_snapshot(r)
            for r in db.query(WeldRequirement)
            .filter(WeldRequirement.revision_id == revision.id)
            .all()
        ],
    }


def capture_issue(db, issue):
    if issue is None:
        return None
    return {
        "document": _record_snapshot(issue),
        "items": [
            _record_snapshot(item)
            for item in db.query(ConsumableIssueItem)
            .filter(ConsumableIssueItem.issue_list_id == issue.id)
            .all()
        ],
    }


def delivery_package(db, sequence_id, user, context):
    from app.services.production_release_service import ProductionReleaseService

    detail = ProductionReleaseService(db).for_sequence(sequence_id, user, context)
    if detail is None:
        raise HTTPException(409, "焊序尚未放行，没有施工交付包")
    batch = detail["release"]
    snapshot = batch.get("source_snapshot") or {}
    task_ids = [item["id"] for item in detail["tasks"]]
    inspections = (
        db.query(QualityInspection)
        .filter(QualityInspection.production_task_id.in_(task_ids))
        .all()
        if task_ids
        else []
    )
    return {
        **detail,
        "schema_version": "sequence-delivery-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "drawing": snapshot.get("drawing"),
        "issue": snapshot.get("issue"),
        "frozen_sequence": snapshot.get("sequence") or {},
        "inspections": [_record_snapshot(item) for item in inspections],
        "notice": "文件记录导出时状态。开工及完工以系统实时校验为准；二维码仅定位，不授予访问权限。",
    }

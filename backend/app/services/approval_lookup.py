"""Batch-load latest approval instances to avoid per-row queries."""
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalWorkflowDefinition


def load_latest_approvals(
    db: Session,
    document_type: str,
    document_ids: Iterable[int],
) -> tuple[dict[int, ApprovalInstance], dict[int, ApprovalWorkflowDefinition]]:
    ids = [int(item) for item in document_ids]
    if not ids:
        return {}, {}

    rows = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.document_type == document_type,
            ApprovalInstance.document_id.in_(ids),
        )
        .order_by(ApprovalInstance.created_at.desc())
        .all()
    )
    latest: dict[int, ApprovalInstance] = {}
    for row in rows:
        if row.document_id not in latest:
            latest[row.document_id] = row

    workflow_ids = {row.workflow_id for row in latest.values() if row.workflow_id}
    workflows: dict[int, ApprovalWorkflowDefinition] = {}
    if workflow_ids:
        workflows = {
            item.id: item
            for item in db.query(ApprovalWorkflowDefinition)
            .filter(ApprovalWorkflowDefinition.id.in_(workflow_ids))
            .all()
        }
    return latest, workflows

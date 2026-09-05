"""Synchronize the approved request before recalculation as well as application."""
from app.models.approval import ApprovalInstance


def sync_change_approval(db, item):
    if not item or item.status != "pending" or not item.approval_instance_id:
        return
    instance = db.get(ApprovalInstance, item.approval_instance_id)
    if not instance:
        return
    status = getattr(instance.status, "value", instance.status)
    if status in {"approved", "rejected", "returned", "cancelled"}:
        item.status = "approved" if status == "approved" else "rejected"
        item.decided_by = instance.final_approver_id
        item.decided_at = instance.completed_at

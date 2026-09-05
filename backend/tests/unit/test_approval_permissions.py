"""Batch approval permission tests."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from app.models.approval import DocumentType
from app.models.wps import WPS
from app.services.approval_service import ApprovalService


def test_admin_can_always_approve():
    service = ApprovalService(MagicMock())
    user = SimpleNamespace(id=1, is_admin=True)
    instance = SimpleNamespace(company_id=9, document_type="wps")
    assert service._can_approve(instance, user, {}) is True


def test_wps_signature_is_recorded_from_completed_workflow():
    from datetime import datetime
    db = MagicMock()
    document = WPS(id=11, title="WPS", wps_number="WPS-11", status="draft")
    db.query.return_value.filter.return_value.first.return_value = document
    completed = datetime(2026, 9, 5, 10, 0)
    instance = SimpleNamespace(document_type="wps", document_id=11,
                               final_approver_id=7, completed_at=completed)
    ApprovalService(db)._update_document_status(instance, "approved")
    assert document.status == "approved"
    assert document.approved_by == 7
    assert document.approved_date == completed


def test_can_approve_uses_preloaded_company_permissions():
    service = ApprovalService(MagicMock())
    user = SimpleNamespace(id=2, is_admin=False)
    instance = SimpleNamespace(company_id=5, document_type="wps")
    allowed = {5: {"wps_management": {"approve": True}}}
    denied = {5: {"wps_management": {"approve": False}}}
    missing = {8: {"wps_management": {"approve": True}}}

    assert service._can_approve(instance, user, allowed) is True
    assert service._can_approve(instance, user, denied) is False
    assert service._can_approve(instance, user, missing) is False


def test_can_approve_without_company_is_false():
    service = ApprovalService(MagicMock())
    user = SimpleNamespace(id=3, is_admin=False)
    instance = SimpleNamespace(company_id=None, document_type="pqr")
    assert service._can_approve(instance, user, {}) is False


def test_is_current_step_approver_by_role_and_user():
    service = ApprovalService(MagicMock())
    user = SimpleNamespace(id=42, is_admin=False)
    employee = SimpleNamespace(company_role_id=7, factory_id=3, department="质检")

    assert service._is_current_step_approver(
        {"approver_type": "role", "approver_ids": [7, 8]},
        user=user,
        employee=employee,
    )
    assert not service._is_current_step_approver(
        {"approver_type": "role", "approver_ids": [9]},
        user=user,
        employee=employee,
    )
    assert service._is_current_step_approver(
        {"approver_type": "user", "approver_ids": [42]},
        user=user,
        employee=employee,
    )
    assert service._is_current_step_approver(
        {"approver_type": "department", "approver_ids": [3]},
        user=user,
        employee=employee,
    )
    assert service._is_current_step_approver(
        {"approver_type": "department", "approver_ids": ["质检"]},
        user=user,
        employee=employee,
    )


def test_current_step_config_is_one_based():
    service = ApprovalService(MagicMock())
    workflow = SimpleNamespace(
        steps=[
            {"step_number": 1, "approver_type": "role", "approver_ids": [1]},
            {"step_number": 2, "approver_type": "user", "approver_ids": [9]},
        ]
    )
    instance = SimpleNamespace(
        current_step=2, workflow_id=1, workflow_definition=workflow
    )
    step = service._current_step_config(instance, workflow)
    assert step["approver_type"] == "user"
    assert step["approver_ids"] == [9]


def test_new_versioned_approval_document_types_are_registered():
    assert {
        DocumentType.IMPORT_DRAFT.value,
        DocumentType.RULE_PACKAGE.value,
        DocumentType.PRODUCT_VERSION.value,
        DocumentType.WELD_SEQUENCE_VERSION.value,
    } == {
        "import_draft",
        "rule_package",
        "product_version",
        "weld_sequence_version",
    }


def test_approval_detects_silent_document_change():
    db = MagicMock()
    document = WPS(id=11, title="Original", wps_number="WPS-11")
    snapshot = jsonable_encoder(
        {
            column.name: getattr(document, column.name)
            for column in document.__table__.columns
            if column.name not in {"status", "updated_at"}
        }
    )
    service = ApprovalService(db)
    instance = SimpleNamespace(
        document_type="wps",
        document_id=11,
        snapshot_hash=service._snapshot_hash(snapshot),
    )
    db.query.return_value.filter.return_value.first.return_value = document

    service._assert_snapshot_unchanged(instance)
    document.title = "Changed without resubmission"

    with pytest.raises(HTTPException) as exc_info:
        service._assert_snapshot_unchanged(instance)
    assert exc_info.value.status_code == 409

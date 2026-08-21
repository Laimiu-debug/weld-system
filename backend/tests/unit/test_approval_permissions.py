"""Batch approval permission tests."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.approval_service import ApprovalService


def test_admin_can_always_approve():
    service = ApprovalService(MagicMock())
    user = SimpleNamespace(id=1, is_admin=True)
    instance = SimpleNamespace(company_id=9, document_type="wps")
    assert service._can_approve(instance, user, {}) is True


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
    instance = SimpleNamespace(current_step=2, workflow_id=1, workflow_definition=workflow)
    step = service._current_step_config(instance, workflow)
    assert step["approver_type"] == "user"
    assert step["approver_ids"] == [9]

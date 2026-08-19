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

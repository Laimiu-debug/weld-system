"""Unit tests for enterprise invitation redemption."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.invitation_service import InvitationService, _parse_optional_int


def test_parse_optional_int():
    assert _parse_optional_int("12") == 12
    assert _parse_optional_int(8) == 8
    assert _parse_optional_int("") is None
    assert _parse_optional_int(None) is None


def test_require_pending_rejects_email_mismatch():
    invitation = SimpleNamespace(
        email="owner@example.com",
        status="pending",
        expires_at=datetime.utcnow() + timedelta(days=2),
    )
    service = InvitationService(MagicMock())
    service._get_by_token = MagicMock(return_value=invitation)

    with pytest.raises(HTTPException) as exc:
        service.require_pending("token", "other@example.com")

    assert exc.value.status_code == 400
    assert "邮箱" in exc.value.detail


def test_require_pending_rejects_expired_invite():
    invitation = SimpleNamespace(
        email="owner@example.com",
        status="pending",
        expires_at=datetime.utcnow() - timedelta(hours=1),
    )
    db = MagicMock()
    service = InvitationService(db)
    service._get_by_token = MagicMock(return_value=invitation)

    with pytest.raises(HTTPException) as exc:
        service.require_pending("token", "owner@example.com")

    assert exc.value.status_code == 400
    assert invitation.status == "expired"


def test_serialize_invitation_includes_factory_name():
    invitation = SimpleNamespace(
        id=9,
        email="join@example.com",
        invitation_code="INV-ABCD",
        role="employee",
        factory_id=3,
        department="焊接车间",
        status="pending",
        permissions={"wps.view": True},
        message="欢迎",
        expires_at=datetime(2026, 8, 26, 12, 0, 0),
        accepted_at=None,
        created_at=datetime(2026, 8, 19, 8, 0, 0),
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(name="一厂")
    service = InvitationService(db)

    data = service.serialize(invitation)

    assert data["id"] == "9"
    assert data["factory_name"] == "一厂"
    assert data["invitation_code"] == "INV-ABCD"
    assert data["department_name"] == "焊接车间"

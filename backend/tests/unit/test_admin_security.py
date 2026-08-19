"""Admin security listing tests."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.admin_user_service import admin_user_service


def test_list_admins_omits_password_hash():
    admin = SimpleNamespace(
        id=1,
        username="ops",
        email="ops@example.com",
        full_name="Ops Admin",
        is_super_admin=True,
        admin_level="super_admin",
        permissions=["all"],
        is_active=True,
        last_login_at=None,
        created_at=None,
        hashed_password="should-not-leak",
    )
    db = MagicMock()
    db.query.return_value.order_by.return_value.all.return_value = [admin]

    result = admin_user_service.list_admins(db)

    assert result["total"] == 1
    assert result["items"][0]["username"] == "ops"
    assert result["items"][0]["role"] == "super_admin"
    assert "hashed_password" not in result["items"][0]
    assert "password" not in result["items"][0]


def test_list_admins_flattens_permission_dict():
    admin = SimpleNamespace(
        id=2,
        username="sec",
        email="sec@example.com",
        full_name="Sec",
        is_super_admin=False,
        admin_level="admin",
        permissions={"user_management": True, "security_logs": False},
        is_active=True,
        last_login_at=None,
        created_at=None,
        hashed_password="secret",
    )
    db = MagicMock()
    db.query.return_value.order_by.return_value.all.return_value = [admin]

    result = admin_user_service.list_admins(db)

    assert result["items"][0]["permissions"] == ["user_management"]
    assert result["items"][0]["role"] == "admin"

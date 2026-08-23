from types import SimpleNamespace
from unittest.mock import Mock

from app.api.v1.endpoints import pqr, smart_import, welders, wps
from app.core import config
from app.core.data_access import WorkspaceContext, WorkspaceType
from app.services.permission_service import Permission


def _post_paths(router) -> set[str]:
    return {
        route.path
        for route in router.routes
        if "POST" in getattr(route, "methods", set())
    }


def test_manual_wps_pqr_welder_and_import_draft_routes_work_without_ai_config(
    monkeypatch,
) -> None:
    monkeypatch.setattr(config.settings, "AI_PLATFORM_API_KEY", None)
    monkeypatch.setattr(config.settings, "AI_PLATFORM_MODEL", None)

    assert "/" in _post_paths(wps.router)
    assert "/" in _post_paths(pqr.router)
    assert "/" in _post_paths(welders.router)
    assert "/documents/{document_id}/manual-drafts" in _post_paths(smart_import.router)


def test_import_permissions_distinguish_all_sensitive_actions() -> None:
    values = {permission.value for permission in Permission}
    assert {
        "import.upload",
        "import.extract",
        "import.modify",
        "import.review",
        "import.publish",
        "import.key_manage",
    }.issubset(values)
    assert any(value.startswith("engineering.") for value in values)
    assert any(value.startswith("capability.") for value in values)
    assert any(value.startswith("rules.") for value in values)


def test_personal_import_is_owner_scoped_and_enterprise_uses_role_permission(
    monkeypatch,
) -> None:
    check = Mock()
    monkeypatch.setattr(smart_import, "ensure_module_permission", check)
    user = SimpleNamespace(id=7, is_active=True)

    smart_import.ensure_import_permission(
        Mock(), user, WorkspaceContext(7, WorkspaceType.PERSONAL), "publish"
    )
    check.assert_not_called()

    enterprise = WorkspaceContext(
        7, WorkspaceType.ENTERPRISE, company_id=3, factory_id=4
    )
    db = Mock()
    smart_import.ensure_import_permission(db, user, enterprise, "publish")
    check.assert_called_once_with(db, user, "import", "publish")

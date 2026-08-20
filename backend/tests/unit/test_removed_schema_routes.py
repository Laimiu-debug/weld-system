"""Regression tests for schema-mutating maintenance endpoints."""

from app.api.v1.endpoints.company_roles import router


def test_schema_initialization_routes_are_not_exposed() -> None:
    paths = {route.path for route in router.routes}

    assert "/roles/init" not in paths
    assert "/roles/init-table" not in paths

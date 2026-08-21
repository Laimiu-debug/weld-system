"""Smoke tests for workspace entity helpers."""
from app.services.workspace_entity_service import (
    paginated_payload,
    plan_service,
    standard_service,
)


def test_paginated_payload():
    data = paginated_payload([{"id": 1}], total=11, skip=10, limit=10)
    assert data["page"] == 2
    assert data["total_pages"] == 2
    assert data["total"] == 11


def test_service_factories_bind_models():
    from unittest.mock import MagicMock

    db = MagicMock()
    assert plan_service(db).code_field == "plan_number"
    assert standard_service(db).code_field == "standard_code"

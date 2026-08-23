from pydantic import ValidationError
import pytest

from app.schemas.smart_import import FormPublishRequest
from app.api.v1.endpoints.smart_import import router
from app.services.smart_import_template_service import SmartImportTemplateService


def test_content_classifier_detects_pqr_process_and_standard() -> None:
    result = SmartImportTemplateService.classify(
        "Procedure Qualification Record PQR-001 ASME Section IX GTAW 141",
        "unknown",
    )

    assert result["document_type"] == "pqr"
    assert result["confidence"] >= 0.75
    assert "GTAW" in result["detected_processes"]
    assert any("ASME" in value.upper() for value in result["detected_standards"])


def test_form_publish_requires_pqr_id_for_matched_decision() -> None:
    with pytest.raises(ValidationError):
        FormPublishRequest(
            payload={"wps_number": "WPS-1", "title": "WPS"},
            supporting_pqr_decision="matched",
        )


def test_p1_template_and_existing_form_routes_are_registered() -> None:
    paths = {route.path for route in router.routes}

    assert "/documents/{document_id}/template-recommendations" in paths
    assert "/entities/{entity_id}/form-handoff" in paths
    assert "/entities/{entity_id}/form-publish" in paths

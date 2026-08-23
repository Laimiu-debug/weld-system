from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

from app.core.data_access import WorkspaceContext, WorkspaceType
from app.models.smart_import import (
    DocumentPage,
    ExtractedEntity,
    ExtractedField,
    FieldEvidence,
)
from app.services.ai_extraction_service import (
    AIExtractionService,
    relax_business_required_fields,
)
from app.services.ai_provider_service import AIProviderResult


SCHEMA_SNAPSHOT = {
    "schema_version": "1.0",
    "document_type": "pqr",
    "json_schema": {
        "type": "object",
        "properties": {
            "pqr_number": {
                "type": "object",
                "x-weld-field-id": "field-1",
                "properties": {
                    "value": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "page": {"type": "integer", "minimum": 1},
                                "text": {"type": "string"},
                            },
                            "required": ["page", "text"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["value", "confidence", "evidence"],
                "additionalProperties": False,
            }
        },
        "required": ["pqr_number"],
        "additionalProperties": False,
    },
    "field_bindings": [
        {
            "module_id": "basic",
            "instance_id": None,
            "field_id": "field-1",
            "field_key": "pqr_number",
            "canonical_field_key": "document.number",
            "extractable": True,
        }
    ],
}


class FakeProvider:
    provider_name = "openai_responses"
    model_name = "vision-model"

    def __init__(self):
        self.calls = 0

    def structured_response(self, request):
        self.calls += 1
        if self.calls == 1:
            return AIProviderResult(
                {"text": "PQR No. PQR-001", "confidence": 0.95},
                "ocr-response",
                10,
                5,
                15,
            )
        return AIProviderResult(
            {
                "pqr_number": {
                    "value": "PQR-001",
                    "confidence": 0.96,
                    "evidence": [{"page": 1, "text": "PQR No. PQR-001"}],
                }
            },
            "extract-response",
            20,
            8,
            28,
        )


def test_runtime_schema_allows_missing_business_field_but_keeps_payload_contract() -> (
    None
):
    runtime = relax_business_required_fields(SCHEMA_SNAPSHOT["json_schema"])

    assert "required" not in runtime
    field_schema = runtime["properties"]["pqr_number"]
    assert field_schema["required"] == ["value", "confidence", "evidence"]


def test_scanned_page_ocr_and_extraction_create_review_only_evidence() -> None:
    db = Mock()
    added = []
    db.add.side_effect = added.append
    document = SimpleNamespace(
        id="document-1",
        batch_id="batch-1",
        status="ready",
        storage_key="private_documents/file.pdf",
        original_filename="PQR.pdf",
        user_id=7,
        workspace_type="personal",
        company_id=None,
        factory_id=None,
        access_level="private",
    )
    batch = SimpleNamespace(
        id="batch-1",
        target_entity_type="pqr",
        total_documents=1,
        processed_documents=0,
        progress=0,
        status="draft",
    )
    page = DocumentPage(
        id="page-1",
        document_id=document.id,
        page_number=1,
        text_content="",
        ocr_status="pending",
        page_metadata={},
        user_id=7,
        workspace_type="personal",
        access_level="private",
    )
    query = Mock()
    query.filter.return_value.order_by.return_value.first.return_value = None
    smart_import = Mock()
    smart_import.get_document.return_value = document
    smart_import.get_batch.return_value = batch
    smart_import.get_document_pages.return_value = [page]
    smart_import._scope_query.return_value = query
    storage = Mock()
    storage.open_stream.return_value = BytesIO(b"pdf")
    renderer = Mock()
    renderer.render_png.return_value = b"\x89PNG\r\n\x1a\nimage"
    provider = FakeProvider()
    quota = Mock()
    service = AIExtractionService(db, storage, provider, renderer, quota)
    service.smart_import = smart_import
    context = WorkspaceContext(user_id=7, workspace_type=WorkspaceType.PERSONAL)

    job, entity, pages = service.run(
        document.id,
        SCHEMA_SNAPSHOT,
        None,
        "byok",
        True,
        SimpleNamespace(id=7),
        context,
    )

    assert page.ocr_status == "completed"
    assert page.text_content == "PQR No. PQR-001"
    assert job.status == "completed"
    assert job.external_response_id == "extract-response"
    assert (job.input_tokens, job.output_tokens, job.total_tokens) == (30, 13, 43)
    assert entity.status == "draft"
    assert entity.draft_data == {"pqr_number": "PQR-001"}
    assert batch.status == "review"
    assert pages == [page]
    assert any(isinstance(item, ExtractedEntity) for item in added)
    assert any(isinstance(item, ExtractedField) for item in added)
    evidence = next(item for item in added if isinstance(item, FieldEvidence))
    assert evidence.page_id == "page-1"
    assert evidence.evidence_type == "ocr"
    quota.settle.assert_called_once_with(job, SimpleNamespace(id=7), context, 1)

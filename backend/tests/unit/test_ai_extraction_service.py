from io import BytesIO
from copy import deepcopy
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
    build_extraction_stages,
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
            },
            "notes": {
                "type": "object",
                "x-weld-field-id": "field-2",
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
            },
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
        },
        {
            "module_id": "enterprise-notes",
            "instance_id": None,
            "field_id": "field-2",
            "field_key": "notes",
            "canonical_field_key": None,
            "extractable": True,
        },
    ],
}


class FakeProvider:
    provider_name = "openai_responses"
    model_name = "vision-model"

    def __init__(self):
        self.calls = 0

    def structured_response(self, request):
        self.calls += 1
        properties = request.json_schema["properties"]
        if "text" in properties:
            return AIProviderResult(
                {"text": "PQR No. PQR-001", "confidence": 0.95},
                "ocr-response",
                10,
                5,
                15,
            )
        if "pqr_number" in properties:
            return AIProviderResult(
                {
                    "pqr_number": {
                        "value": "PQR-001",
                        "confidence": 0.96,
                        "evidence": [{"page": 1, "text": "PQR No. PQR-001"}],
                    }
                },
                "core-response",
                20,
                8,
                28,
            )
        if "unmapped_fields" in properties:
            return AIProviderResult(
                {
                    "unmapped_fields": [
                        {
                            "label": "Legacy note",
                            "suggested_key": "legacy_note",
                            "value": "PQR-001",
                            "confidence": 0.72,
                            "evidence": [{"page": 1, "text": "PQR No. PQR-001"}],
                        }
                    ]
                },
                None,
                0,
                0,
                0,
            )
        return AIProviderResult(
            {
                "notes": {
                    "value": "PQR-001",
                    "confidence": 0.91,
                    "evidence": [{"page": 1, "text": "PQR No. PQR-001"}],
                }
            },
            "custom-response",
            7,
            3,
            10,
        )


def test_runtime_schema_allows_missing_business_field_but_keeps_payload_contract() -> (
    None
):
    runtime = relax_business_required_fields(SCHEMA_SNAPSHOT["json_schema"])

    assert "required" not in runtime
    field_schema = runtime["properties"]["pqr_number"]
    assert field_schema["required"] == ["value", "confidence", "evidence"]


def test_schema_is_split_into_core_and_enterprise_custom_stages() -> None:
    stages = build_extraction_stages(SCHEMA_SNAPSHOT)

    assert [stage["name"] for stage in stages] == [
        "core_fields_1",
        "enterprise_custom_fields_1",
    ]
    assert set(stages[0]["json_schema"]["properties"]) == {"pqr_number"}
    assert set(stages[1]["json_schema"]["properties"]) == {"notes"}


def test_staged_schema_preserves_template_instance_paths_and_chunks_custom_fields() -> (
    None
):
    field_schemas = SCHEMA_SNAPSHOT["json_schema"]["properties"]
    snapshot = {
        "json_schema": {
            "type": "object",
            "properties": {
                "instance-1": {
                    "type": "object",
                    "properties": deepcopy(field_schemas),
                    "required": ["pqr_number", "notes"],
                    "additionalProperties": False,
                }
            },
            "required": ["instance-1"],
            "additionalProperties": False,
        },
        "field_bindings": [
            {**binding, "instance_id": "instance-1"}
            for binding in SCHEMA_SNAPSHOT["field_bindings"]
        ],
    }

    stages = build_extraction_stages(snapshot, max_fields=1)

    assert len(stages) == 2
    assert set(stages[0]["json_schema"]["properties"]["instance-1"]["properties"]) == {
        "pqr_number"
    }
    assert set(stages[1]["json_schema"]["properties"]["instance-1"]["properties"]) == {
        "notes"
    }


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
    assert job.external_response_id == "custom-response"
    assert (job.input_tokens, job.output_tokens, job.total_tokens) == (37, 16, 53)
    assert entity.status == "draft"
    assert entity.draft_data == {"pqr_number": "PQR-001", "notes": "PQR-001"}
    assert batch.status == "review"
    assert pages == [page]
    assert any(isinstance(item, ExtractedEntity) for item in added)
    assert any(isinstance(item, ExtractedField) for item in added)
    assert any(
        isinstance(item, ExtractedField) and item.module_id == "unmapped"
        for item in added
    )
    evidence = next(item for item in added if isinstance(item, FieldEvidence))
    assert evidence.page_id == "page-1"
    assert evidence.evidence_type == "ocr"
    assert provider.calls == 4
    quota.settle.assert_called_once_with(job, SimpleNamespace(id=7), context, 1)

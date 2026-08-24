from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.core.data_access import WorkspaceContext, WorkspaceType
from app.api.v1.endpoints.smart_import import (
    build_entity_detail,
    router,
    validate_ai_extraction_request,
)
from app.models.smart_import import (
    AIUsageLedger,
    DocumentArtifact,
    DocumentPage,
    EntityPublishRecord,
    ExtractedEntity,
    ExtractedField,
    ExtractionJob,
    FieldEvidence,
    ImportBatch,
    ImportReviewRecord,
    SourceDocument,
)
from app.schemas.smart_import import (
    AIExtractionRequest,
    ManualDraftCreate,
    SourceDocumentRegister,
)
from app.services.smart_import_service import SmartImportService


WORKSPACE_MODELS = (
    ImportBatch,
    SourceDocument,
    DocumentPage,
    ExtractionJob,
    ExtractedEntity,
    ExtractedField,
    FieldEvidence,
    ImportReviewRecord,
    EntityPublishRecord,
    AIUsageLedger,
)


def test_all_staging_models_have_workspace_isolation_columns() -> None:
    required = {"user_id", "workspace_type", "company_id", "factory_id", "access_level"}
    for model in WORKSPACE_MODELS:
        assert required.issubset(model.__table__.columns.keys()), model.__name__
        constraint_names = {item.name for item in model.__table__.constraints}
        assert any(
            name and name.endswith("workspace_type") for name in constraint_names
        )
        assert any(name and name.endswith("access_level") for name in constraint_names)
        assert "CREATE TABLE" in str(
            CreateTable(model.__table__).compile(dialect=postgresql.dialect())
        )


def test_source_document_rejects_invalid_hash_and_path_filename() -> None:
    with pytest.raises(ValidationError):
        SourceDocumentRegister(
            original_filename="../pqr.pdf",
            sha256="bad-hash",
            document_type="pqr",
        )


def test_manual_draft_does_not_require_ai_configuration() -> None:
    draft = ManualDraftCreate(
        entity_type="pqr",
        schema_version="1.0",
        draft_data={"pqr_number": "PQR-001"},
        fields=[
            {
                "field_key": "pqr_number",
                "value": "PQR-001",
                "evidence": [
                    {"page_number": 1, "text": "PQR No. PQR-001", "bbox": [1, 2, 3, 4]}
                ],
            }
        ],
    )

    assert draft.fields[0].value == "PQR-001"
    assert draft.fields[0].evidence[0].page_number == 1


def test_temporary_byok_key_is_masked_and_validation_error_does_not_echo_it() -> None:
    request = AIExtractionRequest(
        mode="byok",
        api_key="super-secret-key",
        module_id="module-1",
    )

    assert "super-secret-key" not in repr(request)
    assert "super-secret-key" not in request.model_dump_json()
    with pytest.raises(HTTPException) as exc_info:
        validate_ai_extraction_request(request)
    assert "super-secret-key" not in str(exc_info.value.detail)


def test_personal_scope_only_contains_current_user() -> None:
    db = Session()
    service = SmartImportService(db)
    user = SimpleNamespace(id=7)
    context = WorkspaceContext(user_id=7, workspace_type=WorkspaceType.PERSONAL)

    query = service._scope_query(db.query(ImportBatch), ImportBatch, user, context)
    sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

    assert "import_batches.workspace_type = 'personal'" in sql
    assert "import_batches.user_id = 7" in sql


def test_enterprise_scope_limits_company_and_factory_visibility() -> None:
    db = Session()
    service = SmartImportService(db)
    user = SimpleNamespace(id=7)
    context = WorkspaceContext(
        user_id=7,
        workspace_type=WorkspaceType.ENTERPRISE,
        company_id=3,
        factory_id=4,
    )

    query = service._scope_query(db.query(ImportBatch), ImportBatch, user, context)
    sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

    assert "import_batches.workspace_type = 'enterprise'" in sql
    assert "import_batches.company_id = 3" in sql
    assert "import_batches.factory_id = 4" in sql
    assert "import_batches.user_id = 7" in sql


def test_smart_import_router_exposes_extract_review_and_publish_flow() -> None:
    paths = {route.path for route in router.routes}

    assert "/batches" in paths
    assert "/batches/{batch_id}" in paths
    assert "/ai-capabilities" in paths
    assert "/ai-quota" in paths
    assert "/batches/{batch_id}/documents" in paths
    assert "/batches/{batch_id}/upload" in paths
    assert "/documents/{document_id}/content" in paths
    assert "/documents/{document_id}/parse" in paths
    assert "/documents/{document_id}/pages" in paths
    assert "/documents/{document_id}/extract" in paths
    assert "/entities/{entity_id}" in paths
    assert "/entities/{entity_id}/fields/{field_id}/review" in paths
    assert "/entities/{entity_id}/fields/bulk-accept" in paths
    assert "/entities/{entity_id}/publish" in paths
    assert "/documents/{document_id}/manual-drafts" in paths


def test_entity_detail_contains_field_confidence_and_evidence() -> None:
    entity = ExtractedEntity(
        id="entity-1",
        document_id="document-1",
        entity_type="pqr",
        source_mode="ai",
        status="draft",
        draft_data={"pqr_number": "PQR-001"},
        version=1,
        user_id=7,
        workspace_type="personal",
        access_level="private",
        created_at=datetime(2026, 1, 1),
    )
    field = ExtractedField(
        id="field-1",
        entity_id=entity.id,
        field_key="pqr_number",
        normalized_value="PQR-001",
        confidence=0.96,
        review_status="pending",
        schema_version="1.0",
        user_id=7,
        workspace_type="personal",
        access_level="private",
    )
    evidence = FieldEvidence(
        id="evidence-1",
        extracted_field_id=field.id,
        page_number=1,
        evidence_type="ocr",
        text_excerpt="PQR No. PQR-001",
        user_id=7,
        workspace_type="personal",
        access_level="private",
    )
    field_query = Mock()
    field_query.filter.return_value.order_by.return_value.all.return_value = [field]
    evidence_query = Mock()
    evidence_query.filter.return_value.order_by.return_value.all.return_value = [
        evidence
    ]
    db = Mock()
    db.query.side_effect = [field_query, evidence_query]

    detail = build_entity_detail(db, entity)

    assert detail.fields[0].confidence == 0.96
    assert detail.fields[0].evidence[0].page_number == 1
    assert detail.fields[0].evidence[0].text_excerpt == "PQR No. PQR-001"


def test_creator_can_view_own_enterprise_batch_without_new_role_definition() -> None:
    service = SmartImportService(Session())
    service.data_access = SimpleNamespace(check_access=Mock())
    user = SimpleNamespace(id=7)
    context = WorkspaceContext(
        user_id=7,
        workspace_type=WorkspaceType.ENTERPRISE,
        company_id=3,
        factory_id=4,
    )
    resource = SimpleNamespace(
        user_id=7,
        workspace_type=WorkspaceType.ENTERPRISE,
        company_id=3,
    )

    service._check_view(resource, user, context)

    service.data_access.check_access.assert_not_called()


def test_register_document_flushes_parent_before_original_artifact() -> None:
    events: list[str] = []
    db = Mock()
    db.add.side_effect = lambda item: events.append(f"add:{type(item).__name__}")
    db.flush.side_effect = lambda: events.append("flush")
    db.refresh.side_effect = lambda _item: None
    duplicate_query = Mock()
    duplicate_query.filter.return_value.first.return_value = None
    service = SmartImportService(db)
    service.get_batch = Mock(
        return_value=SimpleNamespace(
            id="batch-1", status="draft", total_documents=0, access_level="private"
        )
    )
    service._scope_query = Mock(return_value=duplicate_query)
    user = SimpleNamespace(id=7)
    context = WorkspaceContext(user_id=7, workspace_type=WorkspaceType.PERSONAL)

    service.register_document(
        "batch-1",
        SourceDocumentRegister(
            original_filename="sample.doc",
            storage_key="private/sample.doc",
            sha256="a" * 64,
            mime_type="application/msword",
            size_bytes=100,
            document_type="pqr",
        ),
        user,
        context,
    )

    assert events[:3] == ["add:SourceDocument", "flush", "add:DocumentArtifact"]
    assert DocumentArtifact.__tablename__ == "document_artifacts"


def test_delete_batch_removes_private_objects_after_database_commit() -> None:
    events: list[str] = []
    db = Mock()
    artifact_query = Mock()
    artifact_query.filter.return_value.all.return_value = [("private/preview.png",)]
    job_query = Mock()
    job_query.filter.return_value.all.return_value = [
        SimpleNamespace(id="job-1", status="processing")
    ]
    db.query.side_effect = [artifact_query, job_query]
    db.delete.side_effect = lambda _item: events.append("delete")
    db.commit.side_effect = lambda: events.append("commit")
    storage = Mock()
    storage.delete.side_effect = lambda key: events.append(f"storage:{key}")
    service = SmartImportService(db)
    service.get_batch = Mock(return_value=SimpleNamespace(id="batch-1"))
    service.get_batch_documents = Mock(
        return_value=[
            SimpleNamespace(
                id="document-1", storage_key="private/original.pdf"
            )
        ]
    )
    user = SimpleNamespace(id=7)
    context = WorkspaceContext(user_id=7, workspace_type=WorkspaceType.PERSONAL)

    result = service.delete_batch(
        "batch-1", user, context, storage, delete_related_data=False
    )

    assert result["cancelled_job_ids"] == ["job-1"]
    assert result["deleted_documents"] == 1
    assert events[:2] == ["delete", "commit"]
    assert set(events[2:]) == {
        "storage:private/original.pdf",
        "storage:private/preview.png",
    }


def test_delete_batch_turns_foreign_key_conflict_into_409() -> None:
    from fastapi import HTTPException
    from sqlalchemy.exc import IntegrityError

    db = Mock()
    artifact_query = Mock()
    artifact_query.filter.return_value.all.return_value = []
    job_query = Mock()
    job_query.filter.return_value.all.return_value = []
    db.query.side_effect = [artifact_query, job_query]
    db.commit.side_effect = IntegrityError("delete", {}, Exception("fk"))
    service = SmartImportService(db)
    service.get_batch = Mock(return_value=SimpleNamespace(id="batch-1"))
    service.get_batch_documents = Mock(
        return_value=[SimpleNamespace(id="document-1", storage_key=None)]
    )

    with pytest.raises(HTTPException) as exc_info:
        service.delete_batch(
            "batch-1",
            SimpleNamespace(id=7),
            WorkspaceContext(user_id=7, workspace_type=WorkspaceType.PERSONAL),
            Mock(),
        )

    assert exc_info.value.status_code == 409
    db.rollback.assert_called_once()

from types import SimpleNamespace
from unittest.mock import Mock

from app.core.data_access import WorkspaceContext, WorkspaceType
from app.models.system_log import SystemLog
from app.services.smart_import_audit_service import SmartImportAuditService


def test_sensitive_file_audit_uses_ids_and_hash_without_storage_path():
    db = Mock()
    document = SimpleNamespace(
        id="doc-1",
        batch_id="batch-1",
        document_type="pqr",
        sha256="a" * 64,
        storage_key="private_documents/secret/path.pdf",
    )
    context = WorkspaceContext(7, WorkspaceType.ENTERPRISE, company_id=3)

    SmartImportAuditService(db).record_file_access("download", document, 7, context)

    event = db.add.call_args.args[0]
    assert isinstance(event, SystemLog)
    assert event.details["event"] == "sensitive_file_access"
    assert "storage_key" not in event.details
    assert "secret/path" not in str(event.details)


def test_ai_disclosure_audit_never_contains_text_or_api_key():
    db = Mock()

    SmartImportAuditService(db).record_ai_disclosure(
        job_id="job-1",
        document_id="doc-1",
        user_id=7,
        provider="openai_responses",
        model="model-1",
        phase="core_fields_1",
        page_numbers=[1, 2],
        workspace_type="enterprise",
        company_id=3,
    )

    event = db.add.call_args.args[0]
    assert event.details["contains_api_key"] is False
    assert "api_key" not in event.details
    assert "document_text" not in event.details

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

from app.core.data_access import WorkspaceContext, WorkspaceType
from app.models.smart_import import DocumentPage
from app.services.document_parser_service import ParsedDocument, ParsedPage
from app.services.smart_import_service import SmartImportService


def test_parse_document_replaces_pages_and_preserves_document_owner() -> None:
    db = Mock()
    delete_query = db.query.return_value.filter.return_value
    document = SimpleNamespace(
        id="document-1",
        storage_key="private_documents/a/file.pdf",
        original_filename="PQR.pdf",
        mime_type="application/pdf",
        status="stored",
        metadata_json={},
        user_id=7,
        workspace_type="enterprise",
        company_id=3,
        factory_id=4,
        access_level="factory",
        page_count=None,
    )
    parser = Mock()
    parser.parse.return_value = ParsedDocument(
        parser="pypdf",
        pages=[
            ParsedPage(1, "PQR-001", "not_required", {"source_format": "pdf"}),
            ParsedPage(2, "", "pending", {"source_format": "pdf"}),
        ],
    )
    storage = Mock()
    storage.open_stream.return_value = BytesIO(b"pdf")
    service = SmartImportService(db)
    service.get_document = Mock(return_value=document)

    result, pages = service.parse_document(
        document.id,
        SimpleNamespace(id=9),
        WorkspaceContext(
            user_id=9,
            workspace_type=WorkspaceType.ENTERPRISE,
            company_id=3,
            factory_id=4,
        ),
        storage,
        parser,
    )

    assert result.status == "ready"
    assert result.page_count == 2
    assert [page.ocr_status for page in pages] == ["not_required", "pending"]
    assert all(page.user_id == 7 for page in pages)
    assert all(page.factory_id == 4 for page in pages)
    delete_query.delete.assert_called_once_with(synchronize_session=False)
    db.add_all.assert_called_once()
    assert db.commit.call_count == 2


def test_document_page_query_is_ordered_and_authorized_through_document() -> None:
    db = Mock()
    expected = [SimpleNamespace(page_number=1)]
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
        expected
    )
    service = SmartImportService(db)
    service.get_document = Mock(return_value=SimpleNamespace(id="document-1"))
    user = SimpleNamespace(id=7)
    context = WorkspaceContext(user_id=7, workspace_type=WorkspaceType.PERSONAL)

    pages = service.get_document_pages("document-1", user, context)

    assert pages == expected
    service.get_document.assert_called_once_with("document-1", user, context)
    db.query.assert_called_once_with(DocumentPage)

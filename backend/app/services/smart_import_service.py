"""Transactional service for staged document imports."""
from datetime import datetime, timezone
from typing import Any, TypeVar
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query, Session

from app.core.data_access import (
    AccessLevel,
    DataAccessAction,
    DataAccessMiddleware,
    WorkspaceContext,
    WorkspaceType,
)
from app.models.smart_import import (
    DocumentArtifact,
    DocumentPage,
    ExtractedEntity,
    ExtractedField,
    ExtractionJob,
    FieldEvidence,
    ImportBatch,
    SourceDocument,
)
from app.models.user import User
from app.schemas.smart_import import (
    ImportBatchCreate,
    ManualDraftCreate,
    SourceDocumentRegister,
)
from app.services.document_parser_service import (
    DocumentParseError,
    DocumentParser,
)
from app.services.document_storage_service import DocumentStorage, DocumentUploadError
from app.services.document_artifact_service import artifact_expiry


T = TypeVar("T")


class SmartImportService:
    def __init__(self, db: Session):
        self.db = db
        self.data_access = DataAccessMiddleware(db)

    @staticmethod
    def _workspace_values(
        user: User, context: WorkspaceContext, access_level: str
    ) -> dict:
        context.validate()
        return {
            "user_id": user.id,
            "workspace_type": context.workspace_type,
            "company_id": context.company_id,
            "factory_id": context.factory_id,
            "access_level": access_level,
        }

    def _check_view(self, resource: Any, user: User, context: WorkspaceContext) -> None:
        is_own_personal = (
            context.workspace_type == WorkspaceType.PERSONAL
            and resource.workspace_type == WorkspaceType.PERSONAL
            and resource.user_id == user.id
        )
        is_own_enterprise = (
            context.workspace_type == WorkspaceType.ENTERPRISE
            and resource.workspace_type == WorkspaceType.ENTERPRISE
            and resource.company_id == context.company_id
            and resource.user_id == user.id
        )
        if is_own_personal or is_own_enterprise:
            return
        self.data_access.check_access(user, resource, DataAccessAction.VIEW, context)

    def _scope_query(
        self, query: Query, model: type[T], user: User, context: WorkspaceContext
    ) -> Query:
        context.validate()
        if context.workspace_type == WorkspaceType.PERSONAL:
            return query.filter(
                model.workspace_type == WorkspaceType.PERSONAL, model.user_id == user.id
            )
        visibility = or_(
            model.user_id == user.id,
            model.access_level.in_([AccessLevel.COMPANY, AccessLevel.PUBLIC]),
            and_(
                model.access_level == AccessLevel.FACTORY,
                model.factory_id == context.factory_id,
            ),
        )
        return query.filter(
            model.workspace_type == WorkspaceType.ENTERPRISE,
            model.company_id == context.company_id,
            visibility,
        )

    def create_batch(
        self, data: ImportBatchCreate, user: User, context: WorkspaceContext
    ) -> ImportBatch:
        batch = ImportBatch(
            id=str(uuid4()),
            name=data.name,
            source_type=data.source_type,
            target_entity_type=data.target_entity_type,
            **self._workspace_values(user, context, data.access_level),
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def list_batches(
        self, user: User, context: WorkspaceContext, skip: int = 0, limit: int = 50
    ) -> list[ImportBatch]:
        query = self._scope_query(
            self.db.query(ImportBatch), ImportBatch, user, context
        )
        candidates = query.order_by(ImportBatch.created_at.desc()).all()
        accessible: list[ImportBatch] = []
        for batch in candidates:
            try:
                self._check_view(batch, user, context)
            except HTTPException:
                continue
            accessible.append(batch)
        return accessible[skip : skip + limit]

    def get_batch(
        self, batch_id: str, user: User, context: WorkspaceContext
    ) -> ImportBatch:
        batch = self.db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
        if batch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导入批次不存在")
        self._check_view(batch, user, context)
        return batch

    def get_batch_documents(
        self, batch: ImportBatch, user: User, context: WorkspaceContext
    ) -> list[SourceDocument]:
        query = self._scope_query(
            self.db.query(SourceDocument), SourceDocument, user, context
        )
        return (
            query.filter(SourceDocument.batch_id == batch.id)
            .order_by(SourceDocument.created_at)
            .all()
        )

    def register_document(
        self,
        batch_id: str,
        data: SourceDocumentRegister,
        user: User,
        context: WorkspaceContext,
    ) -> SourceDocument:
        batch = self.get_batch(batch_id, user, context)
        if batch.status not in {"draft", "failed"}:
            raise HTTPException(status_code=409, detail="当前批次状态不允许添加文档")

        duplicate_query = self._scope_query(
            self.db.query(SourceDocument), SourceDocument, user, context
        ).filter(SourceDocument.sha256 == data.sha256.lower())
        duplicate = duplicate_query.first()
        if duplicate:
            raise HTTPException(
                status_code=409,
                detail={"message": "该文件已登记", "existing_document_id": duplicate.id},
            )

        document = SourceDocument(
            id=str(uuid4()),
            batch_id=batch.id,
            original_filename=data.original_filename,
            storage_key=data.storage_key,
            sha256=data.sha256.lower(),
            mime_type=data.mime_type,
            size_bytes=data.size_bytes,
            document_type=data.document_type,
            document_version=data.document_version,
            metadata_json=data.metadata,
            status="stored" if data.storage_key else "registered",
            **self._workspace_values(user, context, batch.access_level),
        )
        workspace = self._workspace_values(user, context, batch.access_level)
        original_artifact = DocumentArtifact(
            id=str(uuid4()),
            document_id=document.id,
            artifact_type="original",
            storage_key=data.storage_key,
            mime_type=data.mime_type,
            size_bytes=data.size_bytes,
            sha256=data.sha256.lower(),
            retention_class="original",
            expires_at=artifact_expiry("original"),
            metadata_json={"filename": data.original_filename},
            **workspace,
        )
        batch.total_documents = (batch.total_documents or 0) + 1
        self.db.add(document)
        self.db.add(original_artifact)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_document(
        self, document_id: str, user: User, context: WorkspaceContext
    ) -> SourceDocument:
        document = (
            self.db.query(SourceDocument)
            .filter(SourceDocument.id == document_id)
            .first()
        )
        if document is None:
            raise HTTPException(status_code=404, detail="原始文档不存在")
        self._check_view(document, user, context)
        return document

    def get_document_pages(
        self, document_id: str, user: User, context: WorkspaceContext
    ) -> list[DocumentPage]:
        document = self.get_document(document_id, user, context)
        return (
            self.db.query(DocumentPage)
            .filter(DocumentPage.document_id == document.id)
            .order_by(DocumentPage.page_number)
            .all()
        )

    def get_document_artifacts(
        self, document_id: str, user: User, context: WorkspaceContext
    ) -> list[DocumentArtifact]:
        document = self.get_document(document_id, user, context)
        return (
            self.db.query(DocumentArtifact)
            .filter(DocumentArtifact.document_id == document.id)
            .order_by(DocumentArtifact.created_at, DocumentArtifact.id)
            .all()
        )

    def parse_document(
        self,
        document_id: str,
        user: User,
        context: WorkspaceContext,
        storage: DocumentStorage,
        parser: DocumentParser,
    ) -> tuple[SourceDocument, list[DocumentPage]]:
        """Parse an original into replaceable staging pages without publishing data."""
        document = self.get_document(document_id, user, context)
        if not document.storage_key:
            raise HTTPException(status_code=409, detail="该记录没有可解析的私有原件")
        if document.status == "parsing":
            raise HTTPException(status_code=409, detail="文档正在解析，请勿重复提交")

        document.status = "parsing"
        self.db.commit()
        try:
            with storage.open_stream(document.storage_key) as stream:
                parsed = parser.parse(
                    stream, document.original_filename, document.mime_type
                )
            if not parsed.pages:
                raise DocumentParseError("文档中没有可解析的页面")
        except (DocumentParseError, DocumentUploadError) as exc:
            self.db.rollback()
            document.status = "failed"
            document.metadata_json = {
                **(document.metadata_json or {}),
                "parsing": {"status": "failed", "message": str(exc)},
            }
            self.db.commit()
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            self.db.rollback()
            document.status = "failed"
            document.metadata_json = {
                **(document.metadata_json or {}),
                "parsing": {"status": "failed", "message": "文档解析失败"},
            }
            self.db.commit()
            raise HTTPException(status_code=500, detail="文档解析失败") from exc

        workspace = {
            "user_id": document.user_id,
            "workspace_type": document.workspace_type,
            "company_id": document.company_id,
            "factory_id": document.factory_id,
            "access_level": document.access_level,
        }
        try:
            self.db.query(DocumentPage).filter(
                DocumentPage.document_id == document.id
            ).delete(synchronize_session=False)
            pages = [
                DocumentPage(
                    id=str(uuid4()),
                    document_id=document.id,
                    page_number=item.page_number,
                    text_content=item.text_content,
                    ocr_status=item.ocr_status,
                    page_metadata=item.metadata,
                    **workspace,
                )
                for item in parsed.pages
            ]
            text_artifacts = [
                DocumentArtifact(
                    id=str(uuid4()),
                    document_id=document.id,
                    artifact_type="ocr_text",
                    reference_id=page.id,
                    mime_type="text/plain; charset=utf-8",
                    size_bytes=len((page.text_content or "").encode("utf-8")),
                    retention_class="evidence",
                    expires_at=artifact_expiry("evidence"),
                    metadata_json={
                        "page_number": page.page_number,
                        "source": (
                            "ocr" if page.ocr_status == "completed" else "native_text"
                        ),
                    },
                    **workspace,
                )
                for page in pages
                if page.text_content
            ]
            # Keep prior evidence immutable across reparses; a newer created_at marks
            # the current rendition while old review evidence remains auditable.
            self.db.add_all([*pages, *text_artifacts])
            document.page_count = len(pages)
            document.status = "ready"
            document.metadata_json = {
                **(document.metadata_json or {}),
                "parsing": {
                    "status": "completed",
                    "parser": parsed.parser,
                    "page_numbering": parsed.page_numbering,
                    "parsed_at": datetime.now(timezone.utc).isoformat(),
                },
            }
            self.db.commit()
            self.db.refresh(document)
            return document, pages
        except Exception:
            self.db.rollback()
            document.status = "failed"
            document.metadata_json = {
                **(document.metadata_json or {}),
                "parsing": {"status": "failed", "message": "页面记录保存失败"},
            }
            self.db.commit()
            raise

    def create_manual_draft(
        self,
        document_id: str,
        data: ManualDraftCreate,
        user: User,
        context: WorkspaceContext,
    ) -> ExtractedEntity:
        document = self.get_document(document_id, user, context)
        batch = self.get_batch(document.batch_id, user, context)
        if data.entity_type != batch.target_entity_type:
            raise HTTPException(status_code=422, detail="草稿类型与导入批次目标类型不一致")

        workspace = self._workspace_values(user, context, document.access_level)
        now = datetime.utcnow()
        previous = (
            self._scope_query(
                self.db.query(ExtractedEntity), ExtractedEntity, user, context
            )
            .filter(
                ExtractedEntity.document_id == document.id,
                ExtractedEntity.is_current.is_(True),
            )
            .order_by(ExtractedEntity.version.desc())
            .first()
        )
        version = 1
        if previous is not None:
            previous.is_current = False
            version = (previous.version or 1) + 1
        job = ExtractionJob(
            id=str(uuid4()),
            document_id=document.id,
            mode="manual",
            schema_version=data.schema_version,
            schema_snapshot=data.schema_snapshot,
            status="completed",
            started_at=now,
            completed_at=now,
            **workspace,
        )
        entity = ExtractedEntity(
            id=str(uuid4()),
            document_id=document.id,
            job_id=job.id,
            entity_type=data.entity_type,
            source_mode="manual",
            status="draft",
            draft_data=data.draft_data,
            version=version,
            **workspace,
        )
        self.db.add_all([job, entity])
        for item in data.fields:
            field = ExtractedField(
                id=str(uuid4()),
                entity_id=entity.id,
                module_id=item.module_id,
                instance_id=item.instance_id,
                field_id=item.field_id,
                field_key=item.field_key,
                canonical_field_key=item.canonical_field_key,
                raw_value=item.value,
                normalized_value=item.value,
                confidence=1.0,
                review_status="accepted",
                schema_version=data.schema_version,
                **workspace,
            )
            self.db.add(field)
            for evidence in item.evidence:
                self.db.add(
                    FieldEvidence(
                        id=str(uuid4()),
                        extracted_field_id=field.id,
                        page_number=evidence.page_number,
                        evidence_type="manual",
                        text_excerpt=evidence.text,
                        bbox=evidence.bbox,
                        **workspace,
                    )
                )
        document.status = "ready"
        batch.status = "review"
        if previous is None:
            batch.processed_documents = min(
                batch.total_documents, (batch.processed_documents or 0) + 1
            )
        batch.progress = int(
            batch.processed_documents * 100 / max(batch.total_documents, 1)
        )
        self.db.commit()
        self.db.refresh(entity)
        return entity

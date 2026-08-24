"""Field review and controlled publication of smart-import drafts."""
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.data_access import WorkspaceContext, WorkspaceType
from app.models.smart_import import (
    EntityPublishRecord,
    ExtractedEntity,
    ExtractedField,
    ExtractionJob,
    ImportReviewRecord,
    SourceDocument,
)
from app.models.user import User
from app.schemas.pqr import PQRCreate
from app.schemas.qualification import WPSPQRSupportCreate
from app.schemas.smart_import import (
    BulkFieldAcceptRequest,
    FieldReviewRequest,
    FormPublishRequest,
)
from app.schemas.wps import WPSCreate
from app.domain.semantic_field_mapping import (
    SemanticMappingConflict,
    assign_semantic_value,
    fixed_to_modules_data,
    modules_data_to_fixed,
)
from app.services.membership_service import MembershipService
from app.services.pqr_service import PQRService
from app.services.qualification_service import QualificationService
from app.services.smart_import_service import SmartImportService
from app.services.smart_import_template_service import SmartImportTemplateService
from app.services.wps_service import WPSService


class SmartImportReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.smart_import = SmartImportService(db)

    def get_entity(
        self, entity_id: str, user: User, context: WorkspaceContext
    ) -> ExtractedEntity:
        entity = (
            self.smart_import._scope_query(
                self.db.query(ExtractedEntity), ExtractedEntity, user, context
            )
            .filter(ExtractedEntity.id == entity_id)
            .first()
        )
        if entity is None:
            raise HTTPException(status_code=404, detail="提取草稿不存在或无权访问")
        self.smart_import._check_view(entity, user, context)
        return entity

    def review_field(
        self,
        entity_id: str,
        field_id: str,
        request: FieldReviewRequest,
        user: User,
        context: WorkspaceContext,
    ) -> ExtractedEntity:
        entity = self.get_entity(entity_id, user, context)
        self._ensure_editable(entity)
        field = (
            self.db.query(ExtractedField)
            .filter(
                ExtractedField.id == field_id,
                ExtractedField.entity_id == entity.id,
            )
            .first()
        )
        if field is None:
            raise HTTPException(status_code=404, detail="识别字段不存在")
        if request.action == "correct" and request.value is None:
            raise HTTPException(status_code=422, detail="修正字段必须提供新值")

        previous = field.normalized_value
        if request.action == "accept":
            field.review_status = "accepted"
            new_value = previous
        elif request.action == "correct":
            field.normalized_value = request.value
            field.review_status = "corrected"
            entity.source_mode = "mixed"
            new_value = request.value
        else:
            field.review_status = "rejected"
            new_value = None
        self._update_draft(entity, field, new_value, request.action == "reject")
        self.db.add(
            self._review_record(
                entity,
                field,
                request.action,
                previous,
                new_value,
                request.reason,
                user,
            )
        )
        self._refresh_entity_status(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def bulk_accept(
        self,
        entity_id: str,
        request: BulkFieldAcceptRequest,
        user: User,
        context: WorkspaceContext,
    ) -> ExtractedEntity:
        entity = self.get_entity(entity_id, user, context)
        self._ensure_editable(entity)
        query = self.db.query(ExtractedField).filter(
            ExtractedField.entity_id == entity.id,
            ExtractedField.review_status == "pending",
        )
        if request.field_ids:
            query = query.filter(ExtractedField.id.in_(request.field_ids))
        if request.minimum_confidence is not None:
            query = query.filter(
                ExtractedField.confidence >= request.minimum_confidence
            )
        fields = query.all()
        if not fields:
            raise HTTPException(status_code=422, detail="没有符合条件的待审核字段")
        for field in fields:
            field.review_status = "accepted"
            self.db.add(
                self._review_record(
                    entity,
                    field,
                    "accept",
                    field.normalized_value,
                    field.normalized_value,
                    "批量接受",
                    user,
                )
            )
        self._refresh_entity_status(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def publish(
        self, entity_id: str, user: User, context: WorkspaceContext
    ) -> EntityPublishRecord:
        entity = self.get_entity(entity_id, user, context)
        existing = (
            self.db.query(EntityPublishRecord)
            .filter(EntityPublishRecord.entity_id == entity.id)
            .order_by(EntityPublishRecord.created_at.desc())
            .first()
        )
        if existing and existing.target_entity_id != "pending":
            return existing
        if entity.entity_type not in {"wps", "pqr"}:
            raise HTTPException(status_code=422, detail="当前仅支持发布 WPS 和 PQR")
        if entity.entity_type == "wps":
            raise HTTPException(
                status_code=409,
                detail="WPS 必须进入现有表单并人工确认支持 PQR 后发布",
            )
        fields = (
            self.db.query(ExtractedField)
            .filter(ExtractedField.entity_id == entity.id)
            .all()
        )
        pending = [field for field in fields if field.review_status == "pending"]
        if pending:
            raise HTTPException(status_code=409, detail=f"仍有 {len(pending)} 个字段未审核")
        accepted = [
            field
            for field in fields
            if field.review_status in {"accepted", "corrected"}
        ]
        if not accepted:
            raise HTTPException(status_code=422, detail="没有可发布的已确认字段")

        job = (
            self.db.query(ExtractionJob)
            .filter(ExtractionJob.id == entity.job_id)
            .first()
        )
        payload = self._build_payload(entity, accepted, job)
        obj_in = self._validate_payload(entity.entity_type, payload)
        self._check_formal_quota(entity.entity_type, user, context)
        workspace = self._workspace(entity)
        record = existing or EntityPublishRecord(
            id=str(uuid4()),
            entity_id=entity.id,
            target_entity_type=entity.entity_type,
            target_entity_id="pending",
            published_snapshot=obj_in.model_dump(mode="json"),
            published_by=user.id,
            **workspace,
        )
        if existing is None:
            self.db.add(record)
        self.db.flush()
        try:
            if entity.entity_type == "wps":
                target = WPSService(self.db).create(
                    self.db,
                    obj_in=obj_in,
                    current_user=user,
                    workspace_context=context,
                )
            else:
                target = PQRService(self.db).create(
                    self.db,
                    obj_in=obj_in,
                    current_user=user,
                    workspace_context=context,
                )
        except ValueError as exc:
            self.db.rollback()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        record.target_entity_id = str(target.id)
        entity.status = "published"
        self.db.add(
            self._review_record(
                entity,
                None,
                "approve",
                None,
                {
                    "target_entity_type": entity.entity_type,
                    "target_entity_id": target.id,
                },
                "发布到现有业务模块，正式记录状态保持草稿",
                user,
            )
        )
        document = (
            self.db.query(SourceDocument)
            .filter(SourceDocument.id == entity.document_id)
            .first()
        )
        if document is not None:
            batch = self.smart_import.get_batch(document.batch_id, user, context)
            if (batch.processed_documents or 0) >= (batch.total_documents or 0):
                batch.status = "completed"
                batch.progress = 100
        self.db.commit()
        self._increment_formal_quota(entity.entity_type, user, context)
        self.db.refresh(record)
        return record

    def publish_form(
        self,
        entity_id: str,
        request: FormPublishRequest,
        user: User,
        context: WorkspaceContext,
    ) -> EntityPublishRecord:
        """Publish a complete human-reviewed existing form through the domain Service."""
        entity = self.get_entity(entity_id, user, context)
        self._ensure_editable(entity)
        if entity.entity_type not in {"wps", "pqr"}:
            raise HTTPException(status_code=422, detail="当前仅支持 WPS 和 PQR 表单校核")
        existing = (
            self.db.query(EntityPublishRecord)
            .filter(EntityPublishRecord.entity_id == entity.id)
            .order_by(EntityPublishRecord.created_at.desc())
            .first()
        )
        if existing and existing.target_entity_id != "pending":
            return existing

        payload = dict(request.payload)
        payload["status"] = "draft"
        matched_pqr_id = None
        if entity.entity_type == "wps":
            if request.supporting_pqr_decision not in {"matched", "no_match"}:
                raise HTTPException(status_code=422, detail="请明确确认支持 PQR 或选择暂无匹配")
            match = None
            if request.supporting_pqr_decision == "matched":
                candidates = SmartImportTemplateService(self.db).match_supporting_pqrs(
                    entity, user, context
                )
                match = next(
                    (
                        item
                        for item in candidates
                        if item["pqr_id"] == request.supporting_pqr_id
                        and item["eligible"]
                    ),
                    None,
                )
                if match is None:
                    raise HTTPException(
                        status_code=422,
                        detail="所选 PQR 不可访问、未批准或不在当前匹配候选中",
                    )
                payload["wpqr_number"] = match["pqr_number"]
                matched_pqr_id = match["pqr_id"]
            modules = dict(payload.get("modules_data") or {})
            modules["_import_control"] = {
                "moduleId": "_import_control",
                "data": {
                    "supporting_pqr_decision": request.supporting_pqr_decision,
                    "supporting_pqr_id": match["pqr_id"] if match else None,
                    "supporting_pqr_number": match["pqr_number"] if match else None,
                    "capability_eligible": bool(match),
                },
            }
            payload["modules_data"] = modules
            entity.draft_data = {
                **(entity.draft_data or {}),
                "_supporting_pqr_match": modules["_import_control"]["data"],
            }

        obj_in = self._validate_payload(entity.entity_type, payload)
        self._check_formal_quota(entity.entity_type, user, context)
        record = existing or EntityPublishRecord(
            id=str(uuid4()),
            entity_id=entity.id,
            target_entity_type=entity.entity_type,
            target_entity_id="pending",
            published_snapshot=obj_in.model_dump(mode="json"),
            published_by=user.id,
            **self._workspace(entity),
        )
        if existing is None:
            self.db.add(record)
        fields = (
            self.db.query(ExtractedField)
            .filter(ExtractedField.entity_id == entity.id)
            .all()
        )
        for field in fields:
            if field.review_status == "pending":
                field.review_status = "accepted"
        self.db.add(
            self._review_record(
                entity,
                None,
                "submit",
                entity.draft_data,
                obj_in.model_dump(mode="json"),
                "使用现有动态表单完成人工校核",
                user,
            )
        )
        self.db.flush()
        try:
            if entity.entity_type == "wps":
                target = WPSService(self.db).create(
                    self.db,
                    obj_in=obj_in,
                    current_user=user,
                    workspace_context=context,
                )
            else:
                target = PQRService(self.db).create(
                    self.db,
                    obj_in=obj_in,
                    current_user=user,
                    workspace_context=context,
                )
        except ValueError as exc:
            self.db.rollback()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        record.target_entity_id = str(target.id)
        if entity.entity_type == "wps" and matched_pqr_id is not None:
            QualificationService(self.db).create_support_link(
                target.id,
                WPSPQRSupportCreate(
                    pqr_id=matched_pqr_id,
                    source="smart_import",
                    confirmation_status="pending",
                    confirmation_note="智能导入表单中选择，待绑定明确合格的资格计算结果后人工确认",
                ),
                user,
                context,
            )
        entity.status = "published"
        self.db.add(
            self._review_record(
                entity,
                None,
                "approve",
                None,
                {
                    "target_entity_type": entity.entity_type,
                    "target_entity_id": target.id,
                },
                "表单校核后发布到现有 Service，正式记录保持草稿",
                user,
            )
        )
        self.db.commit()
        self._increment_formal_quota(entity.entity_type, user, context)
        self.db.refresh(record)
        return record

    def _build_payload(
        self,
        entity: ExtractedEntity,
        fields: list[ExtractedField],
        job: ExtractionJob | None,
    ) -> dict[str, Any]:
        model_fields = (
            WPSCreate.model_fields
            if entity.entity_type == "wps"
            else PQRCreate.model_fields
        )
        payload: dict[str, Any] = {"status": "draft"}
        modules: dict[str, Any] = {}
        accepted_by_key: dict[str, Any] = {}
        for field in fields:
            value = field.normalized_value
            if value not in (None, "", []):
                accepted_by_key.setdefault(field.field_key, value)
            if field.field_key in model_fields:
                if field.field_key in payload and payload[field.field_key] != value:
                    raise HTTPException(
                        status_code=409,
                        detail=f"字段 {field.field_key} 存在多个已确认值，请先解决冲突",
                    )
                payload[field.field_key] = value
            try:
                assign_semantic_value(
                    entity.entity_type,
                    payload,
                    field.canonical_field_key,
                    value,
                )
            except SemanticMappingConflict as exc:
                raise HTTPException(
                    status_code=409,
                    detail=f"字段 {exc.args[0]} 存在多个已确认值，请先解决冲突",
                ) from exc
            instance_id = field.instance_id or field.module_id or "imported_fields"
            module = modules.setdefault(
                instance_id,
                {"moduleId": field.module_id or "imported_fields", "data": {}},
            )
            module["data"][field.field_key] = value
        accepted_binding_keys = {
            (
                field.instance_id,
                field.module_id,
                field.field_key,
            )
            for field in fields
        }
        all_bindings = (
            (job.schema_snapshot or {}).get("field_bindings", []) if job else []
        )
        bindings = [
            binding
            for binding in all_bindings
            if (
                binding.get("instance_id"),
                binding.get("module_id"),
                binding.get("field_key"),
            )
            in accepted_binding_keys
        ]
        try:
            payload = modules_data_to_fixed(
                entity.entity_type,
                modules,
                bindings,
                payload,
            )
        except SemanticMappingConflict as exc:
            raise HTTPException(
                status_code=409,
                detail=f"字段 {exc.args[0]} 存在多个已确认值，请先解决冲突",
            ) from exc
        modules = fixed_to_modules_data(
            entity.entity_type,
            payload,
            modules,
            bindings,
        )
        payload["modules_data"] = modules
        if job and job.template_id:
            payload["template_id"] = job.template_id
        # Providers and legacy templates often use a document-level
        # `report_number` instead of the formal PQR field name. Once the user
        # has explicitly accepted that field it is safe to use as a published
        # draft identifier. Keep the original field in modules_data for trace.
        if entity.entity_type == "pqr" and not payload.get("pqr_number"):
            payload["pqr_number"] = next(
                (
                    accepted_by_key.get(key)
                    for key in (
                        "report_number",
                        "procedure_qualification_record_number",
                        "qualification_record_number",
                    )
                    if accepted_by_key.get(key)
                ),
                None,
            )
        if not payload.get("title"):
            explicit_title = next(
                (
                    accepted_by_key.get(key)
                    for key in ("document_title", "report_title", "product_name")
                    if accepted_by_key.get(key)
                ),
                None,
            )
            number = payload.get("pqr_number") or payload.get("wps_number")
            payload["title"] = explicit_title or (
                f"{entity.entity_type.upper()} {number}" if number else None
            )
        required = "wps_number" if entity.entity_type == "wps" else "pqr_number"
        missing = [key for key in (required, "title") if not payload.get(key)]
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"发布前必须确认字段：{', '.join(missing)}",
            )
        return payload

    @staticmethod
    def _validate_payload(entity_type: str, payload: dict[str, Any]) -> Any:
        try:
            return (
                WPSCreate(**payload) if entity_type == "wps" else PQRCreate(**payload)
            )
        except ValidationError as exc:
            errors = ", ".join(
                ".".join(str(part) for part in item["loc"]) for item in exc.errors()[:5]
            )
            raise HTTPException(status_code=422, detail=f"正式表单校验失败：{errors}") from exc

    @staticmethod
    def _update_draft(
        entity: ExtractedEntity,
        field: ExtractedField,
        value: Any,
        remove: bool,
    ) -> None:
        data = dict(entity.draft_data or {})
        container = data
        if field.instance_id:
            container = dict(data.get(field.instance_id) or {})
            data[field.instance_id] = container
        if remove:
            container.pop(field.field_key, None)
        else:
            container[field.field_key] = value
        entity.draft_data = data

    def _refresh_entity_status(self, entity: ExtractedEntity) -> None:
        pending = (
            self.db.query(ExtractedField)
            .filter(
                ExtractedField.entity_id == entity.id,
                ExtractedField.review_status == "pending",
            )
            .count()
        )
        entity.status = "review" if pending == 0 else "draft"

    @staticmethod
    def _ensure_editable(entity: ExtractedEntity) -> None:
        if entity.status in {"published", "approved", "rejected"}:
            raise HTTPException(status_code=409, detail="当前草稿状态不允许继续修改")
        if not entity.is_current:
            raise HTTPException(status_code=409, detail="只能审核当前版本草稿")

    @staticmethod
    def _workspace(entity: ExtractedEntity) -> dict[str, Any]:
        return {
            "user_id": entity.user_id,
            "workspace_type": entity.workspace_type,
            "company_id": entity.company_id,
            "factory_id": entity.factory_id,
            "access_level": entity.access_level,
        }

    def _review_record(
        self,
        entity: ExtractedEntity,
        field: ExtractedField | None,
        action: str,
        previous: Any,
        new: Any,
        reason: str | None,
        user: User,
    ) -> ImportReviewRecord:
        return ImportReviewRecord(
            id=str(uuid4()),
            entity_id=entity.id,
            extracted_field_id=field.id if field else None,
            action=action,
            previous_value=previous,
            new_value=new,
            reason=reason,
            reviewer_id=user.id,
            **self._workspace(entity),
        )

    def _check_formal_quota(
        self, entity_type: str, user: User, context: WorkspaceContext
    ) -> None:
        if context.workspace_type != WorkspaceType.PERSONAL:
            return
        service = MembershipService(self.db)
        if not service.check_quota_available(user, entity_type):
            limits = service.get_membership_limits(user.member_tier)
            raise HTTPException(
                status_code=403,
                detail=f"已达到{entity_type.upper()}配额限制 ({limits[entity_type]}个)",
            )

    def _increment_formal_quota(
        self, entity_type: str, user: User, context: WorkspaceContext
    ) -> None:
        if context.workspace_type == WorkspaceType.PERSONAL:
            MembershipService(self.db).update_quota_usage(user, entity_type, 1)

"""Review and publish welder/certification imports through the existing domain service."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.data_access import WorkspaceContext
from app.models.smart_import import (
    EntityPublishRecord,
    ExtractedEntity,
    ExtractedField,
    ImportReviewRecord,
)
from app.models.user import User
from app.models.welder import Welder, WelderCertification, WelderCertifiedProject
from app.services.smart_import_review_service import SmartImportReviewService
from app.services.welder_service import WelderService


def _date_value(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip().replace("/", "-")
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        for pattern in ("%Y-%m-%d", "%Y-%m", "%Y年%m月%d日"):
            try:
                return datetime.strptime(text, pattern).date()
            except ValueError:
                continue
    return None


def _expiry_status(value: Any) -> str:
    expiry = _date_value(value)
    if expiry is None:
        return "valid"
    if expiry < date.today():
        return "expired"
    if expiry <= date.today() + timedelta(days=30):
        return "expiring_soon"
    return "valid"


class WelderImportService:
    def __init__(self, db: Session):
        self.db = db
        self.review_service = SmartImportReviewService(db)
        self.welder_service = WelderService(db)

    def review(
        self, entity_id: str, user: User, context: WorkspaceContext
    ) -> dict[str, Any]:
        entity = self.review_service.get_entity(entity_id, user, context)
        if entity.entity_type != "welder":
            raise HTTPException(status_code=422, detail="当前草稿不是焊工资质数据")
        rows = self._records(entity)
        if not rows:
            raise HTTPException(status_code=422, detail="未识别到可导入的焊工或证书记录")
        reviewed = []
        for row in rows:
            row["_source_document_id"] = entity.document_id
            reviewed.append(self._review_record(row, context))
        return {
            "entity_id": entity.id,
            "records": reviewed,
        }

    def publish(
        self,
        entity_id: str,
        decisions: list[dict[str, Any]],
        user: User,
        context: WorkspaceContext,
    ) -> EntityPublishRecord:
        entity = self.review_service.get_entity(entity_id, user, context)
        if entity.entity_type != "welder":
            raise HTTPException(status_code=422, detail="当前草稿不是焊工资质数据")
        existing_publish = (
            self.db.query(EntityPublishRecord)
            .filter(EntityPublishRecord.entity_id == entity.id)
            .order_by(EntityPublishRecord.created_at.desc())
            .first()
        )
        if existing_publish and existing_publish.target_entity_id != "pending":
            return existing_publish

        by_key = {str(item.get("record_key")): item for item in decisions}
        reviewed = self.review(entity_id, user, context)["records"]
        created_ids: list[int] = []
        results: list[dict[str, Any]] = []
        resolved_welders: dict[str, Welder] = {}
        for item in reviewed:
            decision = by_key.get(item["record_key"], {})
            if item["identity_status"] == "ambiguous" and not decision:
                raise HTTPException(
                    status_code=409, detail=f"{item['full_name']} 存在重名，请先确认对应焊工"
                )
            if item["certificate_status"] == "conflict":
                raise HTTPException(
                    status_code=409, detail=f"证书 {item['certification_number']} 已属于其他焊工"
                )
            if not item.get("certification_number") or not item.get(
                "certification_type"
            ):
                raise HTTPException(
                    status_code=422, detail=f"{item['full_name']} 缺少证书编号或证书类型"
                )
            if item["certificate_status"] == "duplicate" and not decision.get(
                "skip_duplicate"
            ):
                raise HTTPException(
                    status_code=409,
                    detail=f"证书 {item['certification_number']} 已存在，请确认跳过",
                )

            identity_key = (
                f"code:{item['welder_code']}"
                if item.get("welder_code")
                else f"id:{item['id_number']}"
                if item.get("id_number")
                else ""
            )
            welder = resolved_welders.get(identity_key) if identity_key else None
            if welder is None:
                welder = self._resolve_welder(item, decision, user, context)
                if identity_key:
                    resolved_welders[identity_key] = welder
            if item.get("existing_certification_id"):
                owner_id = (
                    self.db.query(WelderCertification.welder_id)
                    .filter(WelderCertification.id == item["existing_certification_id"])
                    .scalar()
                )
                if owner_id is not None and owner_id != welder.id:
                    raise HTTPException(
                        status_code=409,
                        detail=f"证书 {item['certification_number']} 与所选焊工不一致",
                    )
            if welder.id not in created_ids:
                created_ids.append(welder.id)
            if item["certificate_status"] == "duplicate":
                results.append(
                    {"welder_id": welder.id, "certificate": "skipped_duplicate"}
                )
                continue
            cert_id = self._publish_certificate(welder, item, user, context)
            results.append({"welder_id": welder.id, "certification_id": cert_id})

        if not created_ids:
            raise HTTPException(status_code=422, detail="没有可发布的焊工记录")
        workspace = self.review_service._workspace(entity)
        record = existing_publish or EntityPublishRecord(
            id=str(uuid4()),
            entity_id=entity.id,
            target_entity_type="welder",
            target_entity_id=str(created_ids[0]),
            published_snapshot={"welder_ids": created_ids, "results": results},
            published_by=user.id,
            **workspace,
        )
        record.target_entity_id = str(created_ids[0])
        record.published_snapshot = {"welder_ids": created_ids, "results": results}
        if existing_publish is None:
            self.db.add(record)
        entity.status = "published"
        self.db.add(
            ImportReviewRecord(
                id=str(uuid4()),
                entity_id=entity.id,
                action="approve",
                previous_value=None,
                new_value=record.published_snapshot,
                reason="经身份与证书冲突校验后发布到现有焊工 Service",
                reviewer_id=user.id,
                **workspace,
            )
        )
        self.db.commit()
        self.db.refresh(record)
        return record

    def _records(self, entity: ExtractedEntity) -> list[dict[str, Any]]:
        values: dict[str, Any] = dict(entity.draft_data or {})
        fields = (
            self.db.query(ExtractedField)
            .filter(ExtractedField.entity_id == entity.id)
            .all()
        )
        for field in fields:
            if field.review_status != "rejected":
                values[field.field_key] = field.normalized_value
        roster = values.get("welder_records")
        source = roster if isinstance(roster, list) and roster else [values]
        grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
        for index, raw in enumerate(source):
            if not isinstance(raw, dict):
                continue
            row = {**values, **raw}
            row.pop("welder_records", None)
            key = (
                str(
                    row.get("welder_code")
                    or row.get("id_number")
                    or row.get("full_name")
                    or index
                ),
                str(row.get("certification_number") or index),
                str(row.get("certification_type") or ""),
            )
            target = grouped.setdefault(key, {**row, "qualified_projects": []})
            projects = raw.get("qualified_projects")
            if isinstance(projects, list):
                target["qualified_projects"].extend(
                    p for p in projects if isinstance(p, dict)
                )
            elif any(
                raw.get(k)
                for k in (
                    "welding_process",
                    "welding_position",
                    "material_group",
                    "thickness_range",
                    "diameter_range",
                    "project_code",
                    "project_name",
                )
            ):
                target["qualified_projects"].append(
                    {
                        key: raw.get(key)
                        for key in (
                            "project_code",
                            "project_name",
                            "welding_process",
                            "welding_position",
                            "material_group",
                            "thickness_range",
                            "diameter_range",
                            "issue_date",
                            "expiry_date",
                        )
                        if raw.get(key) is not None
                    }
                )
        return list(grouped.values())

    def _welder_query(self, context: WorkspaceContext):
        query = self.db.query(Welder).filter(Welder.is_active.is_(True))
        if context.is_personal():
            return query.filter(
                Welder.workspace_type == "personal", Welder.user_id == context.user_id
            )
        return query.filter(
            Welder.workspace_type == "enterprise",
            Welder.company_id == context.company_id,
        )

    def _review_record(
        self, row: dict[str, Any], context: WorkspaceContext
    ) -> dict[str, Any]:
        code = str(row.get("welder_code") or "").strip()
        id_number = str(row.get("id_number") or "").strip()
        name = str(row.get("full_name") or "").strip()
        query = self._welder_query(context)
        if code:
            candidates = query.filter(Welder.welder_code == code).all()
            matched_by = "welder_code"
        elif id_number:
            candidates = query.filter(Welder.id_number == id_number).all()
            matched_by = "id_number"
        else:
            candidates = query.filter(Welder.full_name == name).all() if name else []
            matched_by = "full_name" if candidates else None
        identity_status = "new"
        if candidates:
            identity_status = (
                "matched"
                if matched_by in {"welder_code", "id_number"} and len(candidates) == 1
                else "ambiguous"
            )

        cert_number = str(row.get("certification_number") or "").strip()
        cert = (
            self.db.query(WelderCertification)
            .filter(
                WelderCertification.certification_number == cert_number,
                WelderCertification.is_active.is_(True),
            )
            .first()
            if cert_number
            else None
        )
        certificate_status = "new"
        if cert:
            candidate_ids = {candidate.id for candidate in candidates}
            if cert.welder_id not in candidate_ids:
                certificate_status = "conflict"
            else:
                incoming_expiry = _date_value(row.get("expiry_date"))
                certificate_status = (
                    "renewal"
                    if incoming_expiry
                    and (not cert.expiry_date or incoming_expiry > cert.expiry_date)
                    else "duplicate"
                )
        projects = (
            row.get("qualified_projects")
            if isinstance(row.get("qualified_projects"), list)
            else []
        )
        if not projects:
            projects = [
                {
                    "project_name": row.get("project_name")
                    or row.get("certification_type")
                    or "持证项目",
                    "issue_date": row.get("issue_date"),
                    "expiry_date": row.get("expiry_date"),
                }
            ]
        normalized_projects = []
        for project in projects:
            project = dict(project)
            project["project_name"] = project.get("project_name") or self._project_name(
                project
            )
            project["issue_date"] = project.get("issue_date") or row.get("issue_date")
            project["expiry_date"] = project.get("expiry_date") or row.get(
                "expiry_date"
            )
            project["status"] = _expiry_status(project.get("expiry_date"))
            normalized_projects.append(project)
        record_key = f"{code or id_number or name}:{cert_number}"
        return {
            **row,
            "record_key": record_key,
            "full_name": name,
            "welder_code": code,
            "id_number": id_number,
            "certification_number": cert_number,
            "identity_status": identity_status,
            "matched_by": matched_by,
            "candidates": [
                {
                    "id": item.id,
                    "welder_code": item.welder_code,
                    "full_name": item.full_name,
                    "id_number": item.id_number,
                }
                for item in candidates
            ],
            "certificate_status": certificate_status,
            "existing_certification_id": cert.id if cert else None,
            "expiry_status": _expiry_status(row.get("expiry_date")),
            "qualified_projects": normalized_projects,
        }

    @staticmethod
    def _project_name(project: dict[str, Any]) -> str:
        parts = [
            project.get("welding_process"),
            project.get("welding_position"),
            project.get("material_group"),
            project.get("thickness_range"),
            project.get("diameter_range"),
        ]
        return " / ".join(str(part) for part in parts if part) or "持证项目"

    def _resolve_welder(
        self,
        item: dict[str, Any],
        decision: dict[str, Any],
        user: User,
        context: WorkspaceContext,
    ) -> Welder:
        selected = decision.get("existing_welder_id")
        if selected:
            return self.welder_service.get_welder_by_id(int(selected), user, context)
        if item["identity_status"] == "matched":
            return self.welder_service.get_welder_by_id(
                int(item["candidates"][0]["id"]), user, context
            )
        if item["identity_status"] == "ambiguous" and not decision.get("create_new"):
            raise HTTPException(
                status_code=409, detail=f"请为 {item['full_name']} 选择现有焊工或确认新建"
            )
        if not item.get("full_name"):
            raise HTTPException(status_code=422, detail="焊工姓名不能为空")
        code = (
            item.get("welder_code")
            or f"IMP-{datetime.utcnow():%Y%m%d%H%M%S}-{uuid4().hex[:6].upper()}"
        )
        return self.welder_service.create_welder(
            user,
            {
                "welder_code": code,
                "full_name": item["full_name"],
                "id_type": item.get("id_type"),
                "id_number": item.get("id_number") or None,
                "department": item.get("department"),
                "status": "active",
                "certification_status": item.get("expiry_status") or "valid",
            },
            context,
        )

    def _publish_certificate(
        self,
        welder: Welder,
        item: dict[str, Any],
        user: User,
        context: WorkspaceContext,
    ) -> int:
        projects = item["qualified_projects"]
        qualified_items = json.dumps(projects, ensure_ascii=False)
        payload = {
            key: item.get(key)
            for key in (
                "certification_number",
                "certification_type",
                "certification_level",
                "certification_standard",
                "certification_system",
                "issuing_authority",
                "issue_date",
                "expiry_date",
            )
        }
        payload.update(
            {
                "qualified_items": qualified_items,
                "status": item["expiry_status"],
                "project_name": projects[0]["project_name"],
            }
        )
        source_document_id = item.get("_source_document_id")
        if source_document_id:
            payload.update(
                {
                    "certificate_file_url": f"/api/v1/smart-import/documents/{source_document_id}/content",
                    "attachments": json.dumps(
                        {"smart_import_document_id": source_document_id},
                        ensure_ascii=False,
                    ),
                }
            )
        if item["certificate_status"] == "renewal":
            cert_id = int(item["existing_certification_id"])
            current = (
                self.db.query(WelderCertification)
                .filter(WelderCertification.id == cert_id)
                .first()
            )
            payload.update(
                {
                    "renewal_date": item.get("issue_date") or date.today(),
                    "renewal_count": (current.renewal_count or 0) + 1,
                    "renewal_result": "passed",
                }
            )
            self.welder_service.update_certification(
                welder.id, cert_id, payload, user, context
            )
            existing_projects = (
                self.db.query(WelderCertifiedProject)
                .filter(
                    WelderCertifiedProject.certification_id == cert_id,
                    WelderCertifiedProject.is_active.is_(True),
                )
                .all()
            )
            by_key = {
                (project.project_code or "", project.project_name): project
                for project in existing_projects
            }
            for project in projects:
                old = by_key.get(
                    (project.get("project_code") or "", project["project_name"])
                )
                if old:
                    self.welder_service.update_certified_project(
                        welder.id, cert_id, old.id, project, user, context
                    )
                else:
                    self.welder_service.add_certified_project(
                        welder.id, cert_id, project, user, context
                    )
            return cert_id
        created = self.welder_service.add_certification(
            welder.id, {**payload, **projects[0]}, user, context
        )
        cert_id = int(created["id"])
        for project in projects[1:]:
            self.welder_service.add_certified_project(
                welder.id, cert_id, project, user, context
            )
        return cert_id

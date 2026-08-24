"""Local review-workbench validation and unmapped-field binding."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.data_access import WorkspaceContext
from app.models.smart_import import (
    ExtractedEntity,
    ExtractedField,
    ExtractionJob,
    ImportReviewRecord,
)
from app.models.user import User
from app.models.pqr import PQR
from app.models.wps import WPS
from app.schemas.custom_module import CustomModuleCreate, CustomModuleUpdate
from app.schemas.smart_import import (
    ManualWorkbenchFieldCreate,
    UnmappedFieldBindRequest,
)
from app.services.custom_module_service import CustomModuleService
from app.services.smart_import_review_service import SmartImportReviewService


FIELD_LABELS_ZH = {
    "report_number": "报告编号",
    "pwps_number": "预焊接工艺规程编号",
    "preliminary_wps_number": "预焊接工艺规程编号",
    "preliminary_wps_date": "预焊接工艺规程日期",
    "company_name": "单位名称",
    "base_material_standard": "母材标准号",
    "weld_metal_thickness": "焊缝金属厚度",
    "filler_material_standard": "焊材标准",
    "filler_material_id": "焊材编号",
    "steel_identification": "钢材编号",
    "joint_position": "焊接位置",
    "welder_name": "焊工姓名",
    "welder_code": "焊工代号",
    "welding_date": "施焊日期",
    "qualification_standard": "评定标准",
    "max_heat_input": "最大线能量",
    "cleaning_method": "焊前及层间清理方法",
    "back_gouging_method": "背面清根方法",
    "single_or_multi_pass": "单道焊或多道焊",
    "single_or_multi_wire": "单丝焊或多丝焊",
    "environmental_conditions": "环境条件",
    "contact_tip_distance": "导电嘴至工件距离",
    "impact_test_report_number": "冲击试验报告编号",
    "groove_preparation": "坡口加工方法",
    "bend_test_report_number": "弯曲试验报告编号",
    "rt_report_number": "射线检测报告编号",
    "ndt_report_number": "无损检测报告编号",
    "charpy_energy_avg": "冲击吸收能量平均值",
    "charpy_energy_min": "冲击吸收能量最小值",
    "hardness_test_performed": "是否进行硬度试验",
}


def _display_field_label(field: ExtractedField, binding: dict[str, Any]) -> str:
    raw_value = field.raw_value if isinstance(field.raw_value, dict) else {}
    provider_label = str(raw_value.get("label") or "").strip()
    return (
        binding.get("label")
        or provider_label
        or FIELD_LABELS_ZH.get(str(field.field_key).casefold())
        or "其他识别字段"
    )


class SmartImportWorkbenchService:
    def __init__(self, db: Session):
        self.db = db
        self.review = SmartImportReviewService(db)

    def validate(
        self, entity_id: str, user: User, context: WorkspaceContext
    ) -> dict[str, Any]:
        entity = self.review.get_entity(entity_id, user, context)
        fields = (
            self.db.query(ExtractedField)
            .filter(ExtractedField.entity_id == entity.id)
            .all()
        )
        job = (
            self.db.query(ExtractionJob)
            .filter(ExtractionJob.id == entity.job_id)
            .first()
        )
        snapshot = job.schema_snapshot or {} if job else {}
        bindings = [
            {**binding, **self._schema_metadata(snapshot, binding)}
            for binding in snapshot.get("field_bindings", [])
        ]
        by_identity = {
            (binding.get("instance_id"), binding.get("field_key")): binding
            for binding in bindings
        }
        issues: list[dict[str, Any]] = []
        states: dict[str, dict[str, Any]] = {}
        active = [field for field in fields if field.review_status != "rejected"]

        for field in fields:
            confidence = field.confidence if field.confidence is not None else 0
            binding = by_identity.get((field.instance_id, field.field_key)) or {}
            states[field.id] = {
                "confidence_level": "high"
                if confidence >= 0.85
                else "medium"
                if confidence >= 0.6
                else "low",
                "conflicts": [],
                "is_unmapped": field.module_id == "unmapped",
                "label": _display_field_label(field, binding),
            }

        grouped: dict[tuple[str | None, str], list[ExtractedField]] = defaultdict(list)
        canonical: dict[str, list[ExtractedField]] = defaultdict(list)
        for field in active:
            grouped[(field.instance_id, field.field_key)].append(field)
            if field.canonical_field_key:
                canonical[field.canonical_field_key].append(field)
            binding = by_identity.get((field.instance_id, field.field_key)) or {}
            self._validate_value(field, binding, issues, states)

        for key, duplicates in grouped.items():
            if len(duplicates) > 1:
                binding = by_identity.get(key) or {}
                label = _display_field_label(duplicates[0], binding)
                self._issue(
                    issues,
                    states,
                    "duplicate_field",
                    "error",
                    [item.id for item in duplicates],
                    f"字段“{label}”出现多条待发布值",
                )
        for key, values in canonical.items():
            distinct = {
                json.dumps(
                    item.normalized_value,
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                )
                for item in values
            }
            if len(distinct) > 1:
                label = _display_field_label(values[0], {})
                self._issue(
                    issues,
                    states,
                    "semantic_conflict",
                    "error",
                    [item.id for item in values],
                    f"关联字段“{label}”的值不一致",
                )

        present = {
            (field.instance_id, field.field_key): field
            for field in active
            if field.normalized_value not in (None, "", [])
        }
        confirmed = [
            field
            for field in active
            if field.review_status in {"accepted", "corrected"}
            and field.normalized_value not in (None, "", [])
        ]
        confirmed_by_key = {field.field_key: field for field in confirmed}
        effective_number_field = None
        if entity.entity_type == "pqr":
            effective_number_field = next(
                (
                    confirmed_by_key.get(key)
                    for key in (
                        "pqr_number",
                        "report_number",
                        "procedure_qualification_record_number",
                        "qualification_record_number",
                    )
                    if confirmed_by_key.get(key)
                ),
                None,
            )
        elif entity.entity_type == "wps":
            effective_number_field = confirmed_by_key.get("wps_number")

        # Keep workbench validation consistent with the payload builder. A
        # confirmed legacy PQR report number becomes the formal PQR number,
        # and a draft title can be generated from that confirmed number.
        effective_required_keys = set(confirmed_by_key)
        if effective_number_field:
            effective_required_keys.add(
                "pqr_number" if entity.entity_type == "pqr" else "wps_number"
            )
        if (
            confirmed_by_key.get("title")
            or any(
                confirmed_by_key.get(key)
                for key in ("document_title", "report_title", "product_name")
            )
            or effective_number_field
        ):
            effective_required_keys.add("title")
        for binding in bindings:
            if (
                binding.get("required")
                and (binding.get("instance_id"), binding.get("field_key"))
                not in present
                and binding.get("field_key") not in effective_required_keys
            ):
                issues.append(
                    {
                        "code": "required_missing",
                        "severity": "error",
                        "field_ids": [],
                        "message": f"必填项未填写：{binding.get('label') or binding.get('field_key')}",
                    }
                )

        number_key = (
            "pqr_number"
            if entity.entity_type == "pqr"
            else "wps_number"
            if entity.entity_type == "wps"
            else None
        )
        if number_key:
            number_field = effective_number_field
            if number_field:
                model = PQR if entity.entity_type == "pqr" else WPS
                column = PQR.pqr_number if model is PQR else WPS.wps_number
                duplicate = (
                    self.review.smart_import._scope_query(
                        self.db.query(model), model, user, context
                    )
                    .filter(column == str(number_field.normalized_value))
                    .first()
                )
                if duplicate:
                    self._issue(
                        issues,
                        states,
                        "existing_record_duplicate",
                        "error",
                        [number_field.id],
                        f"正式库中已存在编号 {number_field.normalized_value}",
                    )

        pending = [field for field in fields if field.review_status == "pending"]
        for field in pending:
            states[field.id]["conflicts"].append("unconfirmed")
        unmapped = [field for field in active if field.module_id == "unmapped"]
        for field in unmapped:
            label = states[field.id]["label"]
            self._issue(
                issues,
                states,
                "unmapped",
                "warning" if field.review_status in {"accepted", "corrected"} else "error",
                [field.id],
                (
                    f"已确认的扩展字段将保存到导入模块：{label}"
                    if field.review_status in {"accepted", "corrected"}
                    else f"待归类字段尚未处理：{label}"
                ),
            )

        counts = {
            "required_missing": sum(
                item["code"] == "required_missing" for item in issues
            ),
            "duplicates": sum(
                item["code"] in {"duplicate_field", "existing_record_duplicate"}
                for item in issues
            ),
            "rule_conflicts": sum(
                item["code"]
                in {
                    "semantic_conflict",
                    "range_violation",
                    "option_violation",
                    "type_violation",
                }
                for item in issues
            ),
            "unconfirmed": len(pending),
            "unmapped": len(unmapped),
        }
        return {
            "entity_id": entity.id,
            "can_publish": not any(item["severity"] == "error" for item in issues)
            and not pending,
            "counts": counts,
            "issues": issues,
            "field_states": states,
            "binding_options": [
                {
                    "field_id": binding.get("field_id"),
                    "module_id": binding.get("module_id"),
                    "instance_id": binding.get("instance_id"),
                    "field_key": binding.get("field_key"),
                    "label": binding.get("label") or binding.get("field_key"),
                    "field_type": binding.get("field_type", "text"),
                    "ai_extract_mode": binding.get("ai_extract_mode", "auto"),
                    "extractable": bool(binding.get("extractable")),
                }
                for binding in bindings
                if binding.get("ai_extract_mode") != "derived"
            ],
        }

    def bind_unmapped(
        self,
        entity_id: str,
        field_id: str,
        request: UnmappedFieldBindRequest,
        user: User,
        context: WorkspaceContext,
    ) -> ExtractedEntity:
        entity = self.review.get_entity(entity_id, user, context)
        self.review._ensure_editable(entity)
        field = (
            self.db.query(ExtractedField)
            .filter(
                ExtractedField.id == field_id,
                ExtractedField.entity_id == entity.id,
            )
            .first()
        )
        if field is None or field.module_id != "unmapped":
            raise HTTPException(status_code=422, detail="只能绑定未映射字段")
        job = (
            self.db.query(ExtractionJob)
            .filter(ExtractionJob.id == entity.job_id)
            .first()
        )
        if request.action == "bind_existing":
            bindings = (
                (job.schema_snapshot or {}).get("field_bindings", []) if job else []
            )
            target = next(
                (
                    item
                    for item in bindings
                    if (
                        request.target_field_id
                        and item.get("field_id") == request.target_field_id
                    )
                    or (
                        item.get("module_id") == request.target_module_id
                        and item.get("field_key") == request.target_field_key
                        and item.get("instance_id") == request.target_instance_id
                    )
                ),
                None,
            )
            if target is None:
                raise HTTPException(status_code=404, detail="目标字段不存在于本次导入 Schema")
        else:
            target = self._create_custom_binding(entity, request, user, context)
            if job:
                snapshot = dict(job.schema_snapshot or {})
                snapshot["field_bindings"] = [
                    *(snapshot.get("field_bindings") or []),
                    target,
                ]
                job.schema_snapshot = snapshot
        previous = {"module_id": field.module_id, "field_key": field.field_key}
        field.module_id = target.get("module_id")
        field.instance_id = target.get("instance_id")
        field.field_id = target.get("field_id")
        field.field_key = target["field_key"]
        field.canonical_field_key = target.get("canonical_field_key")
        field.review_status = "pending"
        entity.source_mode = "mixed"
        workspace = self.review._workspace(entity)
        self.db.add(
            ImportReviewRecord(
                id=str(uuid4()),
                entity_id=entity.id,
                extracted_field_id=field.id,
                action="correct",
                previous_value=previous,
                new_value=target,
                reason="未映射字段绑定到模块字段",
                reviewer_id=user.id,
                **workspace,
            )
        )
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def add_manual_field(
        self,
        entity_id: str,
        request: ManualWorkbenchFieldCreate,
        user: User,
        context: WorkspaceContext,
    ) -> ExtractedEntity:
        """Add a schema-bound value that AI did not or must not extract."""
        entity = self.review.get_entity(entity_id, user, context)
        self.review._ensure_editable(entity)
        job = (
            self.db.query(ExtractionJob)
            .filter(ExtractionJob.id == entity.job_id)
            .first()
        )
        bindings = (job.schema_snapshot or {}).get("field_bindings", []) if job else []
        target = next(
            (
                item
                for item in bindings
                if (
                    request.target_field_id
                    and item.get("field_id") == request.target_field_id
                )
                or (
                    item.get("module_id") == request.target_module_id
                    and item.get("instance_id") == request.target_instance_id
                    and item.get("field_key") == request.target_field_key
                )
            ),
            None,
        )
        if target is None:
            raise HTTPException(status_code=404, detail="目标字段不存在于本次导入 Schema")
        duplicate = (
            self.db.query(ExtractedField)
            .filter(
                ExtractedField.entity_id == entity.id,
                ExtractedField.instance_id == target.get("instance_id"),
                ExtractedField.field_key == target.get("field_key"),
                ExtractedField.review_status != "rejected",
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="该字段已有有效值，请直接修正现有字段")
        workspace = self.review._workspace(entity)
        field = ExtractedField(
            id=str(uuid4()),
            entity_id=entity.id,
            module_id=target.get("module_id"),
            instance_id=target.get("instance_id"),
            field_id=target.get("field_id"),
            field_key=target["field_key"],
            canonical_field_key=target.get("canonical_field_key"),
            raw_value=request.value,
            normalized_value=request.value,
            confidence=1.0,
            review_status="accepted",
            schema_version=job.schema_version if job else "1.0",
            **workspace,
        )
        if entity.source_mode == "ai":
            entity.source_mode = "mixed"
        self.db.add(field)
        self.db.add(
            ImportReviewRecord(
                id=str(uuid4()),
                entity_id=entity.id,
                extracted_field_id=field.id,
                action="correct",
                previous_value=None,
                new_value=request.value,
                reason=request.reason or "审核工作台手工录入字段",
                reviewer_id=user.id,
                **workspace,
            )
        )
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def _create_custom_binding(self, entity, request, user, context):
        if entity.entity_type not in {"wps", "pqr", "ppqr"}:
            raise HTTPException(status_code=422, detail="当前类型暂不支持创建模块字段，请绑定已有字段")
        service = CustomModuleService(self.db)
        key = (
            re.sub(
                r"[^a-zA-Z0-9_]+",
                "_",
                request.field_key or request.field_label or "field",
            )
            .strip("_")
            .lower()[:120]
        )
        if not key:
            key = f"imported_{uuid4().hex[:8]}"
        definition = {
            "label": request.field_label,
            "type": request.field_type,
            "ai_extract_mode": "auto",
            "aliases": [],
        }
        if request.existing_custom_module_id:
            module = service.get_module(
                request.existing_custom_module_id, user, context
            )
            if module is None:
                raise HTTPException(status_code=404, detail="自定义模块不存在或无权修改")
            fields = dict(module.fields or {})
            if key in fields:
                raise HTTPException(status_code=409, detail="模块中已存在同名字段")
            fields[key] = definition
            module = service.update_module(
                module.id, CustomModuleUpdate(fields=fields), user, context
            )
        else:
            module = service.create_module(
                CustomModuleCreate(
                    name=request.module_name or "导入发现字段",
                    description="由智能导入审核工作台创建",
                    module_type=entity.entity_type,
                    category="basic",
                    repeatable=False,
                    fields={key: definition},
                    is_shared=context.is_enterprise(),
                    access_level="shared" if context.is_enterprise() else "private",
                ),
                user,
                context,
            )
        field_def = module.fields[key]
        return {
            "module_id": module.id,
            "instance_id": f"imported_{module.id}",
            "field_id": field_def["field_id"],
            "field_key": key,
            "label": request.field_label,
            "field_type": request.field_type,
            "required": False,
            "canonical_field_key": None,
            "ai_extract_mode": "auto",
            "extractable": True,
        }

    @staticmethod
    def _validate_value(field, binding, issues, states):
        value = field.normalized_value
        field_type = binding.get("field_type")
        invalid_type = (
            field_type in {"number", "integer"}
            and (not isinstance(value, (int, float)) or isinstance(value, bool))
        ) or (field_type == "checkbox" and not isinstance(value, bool))
        if invalid_type:
            SmartImportWorkbenchService._issue(
                issues,
                states,
                "type_violation",
                "error",
                [field.id],
                f"{binding.get('label') or field.field_key} 的值类型不正确",
            )
            return
        minimum, maximum = binding.get("minimum"), binding.get("maximum")
        if isinstance(value, (int, float)) and minimum is not None and value < minimum:
            SmartImportWorkbenchService._issue(
                issues,
                states,
                "range_violation",
                "error",
                [field.id],
                f"{binding.get('label') or field.field_key} 低于最小值 {minimum}",
            )
        if isinstance(value, (int, float)) and maximum is not None and value > maximum:
            SmartImportWorkbenchService._issue(
                issues,
                states,
                "range_violation",
                "error",
                [field.id],
                f"{binding.get('label') or field.field_key} 超过最大值 {maximum}",
            )
        options = binding.get("options") or []
        if options and value not in options:
            SmartImportWorkbenchService._issue(
                issues,
                states,
                "option_violation",
                "error",
                [field.id],
                f"{binding.get('label') or field.field_key} 不在允许选项中",
            )

    @staticmethod
    def _schema_metadata(
        snapshot: dict[str, Any], binding: dict[str, Any]
    ) -> dict[str, Any]:
        root = snapshot.get("json_schema") or {}
        container = root
        instance_id = binding.get("instance_id")
        if instance_id:
            container = (root.get("properties") or {}).get(instance_id) or {}
        payload = (container.get("properties") or {}).get(
            binding.get("field_key")
        ) or {}
        value_schema = (payload.get("properties") or {}).get("value") or {}
        return {
            "label": binding.get("label")
            or payload.get("title")
            or binding.get("field_key"),
            "field_type": binding.get("field_type") or value_schema.get("type", "text"),
            "required": binding.get("required")
            if "required" in binding
            else binding.get("field_key") in (container.get("required") or []),
            "minimum": binding.get("minimum")
            if "minimum" in binding
            else value_schema.get("minimum"),
            "maximum": binding.get("maximum")
            if "maximum" in binding
            else value_schema.get("maximum"),
            "options": binding.get("options") or value_schema.get("enum") or [],
        }

    @staticmethod
    def _issue(issues, states, code, severity, field_ids, message):
        issues.append(
            {
                "code": code,
                "severity": severity,
                "field_ids": field_ids,
                "message": message,
            }
        )
        for field_id in field_ids:
            states[field_id]["conflicts"].append(code)

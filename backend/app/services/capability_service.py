"""Read-only aggregation and conservative availability checks for P2 capability library."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.models.equipment import Equipment
from app.models.material import WeldingMaterial
from app.models.pqr import PQR
from app.models.qualification import PQRQualificationResult, WPSPQRSupportLink
from app.models.smart_import import EntityPublishRecord, ExtractedEntity, SourceDocument
from app.models.user import User
from app.models.welder import Welder, WelderCertification
from app.models.wps import WPS
from app.schemas.capability import CapabilityCheckRequest, CapabilityFilters
from app.services.qualification_service import (
    _hash,
    _legacy_record_hash,
    _normalize_processes,
    _record_snapshot,
)


class CapabilityLibraryService:
    def __init__(self, db: Session):
        self.db = db
        self.access = DataAccessMiddleware(db)

    def overview(
        self,
        user: User,
        context: WorkspaceContext,
        filters: CapabilityFilters,
    ) -> dict[str, Any]:
        factory_id = filters.factory_id
        wps_records = self._scoped(WPS, user, context, factory_id)
        pqr_records = self._scoped(PQR, user, context, factory_id)
        welders = self._scoped(Welder, user, context, factory_id)
        materials = self._scoped(WeldingMaterial, user, context, factory_id)
        equipment = self._scoped(Equipment, user, context, factory_id)
        links = self._scoped(WPSPQRSupportLink, user, context, factory_id)
        results = self._scoped(PQRQualificationResult, user, context, factory_id)

        wps_by_id = {item.id: item for item in wps_records}
        pqr_by_id = {item.id: item for item in pqr_records}
        result_by_id = {item.id: item for item in results}
        traces = self._source_traces({"wps": list(wps_by_id), "pqr": list(pqr_by_id)})
        valid_entries, link_state = self._valid_capabilities(
            links, wps_by_id, pqr_by_id, result_by_id, traces
        )
        certifications = self._certifications([item.id for item in welders])
        today = date.today()
        welder_rows = [
            _welder_row(item, certifications.get(item.id, []), today)
            for item in welders
        ]
        material_rows = [_material_row(item, today) for item in materials]
        equipment_rows = [_equipment_row(item, today) for item in equipment]
        for entry in valid_entries:
            _attach_resources(entry, welder_rows, material_rows, equipment_rows)
        issues = self._issues(
            wps_records,
            pqr_records,
            results,
            links,
            valid_entries,
            link_state,
            welder_rows,
        )

        filtered_entries = [
            item for item in valid_entries if _entry_matches_filters(item, filters)
        ]
        filtered_wps_ids = {item["wps_id"] for item in filtered_entries}
        filtered_pqr_ids = {item["pqr_id"] for item in filtered_entries}
        search = (filters.search or "").strip().casefold()
        wps_rows = [
            self._wps_row(
                item,
                [entry for entry in valid_entries if entry["wps_id"] == item.id],
                traces.get(("wps", item.id), []),
                link_state,
            )
            for item in wps_records
            if _record_filter(item, filters, search)
            and (not _has_dimension_filter(filters) or item.id in filtered_wps_ids)
        ]
        pqr_rows = [
            self._pqr_row(
                item,
                [entry for entry in valid_entries if entry["pqr_id"] == item.id],
                traces.get(("pqr", item.id), []),
                results,
            )
            for item in pqr_records
            if _record_filter(item, filters, search)
            and (not _has_dimension_filter(filters) or item.id in filtered_pqr_ids)
        ]
        if search:
            welder_rows = [
                item
                for item in welder_rows
                if search in f"{item['welder_code']} {item['full_name']}".casefold()
            ]

        health = _health(issues, wps_records, valid_entries, welder_rows)
        dimensions = _dimensions(filtered_entries)
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "workspace": {
                "type": context.workspace_type,
                "company_id": context.company_id,
                "factory_id": factory_id or context.factory_id,
            },
            "filters": filters.model_dump(exclude_none=True),
            "summary": {
                "valid_wps": len({item["wps_id"] for item in valid_entries}),
                "qualified_pqr": len({item["pqr_id"] for item in valid_entries}),
                "active_welders": sum(
                    item["is_currently_valid"] for item in welder_rows
                ),
                "available_materials": sum(
                    item["is_available"] for item in material_rows
                ),
                "available_equipment": sum(
                    item["is_available"] for item in equipment_rows
                ),
                "process_capabilities": len(valid_entries),
                "pending_reviews": link_state["pending"],
            },
            "health": health,
            "dimensions": dimensions,
            "wps_records": wps_rows,
            "pqr_records": pqr_rows,
            "welders": welder_rows,
            "process_capabilities": filtered_entries,
            "materials": material_rows,
            "equipment": equipment_rows,
            "issues": issues,
        }

    def check(
        self,
        user: User,
        context: WorkspaceContext,
        request: CapabilityCheckRequest,
    ) -> dict[str, Any]:
        overview = self.overview(
            user,
            context,
            CapabilityFilters(factory_id=request.factory_id),
        )
        requirement = request.model_dump()
        matched = [
            item
            for item in overview["process_capabilities"]
            if scope_covers_requirement(item["qualified_scope"], requirement)
        ]
        matched_welders = [
            item
            for item in overview["welders"]
            if item["is_currently_valid"]
            and welder_covers_requirement(item, requirement)
        ]
        matched_materials = _matching_materials(overview["materials"], matched)
        matched_equipment = [
            item
            for item in overview["equipment"]
            if item["is_available"]
            and _equipment_supports(item, request.welding_process)
        ]
        process_capable = bool(matched)
        personnel_capable = bool(matched_welders)
        resource_ready = bool(matched_materials) and bool(matched_equipment)
        gaps = []
        explanation = []
        if process_capable:
            explanation.append(f"找到 {len(matched)} 条已批准且版本有效的 WPS/PQR 支持链")
        else:
            gaps.append(
                {
                    "code": "PROCESS_SCOPE_NOT_COVERED",
                    "severity": "blocking",
                    "message": "没有有效工艺能力完整覆盖该焊缝条件",
                }
            )
        if personnel_capable:
            explanation.append(f"找到 {len(matched_welders)} 名当前有效且范围匹配的焊工")
        else:
            gaps.append(
                {
                    "code": "NO_QUALIFIED_WELDER",
                    "severity": "blocking",
                    "message": "没有当前有效的焊工资质完整覆盖该条件",
                }
            )
        if not matched_materials:
            gaps.append(
                {
                    "code": "NO_AVAILABLE_MATERIAL",
                    "severity": "warning",
                    "message": "未找到与匹配 WPS 焊材信息一致的可用库存",
                }
            )
        if not matched_equipment:
            gaps.append(
                {
                    "code": "NO_AVAILABLE_EQUIPMENT",
                    "severity": "warning",
                    "message": "未找到可用焊接设备",
                }
            )
        if process_capable and personnel_capable and resource_ready:
            decision = "capable"
        elif process_capable and personnel_capable:
            decision = "needs_resources"
        else:
            decision = "not_capable"
        return {
            "decision": decision,
            "process_capable": process_capable,
            "personnel_capable": personnel_capable,
            "resource_ready": resource_ready,
            "requirement": requirement,
            "matched_capabilities": matched,
            "matched_welders": matched_welders,
            "matched_materials": matched_materials,
            "matched_equipment": matched_equipment,
            "gaps": gaps,
            "explanation": explanation,
        }

    def _scoped(
        self,
        model: Any,
        user: User,
        context: WorkspaceContext,
        factory_id: int | None,
    ) -> list[Any]:
        query = self.access.apply_workspace_filter(
            self.db.query(model), model, user, context
        )
        if factory_id and hasattr(model, "factory_id"):
            query = query.filter(model.factory_id == factory_id)
        return query.all()

    def _valid_capabilities(
        self,
        links: list[WPSPQRSupportLink],
        wps_by_id: dict[int, WPS],
        pqr_by_id: dict[int, PQR],
        result_by_id: dict[str, PQRQualificationResult],
        traces: dict[tuple[str, int], list[dict[str, Any]]],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        entries = []
        state: dict[str, Any] = {
            "pending": 0,
            "rejected": 0,
            "stale": 0,
            "valid": 0,
            "by_wps": defaultdict(lambda: Counter()),
        }
        for link in links:
            if link.confirmation_status != "confirmed" or not link.is_active:
                key = (
                    "rejected" if link.confirmation_status == "rejected" else "pending"
                )
                state[key] += 1
                state["by_wps"][link.wps_id][key] += 1
                continue
            wps, pqr = wps_by_id.get(link.wps_id), pqr_by_id.get(link.pqr_id)
            result = result_by_id.get(link.qualification_result_id)
            if (
                not wps
                or not pqr
                or _link_stale(link, wps, pqr)
                or wps.status != "approved"
                or not wps.is_active
                or pqr.status != "approved"
                or not pqr.is_active
                or not result
                or not result.is_current
                or result.outcome != "qualified"
                or result.requires_human_confirmation
                or result.pqr_version_key != link.pqr_version_key
            ):
                state["stale"] += 1
                state["by_wps"][link.wps_id]["stale"] += 1
                continue
            scope = link.qualified_scope or (result.result or {}).get(
                "qualification_scope", {}
            )
            if not scope:
                state["stale"] += 1
                state["by_wps"][link.wps_id]["stale"] += 1
                continue
            entries.append(
                {
                    "link_id": link.id,
                    "wps_id": wps.id,
                    "wps_number": wps.wps_number,
                    "wps_revision": wps.revision,
                    "pqr_id": pqr.id,
                    "pqr_number": pqr.pqr_number,
                    "rule_pack_id": result.rule_pack_id,
                    "rule_pack_version": result.rule_pack_version,
                    "supported_processes": link.supported_processes
                    or scope.get("welding_processes", []),
                    "qualified_scope": scope,
                    "factory_id": wps.factory_id,
                    "filler_material_spec": wps.filler_material_spec,
                    "filler_material_classification": wps.filler_material_classification,
                    "source": link.source,
                    "evidence": {
                        "wps_version_key": link.wps_version_key,
                        "pqr_version_key": link.pqr_version_key,
                        "qualification_result_id": result.id,
                        "basis": result.basis,
                        "source_documents": traces.get(("wps", wps.id), [])
                        + traces.get(("pqr", pqr.id), []),
                    },
                }
            )
            state["valid"] += 1
            state["by_wps"][wps.id]["valid"] += 1
        return entries, state

    def _source_traces(
        self, target_ids: dict[str, list[int]]
    ) -> dict[tuple[str, int], list[dict[str, Any]]]:
        pairs = [
            (entity_type, str(target_id))
            for entity_type, ids in target_ids.items()
            for target_id in ids
        ]
        if not pairs:
            return {}
        records = (
            self.db.query(EntityPublishRecord)
            .filter(
                or_(
                    *(
                        and_(
                            EntityPublishRecord.target_entity_type == entity_type,
                            EntityPublishRecord.target_entity_id.in_(
                                [str(item) for item in ids]
                            ),
                        )
                        for entity_type, ids in target_ids.items()
                        if ids
                    )
                )
            )
            .all()
        )
        entities = {
            item.id: item
            for item in self.db.query(ExtractedEntity)
            .filter(ExtractedEntity.id.in_([record.entity_id for record in records]))
            .all()
        }
        documents = {
            item.id: item
            for item in self.db.query(SourceDocument)
            .filter(
                SourceDocument.id.in_(
                    [entity.document_id for entity in entities.values()]
                )
            )
            .all()
        }
        result: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            entity = entities.get(record.entity_id)
            document = documents.get(entity.document_id) if entity else None
            if not document:
                continue
            result[(record.target_entity_type, int(record.target_entity_id))].append(
                {
                    "document_id": document.id,
                    "filename": document.original_filename,
                    "sha256": document.sha256,
                    "document_version": document.document_version,
                    "published_at": record.created_at.isoformat(),
                }
            )
        return result

    def _certifications(
        self, welder_ids: list[int]
    ) -> dict[int, list[WelderCertification]]:
        if not welder_ids:
            return {}
        result: dict[int, list[WelderCertification]] = defaultdict(list)
        for item in (
            self.db.query(WelderCertification)
            .filter(WelderCertification.welder_id.in_(welder_ids))
            .all()
        ):
            result[item.welder_id].append(item)
        return result

    @staticmethod
    def _wps_row(
        wps: WPS,
        entries: list[dict[str, Any]],
        documents: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        link_counts = state["by_wps"][wps.id]
        return {
            "id": wps.id,
            "number": wps.wps_number,
            "title": wps.title,
            "revision": wps.revision,
            "status": wps.status,
            "is_active": bool(wps.is_active),
            "factory_id": wps.factory_id,
            "welding_process": wps.welding_process,
            "material_group": wps.base_material_group,
            "valid_support_count": len(entries),
            "pending_support_count": link_counts["pending"],
            "stale_support_count": link_counts["stale"],
            "health_status": "valid"
            if entries
            else "unsupported"
            if wps.status == "approved" and wps.is_active
            else "inactive",
            "supporting_pqrs": [
                {
                    "pqr_id": item["pqr_id"],
                    "pqr_number": item["pqr_number"],
                    "rule_pack_version": item["rule_pack_version"],
                }
                for item in entries
            ],
            "source_documents": documents,
        }

    @staticmethod
    def _pqr_row(
        pqr: PQR,
        entries: list[dict[str, Any]],
        documents: list[dict[str, Any]],
        results: list[PQRQualificationResult],
    ) -> dict[str, Any]:
        current = next(
            (item for item in results if item.pqr_id == pqr.id and item.is_current),
            None,
        )
        return {
            "id": pqr.id,
            "number": pqr.pqr_number,
            "title": pqr.title,
            "status": pqr.status,
            "is_active": bool(pqr.is_active),
            "factory_id": pqr.factory_id,
            "welding_process": pqr.welding_process,
            "material_group": pqr.base_material_group,
            "qualification_outcome": current.outcome if current else None,
            "rule_pack_version": current.rule_pack_version if current else None,
            "supported_wps_count": len({item["wps_id"] for item in entries}),
            "needs_confirmation": bool(current and current.requires_human_confirmation),
            "source_documents": documents,
        }

    @staticmethod
    def _issues(
        wps_records: list[WPS],
        pqr_records: list[PQR],
        results: list[PQRQualificationResult],
        links: list[WPSPQRSupportLink],
        entries: list[dict[str, Any]],
        link_state: dict[str, Any],
        welders: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        issues = []
        if not entries:
            issues.append(
                {
                    "code": "NO_VALID_CAPABILITY_DATA",
                    "severity": "blocking",
                    "entity_type": "capability",
                    "entity_id": None,
                    "label": "0",
                    "message": "当前工作区尚无可用的已批准工艺能力",
                }
            )
        valid_wps = {item["wps_id"] for item in entries}
        current_pqr = {item.pqr_id for item in results if item.is_current}
        for item in wps_records:
            if (
                item.status == "approved"
                and item.is_active
                and item.id not in valid_wps
            ):
                issues.append(
                    {
                        "code": "WPS_WITHOUT_VALID_PQR",
                        "severity": "blocking",
                        "entity_type": "wps",
                        "entity_id": item.id,
                        "label": item.wps_number,
                        "message": "已批准 WPS 没有当前有效的 PQR 支持关系",
                    }
                )
        for item in pqr_records:
            if (
                item.status == "approved"
                and item.is_active
                and item.id not in current_pqr
            ):
                issues.append(
                    {
                        "code": "PQR_WITHOUT_CALCULATION",
                        "severity": "blocking",
                        "entity_type": "pqr",
                        "entity_id": item.id,
                        "label": item.pqr_number,
                        "message": "已批准 PQR 尚未生成当前规则计算结果",
                    }
                )
        for item in results:
            if item.is_current and item.outcome in {
                "needs_confirmation",
                "insufficient_data",
            }:
                issues.append(
                    {
                        "code": "PQR_CALCULATION_INCOMPLETE",
                        "severity": "blocking",
                        "entity_type": "pqr",
                        "entity_id": item.pqr_id,
                        "label": str(item.pqr_id),
                        "message": "PQR 资格计算存在边界或资料不足，未纳入有效能力",
                    }
                )
        if link_state["pending"]:
            issues.append(
                {
                    "code": "SUPPORT_LINKS_PENDING",
                    "severity": "warning",
                    "entity_type": "support_link",
                    "entity_id": None,
                    "label": str(link_state["pending"]),
                    "message": f"{link_state['pending']} 条 WPS/PQR 支持关系待工程师确认",
                }
            )
        if link_state["stale"]:
            issues.append(
                {
                    "code": "SUPPORT_LINKS_STALE",
                    "severity": "blocking",
                    "entity_type": "support_link",
                    "entity_id": None,
                    "label": str(link_state["stale"]),
                    "message": f"{link_state['stale']} 条关系因版本、状态或计算结果变化已失效",
                }
            )
        expiring = sum(item["expiry_risk"] == "expiring_soon" for item in welders)
        if expiring:
            issues.append(
                {
                    "code": "WELDER_CERTIFICATIONS_EXPIRING",
                    "severity": "warning",
                    "entity_type": "welder",
                    "entity_id": None,
                    "label": str(expiring),
                    "message": f"{expiring} 名焊工的主要资质将在 30 天内到期",
                }
            )
        keys = [
            (
                tuple(sorted(item["supported_processes"])),
                tuple(sorted(item["qualified_scope"].get("material_groups", []))),
                tuple(sorted(item["qualified_scope"].get("positions", []))),
                json.dumps(
                    item["qualified_scope"].get("thickness", {}), sort_keys=True
                ),
            )
            for item in entries
        ]
        duplicates = sum(count - 1 for count in Counter(keys).values() if count > 1)
        if duplicates:
            issues.append(
                {
                    "code": "DUPLICATE_CAPABILITY_SCOPE",
                    "severity": "info",
                    "entity_type": "capability",
                    "entity_id": None,
                    "label": str(duplicates),
                    "message": f"发现 {duplicates} 条重复工艺能力范围，建议核对是否保留",
                }
            )
        prescriptions: dict[tuple[Any, ...], set[tuple[str, str]]] = defaultdict(set)
        for item, key in zip(entries, keys):
            prescriptions[key].add(
                (
                    _norm(item.get("filler_material_spec")),
                    _norm(item.get("filler_material_classification")),
                )
            )
        conflicts = sum(
            1
            for variants in prescriptions.values()
            if len({item for item in variants if any(item)}) > 1
        )
        if conflicts:
            issues.append(
                {
                    "code": "CAPABILITY_REQUIREMENT_CONFLICT",
                    "severity": "warning",
                    "entity_type": "capability",
                    "entity_id": None,
                    "label": str(conflicts),
                    "message": f"发现 {conflicts} 组范围相同但焊材要求冲突的工艺能力",
                }
            )
        return issues


def scope_covers_requirement(
    scope: dict[str, Any], requirement: dict[str, Any]
) -> bool:
    """Strictly test a condition against a calculated scope; missing means no coverage."""
    process = _normalize_processes(requirement.get("welding_process"))
    scope_processes = _normalize_processes(scope.get("welding_processes"))
    if not process or not all(item in scope_processes for item in process):
        return False
    groups = {_norm(item) for item in scope.get("material_groups", [])}
    if _norm(requirement.get("material_group")) not in groups:
        return False
    positions = {_norm(item) for item in scope.get("positions", [])}
    if _norm(requirement.get("welding_position")) not in positions:
        return False
    thickness = scope.get("thickness") or {}
    required_thickness = _number(requirement.get("thickness_mm"))
    minimum, maximum = _number(thickness.get("min_mm")), _number(
        thickness.get("max_mm")
    )
    if None in {required_thickness, minimum, maximum} or not (
        minimum <= required_thickness <= maximum
    ):
        return False
    diameter = requirement.get("diameter_mm")
    if diameter is not None:
        diameter_scope = scope.get("diameter") or {}
        if diameter_scope.get("applicable") is not True:
            return False
        dmin, dmax = _number(diameter_scope.get("min_mm")), _number(
            diameter_scope.get("max_mm")
        )
        required_diameter = _number(diameter)
        if None in {dmin, dmax, required_diameter} or not (
            dmin <= required_diameter <= dmax
        ):
            return False
    if bool((scope.get("pwht") or {}).get("performed")) != bool(
        requirement.get("pwht_required")
    ):
        return False
    if requirement.get("impact_required"):
        impact = scope.get("impact") or {}
        if not impact.get("required"):
            return False
        required_temp = requirement.get("impact_temperature_c")
        tested_temp = impact.get("tested_temperature_c")
        if required_temp is not None and (
            tested_temp is None or float(tested_temp) > float(required_temp)
        ):
            return False
    return True


def welder_covers_requirement(
    welder: dict[str, Any], requirement: dict[str, Any]
) -> bool:
    process = requirement.get("welding_process")
    material = requirement.get("material_group")
    position = requirement.get("welding_position")
    thickness = requirement.get("thickness_mm")
    qualifications = welder.get("qualifications") or []
    for item in qualifications:
        if not _contains_token(item.get("process"), process):
            continue
        if not _contains_token(item.get("material_group"), material):
            continue
        if not _contains_token(item.get("position"), position):
            continue
        if not _range_contains(item.get("thickness_range"), thickness):
            continue
        return True
    return False


def _welder_row(
    welder: Welder, certifications: list[WelderCertification], today: date
) -> dict[str, Any]:
    valid_certifications = [
        item
        for item in certifications
        if item.is_active
        and item.status == "valid"
        and (item.expiry_date is None or item.expiry_date >= today)
    ]
    qualifications = [
        {
            "certification_id": item.id,
            "certification_number": item.certification_number,
            "process": item.qualified_process,
            "material_group": item.qualified_material_group,
            "thickness_range": item.qualified_thickness_range,
            "diameter_range": item.qualified_diameter_range,
            "position": item.qualified_position,
            "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
        }
        for item in valid_certifications
    ]
    if not qualifications and welder.primary_certification_number:
        qualifications.append(
            {
                "certification_id": None,
                "certification_number": welder.primary_certification_number,
                "process": welder.qualified_processes,
                "material_group": welder.qualified_materials,
                "thickness_range": None,
                "diameter_range": None,
                "position": welder.qualified_positions,
                "expiry_date": welder.primary_expiry_date.isoformat()
                if welder.primary_expiry_date
                else None,
            }
        )
    expiry_dates = [
        item.expiry_date for item in valid_certifications if item.expiry_date
    ]
    if welder.primary_expiry_date:
        expiry_dates.append(welder.primary_expiry_date)
    next_expiry = min(expiry_dates) if expiry_dates else None
    if next_expiry and next_expiry < today:
        risk = "expired"
    elif next_expiry and next_expiry <= today + timedelta(days=30):
        risk = "expiring_soon"
    else:
        risk = "normal"
    is_valid = bool(
        welder.is_active
        and welder.status == "active"
        and welder.certification_status == "valid"
        and (welder.primary_expiry_date is None or welder.primary_expiry_date >= today)
        and qualifications
    )
    return {
        "id": welder.id,
        "welder_code": welder.welder_code,
        "full_name": welder.full_name,
        "factory_id": welder.factory_id,
        "status": welder.status,
        "certification_status": welder.certification_status,
        "is_currently_valid": is_valid,
        "expiry_risk": risk,
        "next_expiry_date": next_expiry.isoformat() if next_expiry else None,
        "qualifications": qualifications,
    }


def _material_row(item: WeldingMaterial, today: date) -> dict[str, Any]:
    expired = bool(item.expiry_date and item.expiry_date.date() < today)
    return {
        "id": item.id,
        "code": item.material_code,
        "name": item.material_name,
        "type": item.material_type,
        "specification": item.specification,
        "classification": item.classification,
        "factory_id": item.factory_id,
        "stock": item.current_stock or 0,
        "unit": item.unit,
        "status": item.status,
        "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
        "is_available": bool(
            item.is_active
            and not expired
            and item.status in {"in_stock", "low_stock"}
            and (item.current_stock or 0) > 0
        ),
    }


def _equipment_row(item: Equipment, today: date) -> dict[str, Any]:
    calibration_expired = bool(
        item.calibration_due_date and item.calibration_due_date < today
    )
    return {
        "id": item.id,
        "code": item.equipment_code,
        "name": item.equipment_name,
        "type": item.equipment_type,
        "category": item.category,
        "specifications": item.specifications,
        "factory_id": item.factory_id,
        "status": item.status,
        "calibration_due_date": item.calibration_due_date.isoformat()
        if item.calibration_due_date
        else None,
        "is_available": bool(
            item.is_active
            and item.status in {"operational", "idle"}
            and not calibration_expired
        ),
    }


def _health(
    issues: list[dict[str, Any]],
    wps_records: list[WPS],
    entries: list[dict[str, Any]],
    welders: list[dict[str, Any]],
) -> dict[str, Any]:
    blocking = sum(item["severity"] == "blocking" for item in issues)
    warnings = sum(item["severity"] == "warning" for item in issues)
    denominator = max(1, len(wps_records) + len(welders))
    score = max(
        0, round(100 - blocking * 60 / denominator - warnings * 20 / denominator)
    )
    return {
        "score": score,
        "status": "healthy" if score >= 85 else "attention" if score >= 60 else "risk",
        "blocking_issue_count": blocking,
        "warning_count": warnings,
        "unsupported_wps_count": sum(
            item["code"] == "WPS_WITHOUT_VALID_PQR" for item in issues
        ),
        "expiring_welder_count": sum(
            item["expiry_risk"] == "expiring_soon" for item in welders
        ),
        "valid_relation_count": len(entries),
    }


def _dimensions(entries: list[dict[str, Any]]) -> dict[str, list[Any]]:
    processes, materials, positions, thicknesses, diameters, pwht, impact = (
        set(),
        set(),
        set(),
        set(),
        set(),
        set(),
        set(),
    )
    for item in entries:
        scope = item["qualified_scope"]
        processes.update(scope.get("welding_processes", []))
        materials.update(scope.get("material_groups", []))
        positions.update(scope.get("positions", []))
        if scope.get("thickness"):
            thicknesses.add(json.dumps(scope["thickness"], sort_keys=True))
        if scope.get("diameter"):
            diameters.add(json.dumps(scope["diameter"], sort_keys=True))
        pwht.add(bool((scope.get("pwht") or {}).get("performed")))
        impact.add(bool((scope.get("impact") or {}).get("required")))
    return {
        "processes": sorted(processes),
        "material_groups": sorted(materials),
        "positions": sorted(positions),
        "thickness_ranges": [json.loads(item) for item in sorted(thicknesses)],
        "diameter_ranges": [json.loads(item) for item in sorted(diameters)],
        "pwht_conditions": sorted(pwht),
        "impact_conditions": sorted(impact),
    }


def _link_stale(link: WPSPQRSupportLink, wps: WPS, pqr: PQR) -> bool:
    if str(link.wps_snapshot_hash).startswith("legacy:"):
        return (
            _legacy_record_hash(wps) != link.wps_snapshot_hash
            or _legacy_record_hash(pqr) != link.pqr_snapshot_hash
        )
    return (
        _hash(_record_snapshot(wps)) != link.wps_snapshot_hash
        or _hash(_record_snapshot(pqr)) != link.pqr_snapshot_hash
    )


def _entry_matches_filters(item: dict[str, Any], filters: CapabilityFilters) -> bool:
    scope = item["qualified_scope"]
    if filters.process and _norm(filters.process) not in {
        _norm(value) for value in scope.get("welding_processes", [])
    }:
        return False
    if filters.material_group and _norm(filters.material_group) not in {
        _norm(value) for value in scope.get("material_groups", [])
    }:
        return False
    if filters.position and _norm(filters.position) not in {
        _norm(value) for value in scope.get("positions", [])
    }:
        return False
    if filters.search:
        haystack = f"{item['wps_number']} {item['pqr_number']}".casefold()
        if filters.search.strip().casefold() not in haystack:
            return False
    return True


def _record_filter(item: Any, filters: CapabilityFilters, search: str) -> bool:
    if filters.factory_id and item.factory_id != filters.factory_id:
        return False
    if search:
        number = getattr(item, "wps_number", None) or getattr(item, "pqr_number", "")
        if search not in f"{number} {item.title}".casefold():
            return False
    return True


def _has_dimension_filter(filters: CapabilityFilters) -> bool:
    return bool(filters.process or filters.material_group or filters.position)


def _matching_materials(
    materials: list[dict[str, Any]], capabilities: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    requirements = {
        _norm(value)
        for item in capabilities
        for value in (
            item.get("filler_material_spec"),
            item.get("filler_material_classification"),
        )
        if value
    }
    if not requirements:
        return []
    return [
        item
        for item in materials
        if item["is_available"]
        and requirements.intersection(
            {_norm(item.get("specification")), _norm(item.get("classification"))}
        )
    ]


def _attach_resources(
    entry: dict[str, Any],
    welders: list[dict[str, Any]],
    materials: list[dict[str, Any]],
    equipment: list[dict[str, Any]],
) -> None:
    scope = entry["qualified_scope"]
    thickness = scope.get("thickness") or {}
    minimum, maximum = _number(thickness.get("min_mm")), _number(
        thickness.get("max_mm")
    )
    representative = (
        (minimum + maximum) / 2 if minimum is not None and maximum is not None else None
    )
    requirement = {
        "welding_process": next(iter(scope.get("welding_processes", [])), None),
        "material_group": next(iter(scope.get("material_groups", [])), None),
        "welding_position": next(iter(scope.get("positions", [])), None),
        "thickness_mm": representative,
    }
    matched_welders = [
        item
        for item in welders
        if item["is_currently_valid"] and welder_covers_requirement(item, requirement)
    ]
    matched_materials = _matching_materials(materials, [entry])
    process = requirement["welding_process"] or ""
    matched_equipment = [
        item
        for item in equipment
        if item["is_available"] and _equipment_supports(item, process)
    ]
    entry["resource_links"] = {
        "welder_ids": [item["id"] for item in matched_welders],
        "material_ids": [item["id"] for item in matched_materials],
        "equipment_ids": [item["id"] for item in matched_equipment],
        "welder_count": len(matched_welders),
        "material_count": len(matched_materials),
        "equipment_count": len(matched_equipment),
    }


def _equipment_supports(item: dict[str, Any], process: str) -> bool:
    if item.get("type") != "welding_machine":
        return False
    text = f"{item.get('name')} {item.get('category')} {item.get('specifications')}"
    normalized = _normalize_processes(process)
    return (
        not normalized
        or any(value.casefold() in text.casefold() for value in normalized)
        or not item.get("specifications")
    )


def _contains_token(value: Any, target: Any) -> bool:
    if target in (None, "") or value in (None, ""):
        return False
    target_norm = _norm(target)
    values = _flatten_values(value)
    return target_norm in {_norm(item) for item in values}


def _flatten_values(value: Any) -> list[Any]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if parsed != value:
                return _flatten_values(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
        return [item for item in re.split(r"[,，/+、;；\s]+", value) if item]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _flatten_values(nested)]
    if isinstance(value, (list, tuple, set)):
        return [item for nested in value for item in _flatten_values(nested)]
    return [value]


def _range_contains(value: Any, target: Any) -> bool:
    number = _number(target)
    if value in (None, "") or number is None:
        return False
    numbers = [
        float(item) for item in re.findall(r"(?<!\d)-?\d+(?:\.\d+)?", str(value))
    ]
    if len(numbers) >= 2:
        return min(numbers[0], numbers[1]) <= number <= max(numbers[0], numbers[1])
    if len(numbers) == 1:
        return number == numbers[0]
    return False


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()

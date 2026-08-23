"""Deterministic, versioned PQR qualification and WPS/PQR support management."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.data_access import DataAccessMiddleware, WorkspaceContext
from app.models.pqr import PQR
from app.models.qualification import (
    PQRQualificationResult,
    QualificationRulePack,
    WPSPQRSupportLink,
)
from app.models.user import User
from app.models.wps import WPS
from app.schemas.qualification import WPSPQRSupportConfirm, WPSPQRSupportCreate
from app.services.pqr_service import PQRService
from app.services.wps_service import WPSService


NBT47014_2023_PACK_ID = "47014000-2023-4000-8000-000000000001"
SUPPORTED_STANDARD = "NB/T 47014"
SUPPORTED_EDITION = "2023"
PROTECTED_FACTS = {
    "qualification_result",
    "approval_status",
    "visual_inspection_result",
    "tensile_test_result",
    "root_bend_result",
    "face_bend_result",
    "side_bend_result",
}


PROCESS_ALIASES = {
    "111": "SMAW",
    "SMAW": "SMAW",
    "焊条电弧焊": "SMAW",
    "12": "SAW",
    "121": "SAW",
    "SAW": "SAW",
    "埋弧焊": "SAW",
    "141": "GTAW",
    "GTAW": "GTAW",
    "TIG": "GTAW",
    "钨极气体保护焊": "GTAW",
    "131": "GMAW",
    "135": "GMAW",
    "GMAW": "GMAW",
    "MIG": "GMAW",
    "MAG": "GMAW",
    "熔化极气体保护焊": "GMAW",
    "136": "FCAW",
    "138": "FCAW",
    "FCAW": "FCAW",
    "药芯焊丝电弧焊": "FCAW",
    "15": "PAW",
    "PAW": "PAW",
    "等离子弧焊": "PAW",
    "ESW": "ESW",
    "电渣焊": "ESW",
    "FRW": "FRW",
    "摩擦焊": "FRW",
    "EGW": "EGW",
    "气电立焊": "EGW",
    "螺柱电弧焊": "SW",
    "电子束焊": "EBW",
    "气焊": "OFW",
}


def evaluate_nbt47014_2023(facts: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a conservative, deterministic NB/T 47014—2023 rule subset.

    The engine never broadens material group, position, or pipe diameter beyond
    recorded facts. Dimensions needing the licensed standard tables are surfaced
    for human confirmation instead of being guessed.
    """
    normalized = dict(facts)
    processes = _normalize_processes(facts.get("welding_processes"))
    normalized["welding_processes"] = processes
    required = {
        "qualification_result": facts.get("qualification_result"),
        "approval_status": facts.get("approval_status"),
        "welding_processes": processes,
        "material_group": facts.get("material_group"),
        "test_piece_thickness_mm": _positive_number(
            facts.get("test_piece_thickness_mm")
        ),
        "joint_type": facts.get("joint_type"),
        "welding_position": facts.get("welding_position"),
    }
    missing = [key for key, value in required.items() if value in (None, "", [])]
    basis = [
        {
            "rule_id": "NBT47014-2023-BASE",
            "standard": "NB/T 47014—2023",
            "locator": "焊接工艺评定因素及评定规则",
            "description": "仅使用已确认事实进行确定性推导，不引用或复制标准正文",
        }
    ]
    failed_facts = [
        key
        for key in (
            "visual_inspection_result",
            "tensile_test_result",
            "root_bend_result",
            "face_bend_result",
            "side_bend_result",
        )
        if str(facts.get(key) or "").strip().lower()
        in {"fail", "failed", "不合格", "not qualified"}
    ]
    if missing:
        return {
            "outcome": "insufficient_data",
            "input": normalized,
            "qualification_scope": {},
            "basis": basis,
            "missing_fields": missing,
            "boundary_conditions": [],
            "requires_human_confirmation": True,
        }
    if (
        str(facts.get("qualification_result") or "").lower()
        not in {"qualified", "pass", "合格"}
        or str(facts.get("approval_status") or "").lower() != "approved"
        or failed_facts
    ):
        return {
            "outcome": "not_qualified",
            "input": normalized,
            "qualification_scope": {},
            "basis": basis,
            "missing_fields": missing,
            "boundary_conditions": [
                {
                    "code": "PQR_NOT_APPROVED_OR_TEST_FAILED",
                    "fields": failed_facts,
                    "message": "PQR 未批准、评定结论不合格或存在明确失败试验",
                }
            ],
            "requires_human_confirmation": False,
        }
    thickness = float(required["test_piece_thickness_mm"])
    thickness_scope, thickness_rule = _qualified_thickness(thickness)
    basis.append(thickness_rule)
    boundaries: list[dict[str, Any]] = []
    if thickness in {1.5, 8.0, 12.0}:
        boundaries.append(
            {
                "code": "THICKNESS_TABLE_BOUNDARY",
                "value_mm": thickness,
                "message": "试件厚度位于规则分段边界，发布支持关系前需工程师复核",
            }
        )

    deposited = facts.get("deposited_thickness_by_process") or {}
    per_process = {}
    if len(processes) > 1:
        missing_deposited = [item for item in processes if item not in deposited]
        if missing_deposited:
            missing.extend(
                f"deposited_thickness_by_process.{item}" for item in missing_deposited
            )
        else:
            for process in processes:
                value = _positive_number(deposited.get(process))
                if value is None:
                    missing.append(f"deposited_thickness_by_process.{process}")
                else:
                    per_process[process] = _qualified_thickness(value)[0]
        boundaries.append(
            {
                "code": "COMBINED_PROCESS_REVIEW",
                "message": "组合焊接工艺须按各方法熔敷厚度分别复核",
            }
        )
        basis.append(
            {
                "rule_id": "NBT47014-2023-COMBINED-PROCESS",
                "standard": "NB/T 47014—2023",
                "locator": "组合焊接工艺评定因素",
                "description": "按各焊接方法熔敷厚度独立计算",
            }
        )

    form = str(facts.get("test_piece_form") or "").strip().lower()
    diameter = _positive_number(facts.get("test_piece_diameter_mm"))
    diameter_scope: dict[str, Any]
    if form in {"plate", "板", "板材"}:
        diameter_scope = {"applicable": False, "reason": "plate_test_piece"}
    elif diameter is None:
        diameter_scope = {"applicable": None, "status": "missing"}
        missing.append("test_piece_diameter_mm")
    else:
        diameter_scope = {
            "applicable": True,
            "tested_diameter_mm": diameter,
            "min_mm": diameter,
            "max_mm": diameter,
            "mode": "tested_only",
        }
        boundaries.append(
            {
                "code": "DIAMETER_BROADENING_NOT_AUTOMATED",
                "message": "当前规则包仅输出已试验直径；扩大管径范围需工程师按授权标准复核",
            }
        )

    scope = {
        "standard": "NB/T 47014—2023",
        "welding_processes": processes,
        "material_groups": [str(required["material_group"]).strip()],
        "thickness": thickness_scope,
        "thickness_by_process": per_process,
        "diameter": diameter_scope,
        "positions": [str(required["welding_position"]).strip()],
        "joint_type": str(required["joint_type"]).strip(),
        "pwht": {
            "performed": bool(facts.get("pwht_performed")),
            "mode": "same_condition_only",
        },
        "impact": {
            "required": bool(facts.get("impact_test_performed")),
            "tested_temperature_c": facts.get("impact_test_temperature_c"),
            "mode": "tested_condition_only",
        },
    }
    requires_confirmation = bool(boundaries)
    outcome = (
        "insufficient_data"
        if missing
        else "needs_confirmation"
        if requires_confirmation
        else "qualified"
    )
    return {
        "outcome": outcome,
        "input": normalized,
        "qualification_scope": scope if not missing else {},
        "basis": basis,
        "missing_fields": sorted(set(missing)),
        "boundary_conditions": boundaries,
        "requires_human_confirmation": outcome != "qualified",
    }


class QualificationService:
    def __init__(self, db: Session):
        self.db = db
        self.access = DataAccessMiddleware(db)

    def list_rule_packs(self, include_inactive: bool = False):
        query = self.db.query(QualificationRulePack)
        if not include_inactive:
            query = query.filter(QualificationRulePack.status == "published")
        return query.order_by(
            QualificationRulePack.standard_code, QualificationRulePack.version.desc()
        ).all()

    def get_rule_pack(self, pack_id: str, published_only: bool = True):
        query = self.db.query(QualificationRulePack).filter(
            QualificationRulePack.id == pack_id
        )
        if published_only:
            query = query.filter(QualificationRulePack.status == "published")
        pack = query.first()
        if not pack:
            raise HTTPException(status_code=404, detail="规则包不存在或尚未发布")
        return pack

    def transition_rule_pack(self, pack_id: str, target: str) -> QualificationRulePack:
        pack = self.get_rule_pack(pack_id, published_only=False)
        allowed = {
            "draft": {"review"},
            "review": {"draft", "published"},
            "published": {"retired"},
            "retired": set(),
        }
        if target == pack.status:
            return pack
        if target not in allowed.get(pack.status, set()):
            raise HTTPException(
                status_code=409,
                detail=f"规则包状态不能从 {pack.status} 变更为 {target}",
            )
        if target == "published":
            compliance = pack.compliance_metadata or {}
            if compliance.get(
                "contains_standard_text"
            ) is not False or not compliance.get("citation_mode"):
                raise HTTPException(status_code=422, detail="规则包尚未通过引用与版权元数据检查")
            pack.published_at = datetime.utcnow()
        elif target == "retired":
            pack.retired_at = datetime.utcnow()
        pack.status = target
        self.db.commit()
        self.db.refresh(pack)
        return pack

    def calculate_pqr(
        self,
        pqr_id: int,
        user: User,
        context: WorkspaceContext,
        *,
        rule_pack_id: str | None = None,
        fact_overrides: dict[str, Any] | None = None,
        force_recalculate: bool = False,
    ) -> PQRQualificationResult:
        pqr = self._get_pqr(pqr_id, user, context)
        pack = self.get_rule_pack(rule_pack_id or NBT47014_2023_PACK_ID)
        if (
            pack.standard_code != SUPPORTED_STANDARD
            or pack.edition != SUPPORTED_EDITION
        ):
            raise HTTPException(status_code=422, detail="当前仅启用 NB/T 47014—2023 规则包")
        overrides = fact_overrides or {}
        protected_overrides = sorted(PROTECTED_FACTS.intersection(overrides))
        if protected_overrides:
            raise HTTPException(
                status_code=422,
                detail=f"不允许覆盖 PQR 批准、评定或试验事实: {', '.join(protected_overrides)}",
            )
        snapshot = _record_snapshot(pqr)
        snapshot_hash = _hash(snapshot)
        version_key = _version_key(pqr, "pqr")
        facts = self._pqr_facts(pqr)
        facts.update(overrides)
        calculation_key = _hash(
            {
                "pqr_snapshot_hash": snapshot_hash,
                "rule_pack_id": pack.id,
                "rule_pack_version": pack.version,
                "facts": facts,
            }
        )
        existing = (
            self.db.query(PQRQualificationResult)
            .filter(
                PQRQualificationResult.pqr_id == pqr.id,
                PQRQualificationResult.calculation_key == calculation_key,
                PQRQualificationResult.is_current.is_(True),
            )
            .first()
        )
        if existing and not force_recalculate:
            return existing
        evaluated = evaluate_nbt47014_2023(facts)
        current = (
            self.db.query(PQRQualificationResult)
            .filter(
                PQRQualificationResult.pqr_id == pqr.id,
                PQRQualificationResult.is_current.is_(True),
            )
            .order_by(PQRQualificationResult.calculated_at.desc())
            .first()
        )
        if current:
            current.is_current = False
        result = PQRQualificationResult(
            id=str(uuid4()),
            pqr_id=pqr.id,
            pqr_version_key=version_key,
            pqr_snapshot_hash=snapshot_hash,
            rule_pack_id=pack.id,
            rule_pack_version=pack.version,
            calculation_key=calculation_key,
            outcome=evaluated["outcome"],
            input_snapshot={"pqr": snapshot, "facts": evaluated["input"]},
            result={"qualification_scope": evaluated["qualification_scope"]},
            basis=evaluated["basis"],
            missing_fields=evaluated["missing_fields"],
            boundary_conditions=evaluated["boundary_conditions"],
            requires_human_confirmation=evaluated["requires_human_confirmation"],
            supersedes_result_id=current.id if current else None,
            is_current=True,
            calculated_by=user.id,
            calculated_at=datetime.utcnow(),
            **_workspace(pqr),
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def list_pqr_results(
        self, pqr_id: int, user: User, context: WorkspaceContext
    ) -> list[PQRQualificationResult]:
        pqr = self._get_pqr(pqr_id, user, context)
        return (
            self.db.query(PQRQualificationResult)
            .filter(PQRQualificationResult.pqr_id == pqr.id)
            .order_by(PQRQualificationResult.calculated_at.desc())
            .all()
        )

    def create_support_link(
        self,
        wps_id: int,
        request: WPSPQRSupportCreate,
        user: User,
        context: WorkspaceContext,
    ) -> WPSPQRSupportLink:
        wps = self._get_wps(wps_id, user, context)
        pqr = self._get_pqr(request.pqr_id, user, context)
        qualification = None
        if request.qualification_result_id:
            qualification = (
                self.db.query(PQRQualificationResult)
                .filter(
                    PQRQualificationResult.id == request.qualification_result_id,
                    PQRQualificationResult.pqr_id == pqr.id,
                )
                .first()
            )
            if not qualification:
                raise HTTPException(status_code=404, detail="资格计算结果不存在或不属于该 PQR")
        if request.confirmation_status == "confirmed":
            if (
                wps.status != "approved"
                or pqr.status != "approved"
                or not qualification
                or qualification.outcome != "qualified"
                or not qualification.is_current
                or qualification.pqr_version_key != _version_key(pqr, "pqr")
            ):
                raise HTTPException(status_code=422, detail="只有明确合格的计算结果可以确认支持关系")
        wps_snapshot, pqr_snapshot = _record_snapshot(wps), _record_snapshot(pqr)
        wps_version, pqr_version = _version_key(wps, "wps"), _version_key(pqr, "pqr")
        duplicate = (
            self.db.query(WPSPQRSupportLink)
            .filter(
                WPSPQRSupportLink.wps_id == wps.id,
                WPSPQRSupportLink.pqr_id == pqr.id,
                WPSPQRSupportLink.wps_version_key == wps_version,
                WPSPQRSupportLink.pqr_version_key == pqr_version,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="当前 WPS/PQR 版本已存在支持关系")
        scope = request.qualified_scope
        processes = request.supported_processes
        if qualification:
            calculated_scope = (qualification.result or {}).get(
                "qualification_scope"
            ) or {}
            scope = scope or calculated_scope
            processes = processes or calculated_scope.get("welding_processes") or []
        now = datetime.utcnow()
        link = WPSPQRSupportLink(
            id=str(uuid4()),
            wps_id=wps.id,
            pqr_id=pqr.id,
            qualification_result_id=qualification.id if qualification else None,
            wps_version_key=wps_version,
            pqr_version_key=pqr_version,
            wps_snapshot_hash=_hash(wps_snapshot),
            pqr_snapshot_hash=_hash(pqr_snapshot),
            wps_snapshot=wps_snapshot,
            pqr_snapshot=pqr_snapshot,
            supported_processes=processes,
            qualified_scope=scope,
            source=request.source,
            confirmation_status=request.confirmation_status,
            confirmation_note=request.confirmation_note,
            confirmed_by=user.id
            if request.confirmation_status == "confirmed"
            else None,
            confirmed_at=now if request.confirmation_status == "confirmed" else None,
            is_active=True,
            created_by=user.id,
            created_at=now,
            **_workspace(wps),
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def confirm_support_link(
        self,
        link_id: str,
        request: WPSPQRSupportConfirm,
        user: User,
        context: WorkspaceContext,
    ) -> WPSPQRSupportLink:
        link = self._get_link(link_id, user, context)
        if request.confirmation_status == "confirmed":
            wps = self._get_wps(link.wps_id, user, context)
            pqr = self._get_pqr(link.pqr_id, user, context)
            if wps.status != "approved" or pqr.status != "approved":
                raise HTTPException(status_code=422, detail="WPS 和 PQR 均批准后才能确认支持关系")
            if not link.qualification_result_id:
                raise HTTPException(status_code=422, detail="确认前必须绑定资格计算结果")
            result = (
                self.db.query(PQRQualificationResult)
                .filter(PQRQualificationResult.id == link.qualification_result_id)
                .first()
            )
            if not result or result.outcome != "qualified" or not result.is_current:
                raise HTTPException(status_code=422, detail="资格计算结果不是明确合格")
            if self._link_is_stale(link):
                raise HTTPException(
                    status_code=409, detail="WPS 或 PQR 已变化，请为当前版本重新建立关系"
                )
        link.confirmation_status = request.confirmation_status
        link.confirmation_note = request.confirmation_note
        link.confirmed_by = user.id
        link.confirmed_at = datetime.utcnow()
        if request.confirmation_status == "rejected":
            link.is_active = False
        self.db.commit()
        self.db.refresh(link)
        return link

    def wps_trace(
        self, wps_id: int, user: User, context: WorkspaceContext
    ) -> dict[str, Any]:
        wps = self._get_wps(wps_id, user, context)
        links = (
            self.db.query(WPSPQRSupportLink)
            .filter(WPSPQRSupportLink.wps_id == wps.id)
            .order_by(WPSPQRSupportLink.created_at.desc())
            .all()
        )
        valid, stale = 0, 0
        for link in links:
            if self._link_is_stale(link):
                stale += 1
            elif link.is_active and link.confirmation_status == "confirmed":
                result = None
                if link.qualification_result_id:
                    result = (
                        self.db.query(PQRQualificationResult)
                        .filter(
                            PQRQualificationResult.id == link.qualification_result_id
                        )
                        .first()
                    )
                if result and result.is_current and result.outcome == "qualified":
                    valid += 1
        return {
            "wps_id": wps.id,
            "current_wps_version_key": _version_key(wps, "wps"),
            "valid_support_count": valid,
            "stale_support_count": stale,
            "links": links,
        }

    def _link_is_stale(self, link: WPSPQRSupportLink) -> bool:
        wps = self.db.query(WPS).filter(WPS.id == link.wps_id).first()
        pqr = self.db.query(PQR).filter(PQR.id == link.pqr_id).first()
        if not wps or not pqr:
            return True
        return (
            _hash(_record_snapshot(wps)) != link.wps_snapshot_hash
            or _hash(_record_snapshot(pqr)) != link.pqr_snapshot_hash
        )

    def _get_wps(self, record_id: int, user: User, context: WorkspaceContext) -> WPS:
        record = WPSService(self.db).get(
            self.db,
            id=record_id,
            current_user=user,
            workspace_context=context,
        )
        if not record:
            raise HTTPException(status_code=404, detail="WPS 不存在或无权访问")
        return record

    def _get_pqr(self, record_id: int, user: User, context: WorkspaceContext) -> PQR:
        record = PQRService(self.db).get(
            self.db,
            id=record_id,
            current_user=user,
            workspace_context=context,
        )
        if not record:
            raise HTTPException(status_code=404, detail="PQR 不存在或无权访问")
        return record

    def _get_link(
        self, link_id: str, user: User, context: WorkspaceContext
    ) -> WPSPQRSupportLink:
        query = self.access.apply_workspace_filter(
            self.db.query(WPSPQRSupportLink), WPSPQRSupportLink, user, context
        )
        link = query.filter(WPSPQRSupportLink.id == link_id).first()
        if not link:
            raise HTTPException(status_code=404, detail="支持关系不存在或无权访问")
        return link

    @staticmethod
    def _pqr_facts(pqr: PQR) -> dict[str, Any]:
        modules = pqr.modules_data or {}
        return {
            "qualification_result": pqr.qualification_result,
            "approval_status": pqr.status,
            "welding_processes": pqr.welding_process,
            "material_group": pqr.base_material_group
            or _find_dynamic_value(modules, ("base_material_group", "material_group")),
            "test_piece_thickness_mm": pqr.base_material_thickness
            or _find_dynamic_value(modules, ("thickness", "base_material_thickness")),
            "test_piece_diameter_mm": _find_dynamic_value(
                modules, ("test_piece_diameter", "outside_diameter", "pipe_diameter")
            ),
            "test_piece_form": _find_dynamic_value(
                modules, ("test_piece_form", "product_form", "material_form")
            ),
            "joint_type": pqr.joint_design,
            "welding_position": _find_dynamic_value(
                modules, ("welding_position", "test_position", "position")
            ),
            "pwht_performed": pqr.pwht_performed,
            "impact_test_performed": pqr.charpy_test_performed,
            "impact_test_temperature_c": pqr.charpy_test_temp,
            "visual_inspection_result": pqr.visual_inspection_result,
            "tensile_test_result": pqr.tensile_test_result,
            "root_bend_result": pqr.root_bend_result,
            "face_bend_result": pqr.face_bend_result,
            "side_bend_result": pqr.side_bend_result,
            "deposited_thickness_by_process": _find_dynamic_value(
                modules, ("deposited_thickness_by_process",)
            ),
        }


def _qualified_thickness(thickness: float) -> tuple[dict[str, Any], dict[str, Any]]:
    if thickness < 1.5:
        minimum, maximum, segment = thickness, 2 * thickness, "T<1.5"
    elif thickness < 8:
        minimum, maximum, segment = 1.5, 2 * thickness, "1.5<=T<8"
    elif thickness <= 12:
        minimum, maximum, segment = 0.5 * thickness, 2 * thickness, "8<=T<=12"
    else:
        minimum, maximum, segment = 5.0, 2 * thickness, "T>12"
    return (
        {
            "min_mm": round(minimum, 3),
            "max_mm": round(maximum, 3),
            "tested_mm": thickness,
            "rule_segment": segment,
        },
        {
            "rule_id": "NBT47014-2023-THICKNESS-CONSERVATIVE",
            "standard": "NB/T 47014—2023",
            "locator": "对接焊缝试件厚度适用范围",
            "inputs": {"test_piece_thickness_mm": thickness},
            "segment": segment,
        },
    )


def _normalize_processes(value: Any) -> list[str]:
    if isinstance(value, list):
        parts = value
    else:
        parts = re.split(r"[,，/+、;；\s]+", str(value or ""))
    result = []
    for raw in parts:
        item = str(raw).strip()
        if not item:
            continue
        normalized = PROCESS_ALIASES.get(item) or PROCESS_ALIASES.get(item.upper())
        normalized = normalized or item.upper()
        if normalized not in result:
            result.append(normalized)
    return result


def _positive_number(value: Any) -> float | None:
    try:
        number = float(value)
        return number if number > 0 else None
    except (TypeError, ValueError):
        return None


def _find_dynamic_value(payload: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(payload, dict):
        for key in keys:
            if key in payload and payload[key] not in (None, "", [], {}):
                value = payload[key]
                if isinstance(value, dict) and "value" in value:
                    return value["value"]
                return value
        for value in payload.values():
            found = _find_dynamic_value(value, keys)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _find_dynamic_value(value, keys)
            if found not in (None, "", [], {}):
                return found
    return None


def _record_snapshot(record: Any) -> dict[str, Any]:
    snapshot = {}
    for column in record.__table__.columns:
        value = getattr(record, column.name)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        snapshot[column.name] = value
    return snapshot


def _version_key(record: Any, kind: str) -> str:
    updated = getattr(record, "updated_at", None) or getattr(record, "created_at", None)
    stamp = (
        updated.isoformat()
        if isinstance(updated, datetime)
        else str(updated or "unknown")
    )
    if kind == "wps":
        return f"{getattr(record, 'revision', None) or 'unversioned'}@{stamp}"
    return f"record@{stamp}"


def _hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, default=str
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _workspace(record: Any) -> dict[str, Any]:
    return {
        "user_id": record.user_id,
        "workspace_type": record.workspace_type,
        "company_id": record.company_id,
        "factory_id": record.factory_id,
        "access_level": record.access_level or "private",
    }

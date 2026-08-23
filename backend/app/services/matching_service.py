"""Deterministic P4 WPS/PQR matching with dimension-level explanations."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.data_access import (
    DataAccessAction,
    DataAccessMiddleware,
    WorkspaceContext,
)
from app.models.engineering import (
    EngineeringDependencyState,
    Part,
    ProductRevision,
    WeldJoint,
    WeldRequirement,
)
from app.models.matching import (
    WPSCapabilityGap,
    WPSMatchCandidate,
    WPSMatchCriterion,
    WPSMatchFreeze,
    WPSMatchRun,
)
from app.models.pqr import PQR
from app.models.ppqr import PPQR
from app.models.qualification import QualificationRulePack, WPSPQRSupportLink
from app.models.user import User
from app.models.wps import WPS
from app.services.capability_service import CapabilityLibraryService
from app.schemas.capability import CapabilityFilters
from app.services.engineering_service import workspace_values
from app.services.qualification_service import (
    _hash,
    _normalize_processes,
    _record_snapshot,
)


DIMENSIONS = (
    "material_group",
    "thickness",
    "diameter",
    "joint",
    "process",
    "position",
    "filler",
    "pwht",
    "impact",
)
DEFAULT_WEIGHTS = {
    "material_group": 15,
    "thickness": 15,
    "diameter": 8,
    "joint": 12,
    "process": 15,
    "position": 10,
    "filler": 10,
    "pwht": 8,
    "impact": 7,
}
STATUS_FACTOR = {"pass": 1.0, "boundary": 0.7, "insufficient": 0.25, "fail": 0.0}


def _norm(value: Any) -> str:
    return re.sub(r"[\s_\-/]+", "", str(value or "")).casefold()


def _joint_norm(value: Any) -> str:
    normalized = _norm(value)
    aliases = {
        "对接": "butt",
        "对接接头": "butt",
        "buttjoint": "butt",
        "t形": "tjoint",
        "t型": "tjoint",
        "tjoint": "tjoint",
        "搭接": "lap",
        "lapjoint": "lap",
        "角接": "corner",
        "cornerjoint": "corner",
        "v形": "v",
        "v型": "v",
        "vgroove": "v",
        "u形": "u",
        "u型": "u",
        "ugroove": "u",
        "j形": "j",
        "j型": "j",
        "jgroove": "j",
        "双v": "doublev",
        "x形": "doublev",
        "doublevgroove": "doublev",
    }
    return aliases.get(normalized, normalized)


def _number(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else None


def _criterion(
    dimension: str,
    status: str,
    required: Any,
    available: Any,
    message: str,
    basis: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "status": status,
        "required_value": {"value": required},
        "available_value": {"value": available},
        "message": message,
        "basis": basis,
    }


def build_weld_requirement(
    joint: WeldJoint, requirement: WeldRequirement | None, parts: dict[str, Part]
) -> dict[str, Any]:
    part_a, part_b = parts.get(joint.part_a_id), parts.get(joint.part_b_id)
    explicit_group = requirement.material_group if requirement else None
    groups = []
    for value in (
        (explicit_group,)
        if explicit_group
        else (
            getattr(part_a, "material_group", None),
            getattr(part_b, "material_group", None),
        )
    ):
        if value and _norm(value) not in {_norm(item) for item in groups}:
            groups.append(value)
    thicknesses = [
        item.thickness_mm
        for item in (part_a, part_b)
        if item and item.thickness_mm is not None
    ]
    thickness = max(thicknesses) if len(thicknesses) == 2 else None
    return {
        "weld_joint_id": joint.id,
        "weld_number": joint.weld_number,
        "part_a": {
            "id": part_a.id,
            "number": part_a.part_number,
            "material_group": part_a.material_group,
            "thickness_mm": part_a.thickness_mm,
        }
        if part_a
        else None,
        "part_b": {
            "id": part_b.id,
            "number": part_b.part_number,
            "material_group": part_b.material_group,
            "thickness_mm": part_b.thickness_mm,
        }
        if part_b
        else None,
        "material_groups": groups,
        "thickness_mm": thickness,
        "diameter_applicable": requirement.diameter_applicable if requirement else None,
        "diameter_mm": requirement.diameter_mm if requirement else None,
        "joint_type": joint.joint_type,
        "groove_type": joint.groove_type,
        "welding_process": requirement.welding_process if requirement else None,
        "welding_position": joint.weld_position,
        "filler_material_spec": requirement.filler_material_spec
        if requirement
        else None,
        "filler_material_classification": requirement.filler_material_classification
        if requirement
        else None,
        "pwht_required": requirement.pwht_required if requirement else None,
        "impact_required": requirement.impact_required if requirement else None,
        "impact_temperature_c": _number(requirement.impact_temperature)
        if requirement
        else None,
    }


def evaluate_candidate(
    requirement: dict[str, Any],
    capability: dict[str, Any],
    wps: WPS,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    scope = capability.get("qualified_scope") or {}
    basis_base = {
        "standard": scope.get("standard") or "NB/T 47014—2023",
        "rule_pack_version": capability.get("rule_pack_version"),
        "support_link_id": capability.get("link_id"),
    }
    criteria = []
    required_groups = {_norm(x) for x in requirement.get("material_groups") or []}
    available_groups = {_norm(x) for x in scope.get("material_groups") or []}
    criteria.append(
        _criterion(
            "material_group",
            "insufficient"
            if not required_groups
            else "pass"
            if required_groups <= available_groups
            else "fail",
            sorted(required_groups),
            scope.get("material_groups") or [],
            "母材组信息不足"
            if not required_groups
            else "母材组均在评定范围内"
            if required_groups <= available_groups
            else "母材组超出评定范围",
            basis_base,
        )
    )
    required_t = _number(requirement.get("thickness_mm"))
    ts = scope.get("thickness") or {}
    minimum, maximum = _number(ts.get("min_mm")), _number(ts.get("max_mm"))
    if required_t is None:
        status = "insufficient"
        message = "两侧零件厚度信息不足"
    elif minimum is None or maximum is None:
        status = "insufficient"
        message = "能力快照缺少厚度范围"
    elif not minimum <= required_t <= maximum:
        status = "fail"
        message = "厚度超出评定范围"
    elif abs(required_t - minimum) < 1e-9 or abs(required_t - maximum) < 1e-9:
        status = "boundary"
        message = "厚度位于评定范围边界"
    else:
        status = "pass"
        message = "厚度在评定范围内"
    criteria.append(
        _criterion(
            "thickness",
            status,
            required_t,
            ts,
            message,
            {**basis_base, "rule_id": "NBT47014-2023-THICKNESS-CONSERVATIVE"},
        )
    )
    applicable = requirement.get("diameter_applicable")
    required_d = _number(requirement.get("diameter_mm"))
    ds = scope.get("diameter") or {}
    if applicable is False:
        status = "pass"
        message = "该焊缝不适用直径评定"
    elif applicable is None:
        status = "insufficient"
        message = "未确认是否适用直径评定"
    elif required_d is None:
        status = "insufficient"
        message = "缺少产品直径"
    elif ds.get("applicable") is not True:
        status = "fail"
        message = "候选评定不覆盖管径"
    else:
        dmin, dmax = _number(ds.get("min_mm")), _number(ds.get("max_mm"))
        if dmin is None or dmax is None:
            status = "insufficient"
            message = "能力快照缺少直径范围"
        elif not dmin <= required_d <= dmax:
            status = "fail"
            message = "直径超出评定范围"
        elif abs(required_d - dmin) < 1e-9 or abs(required_d - dmax) < 1e-9:
            status = "boundary"
            message = "直径位于当前保守评定边界"
        else:
            status = "pass"
            message = "直径在评定范围内"
    criteria.append(
        _criterion(
            "diameter",
            status,
            {"applicable": applicable, "diameter_mm": required_d},
            ds,
            message,
            {**basis_base, "rule_id": "NBT47014-2023-DIAMETER"},
        )
    )
    required_joint, required_groove = requirement.get("joint_type"), requirement.get(
        "groove_type"
    )
    available_joint = getattr(wps, "joint_design", None)
    available_groove = getattr(wps, "groove_type", None)
    if not required_joint or not required_groove:
        status = "insufficient"
        message = "接头或坡口信息不足"
    elif not available_joint or not available_groove:
        status = "insufficient"
        message = "WPS 缺少接头或坡口数据"
    elif _joint_norm(required_joint) == _joint_norm(available_joint) and _joint_norm(
        required_groove
    ) == _joint_norm(available_groove):
        status = "pass"
        message = "接头与坡口一致"
    else:
        status = "fail"
        message = "接头或坡口与 WPS 不一致"
    criteria.append(
        _criterion(
            "joint",
            status,
            {"joint_type": required_joint, "groove_type": required_groove},
            {"joint_type": available_joint, "groove_type": available_groove},
            message,
            basis_base,
        )
    )
    required_processes = _normalize_processes(requirement.get("welding_process"))
    available_processes = _normalize_processes(
        capability.get("supported_processes") or scope.get("welding_processes")
    )
    status = (
        "insufficient"
        if not required_processes
        else "pass"
        if set(required_processes) <= set(available_processes)
        else "fail"
    )
    criteria.append(
        _criterion(
            "process",
            status,
            required_processes,
            available_processes,
            "焊接方法信息不足"
            if not required_processes
            else "焊接方法受支持"
            if status == "pass"
            else "焊接方法不受支持",
            basis_base,
        )
    )
    required_position = requirement.get("welding_position")
    positions = scope.get("positions") or []
    status = (
        "insufficient"
        if not required_position
        else "pass"
        if _norm(required_position) in {_norm(x) for x in positions}
        else "fail"
    )
    criteria.append(
        _criterion(
            "position",
            status,
            required_position,
            positions,
            "焊接位置未确认"
            if not required_position
            else "焊接位置在评定范围内"
            if status == "pass"
            else "焊接位置超出评定范围",
            basis_base,
        )
    )
    required_filler = [
        requirement.get("filler_material_spec"),
        requirement.get("filler_material_classification"),
    ]
    available_filler = [wps.filler_material_spec, wps.filler_material_classification]
    if not any(required_filler):
        status = "insufficient"
        message = "焊材要求未确认"
    elif any(
        req and (not got or _norm(req) != _norm(got))
        for req, got in zip(required_filler, available_filler)
    ):
        status = "fail"
        message = "焊材规格或分类不一致"
    else:
        status = "pass"
        message = "焊材要求一致"
    criteria.append(
        _criterion(
            "filler", status, required_filler, available_filler, message, basis_base
        )
    )
    pwht = requirement.get("pwht_required")
    available_pwht = (scope.get("pwht") or {}).get("performed")
    status = (
        "insufficient"
        if pwht is None or available_pwht is None
        else "pass"
        if bool(pwht) == bool(available_pwht)
        else "fail"
    )
    criteria.append(
        _criterion(
            "pwht",
            status,
            pwht,
            scope.get("pwht") or {},
            "PWHT 要求未确认"
            if pwht is None
            else "PWHT 条件一致"
            if status == "pass"
            else "PWHT 条件不一致",
            basis_base,
        )
    )
    impact = requirement.get("impact_required")
    impact_scope = scope.get("impact") or {}
    required_temp = requirement.get("impact_temperature_c")
    if impact is None:
        status = "insufficient"
        message = "冲击要求未确认"
    elif impact is False:
        status = "pass"
        message = "该焊缝不要求冲击试验"
    elif not impact_scope.get("required"):
        status = "fail"
        message = "候选评定未覆盖冲击要求"
    elif required_temp is None:
        status = "insufficient"
        message = "缺少冲击要求温度"
    elif impact_scope.get("tested_temperature_c") is None:
        status = "insufficient"
        message = "候选评定缺少冲击试验温度"
    elif float(impact_scope["tested_temperature_c"]) <= float(required_temp):
        status = "pass"
        message = "冲击试验温度覆盖要求"
    else:
        status = "fail"
        message = "冲击试验温度不覆盖要求"
    criteria.append(
        _criterion(
            "impact",
            status,
            {"required": impact, "temperature_c": required_temp},
            impact_scope,
            message,
            basis_base,
        )
    )
    statuses = {item["status"] for item in criteria}
    decision = (
        "not_eligible"
        if "fail" in statuses
        else "needs_confirmation"
        if statuses & {"boundary", "insufficient"}
        else "eligible"
    )
    applied = {**DEFAULT_WEIGHTS, **(weights or {})}
    total = (
        sum(max(0, float(applied.get(item["dimension"], 0))) for item in criteria) or 1
    )
    score = round(
        sum(
            max(0, float(applied.get(item["dimension"], 0)))
            * STATUS_FACTOR[item["status"]]
            for item in criteria
        )
        / total
        * 100,
        2,
    )
    return {"decision": decision, "score": score, "criteria": criteria}


class WPSMatchingService:
    def __init__(self, db: Session):
        self.db = db
        self.access = DataAccessMiddleware(db)

    def _get(
        self, model, item_id: str, user: User, context: WorkspaceContext, edit=False
    ):
        item = self.db.query(model).filter(model.id == item_id).first()
        if item is None:
            raise HTTPException(404, "匹配数据不存在")
        self.access.check_access(
            user,
            item,
            DataAccessAction.EDIT if edit else DataAccessAction.VIEW,
            context,
        )
        return item

    def _targets(
        self,
        revision: ProductRevision,
        requested: list[str] | None,
        affected_only: bool,
    ) -> list[WeldJoint]:
        query = self.db.query(WeldJoint).filter(
            WeldJoint.revision_id == revision.id, WeldJoint.is_deleted.is_(False)
        )
        if requested:
            query = query.filter(WeldJoint.id.in_(requested))
        elif affected_only:
            states = (
                self.db.query(EngineeringDependencyState)
                .filter(
                    EngineeringDependencyState.revision_id == revision.id,
                    EngineeringDependencyState.dependency_type == "matching",
                    EngineeringDependencyState.status == "stale",
                )
                .all()
            )
            all_scope = any(x.scope == "all" for x in states)
            ids = {
                item for state in states for item in (state.affected_joint_ids or [])
            }
            if not all_scope:
                query = query.filter(WeldJoint.id.in_(ids or ["-"]))
        return query.order_by(WeldJoint.weld_number).all()

    def run(
        self,
        revision_id: str,
        requested: list[str] | None,
        affected_only: bool,
        trigger: str,
        weights: dict[str, float],
        user: User,
        context: WorkspaceContext,
    ) -> WPSMatchRun:
        revision = self._get(ProductRevision, revision_id, user, context, True)
        if revision.status not in {"review", "approved"}:
            raise HTTPException(409, "产品版本需处于待审核或已批准状态")
        joints = self._targets(revision, requested, affected_only)
        if not joints:
            raise HTTPException(422, "没有需要重新匹配的焊缝")
        capabilities = CapabilityLibraryService(self.db).overview(
            user, context, CapabilityFilters(factory_id=revision.factory_id)
        )["process_capabilities"]
        pack = (
            self.db.query(QualificationRulePack)
            .filter(
                QualificationRulePack.code == "NBT47014_2023",
                QualificationRulePack.status == "published",
            )
            .order_by(QualificationRulePack.published_at.desc())
            .first()
        )
        policy = {
            "weights": {**DEFAULT_WEIGHTS, **weights},
            "ranking": "decision_then_weighted_score",
            "automatic_confirmation": False,
        }
        values = workspace_values(user, context, revision.access_level)
        run = WPSMatchRun(
            id=str(uuid4()),
            revision_id=revision.id,
            trigger_type=trigger,
            status="processing",
            source_data_version=revision.data_version,
            rule_pack_code=pack.code if pack else "NBT47014_2023",
            rule_pack_version=pack.version if pack else "1.0.0",
            capability_snapshot_hash=_hash(capabilities),
            capability_snapshot=capabilities,
            policy_snapshot=policy,
            target_joint_ids=[j.id for j in joints],
            **values,
        )
        self.db.add(run)
        self.db.flush()
        parts = {
            p.id: p
            for p in self.db.query(Part)
            .filter(Part.revision_id == revision.id, Part.is_deleted.is_(False))
            .all()
        }
        reqs = {
            r.weld_joint_id: r
            for r in self.db.query(WeldRequirement)
            .filter(WeldRequirement.revision_id == revision.id)
            .all()
        }
        wps_map = {
            x.id: x
            for x in self.db.query(WPS)
            .filter(WPS.id.in_([c["wps_id"] for c in capabilities] or [-1]))
            .all()
        }
        pqr_map = {
            x.id: x
            for x in self.db.query(PQR)
            .filter(PQR.id.in_([c["pqr_id"] for c in capabilities] or [-1]))
            .all()
        }
        count = 0
        gaps = 0
        for joint in joints:
            requirement = build_weld_requirement(joint, reqs.get(joint.id), parts)
            evaluated = []
            for capability in capabilities:
                wps = wps_map.get(capability["wps_id"])
                pqr = pqr_map.get(capability["pqr_id"])
                if not wps or not pqr:
                    continue
                result = evaluate_candidate(
                    requirement, capability, wps, policy["weights"]
                )
                evaluated.append((capability, wps, pqr, result))
            order = {"eligible": 0, "needs_confirmation": 1, "not_eligible": 2}
            evaluated.sort(
                key=lambda x: (order[x[3]["decision"]], -x[3]["score"], x[1].wps_number)
            )
            has_eligible = any(item[3]["decision"] == "eligible" for item in evaluated)
            has_review = any(
                item[3]["decision"] == "needs_confirmation" for item in evaluated
            )
            for rank, (capability, wps, pqr, result) in enumerate(evaluated, 1):
                candidate = WPSMatchCandidate(
                    id=str(uuid4()),
                    run_id=run.id,
                    weld_joint_id=joint.id,
                    support_link_id=capability["link_id"],
                    wps_id=wps.id,
                    pqr_id=pqr.id,
                    rank=rank,
                    decision=result["decision"],
                    score=result["score"],
                    is_recommended=bool(
                        has_eligible and result["decision"] == "eligible" and rank == 1
                    ),
                    requirement_snapshot=requirement,
                    wps_snapshot=_record_snapshot(wps),
                    pqr_snapshot=_record_snapshot(pqr),
                    qualification_snapshot={
                        "scope": capability.get("qualified_scope"),
                        "evidence": capability.get("evidence"),
                    },
                    rule_snapshot={
                        "rule_pack_id": capability.get("rule_pack_id"),
                        "rule_pack_version": capability.get("rule_pack_version"),
                    },
                    **values,
                )
                self.db.add(candidate)
                self.db.flush()
                count += 1
                self.db.add_all(
                    [
                        WPSMatchCriterion(
                            id=str(uuid4()),
                            candidate_id=candidate.id,
                            sort_order=i,
                            **criterion,
                            **values,
                        )
                        for i, criterion in enumerate(result["criteria"], 1)
                    ]
                )
            if not has_eligible:
                code = (
                    "MATCH_REQUIRES_CONFIRMATION" if has_review else "NO_WPS_COVERAGE"
                )
                message = (
                    "存在边界或信息不足候选，必须由工程师复核" if has_review else "当前已发布能力库没有覆盖该焊缝的 WPS/PQR"
                )
                self.db.add(
                    WPSCapabilityGap(
                        id=str(uuid4()),
                        run_id=run.id,
                        weld_joint_id=joint.id,
                        dimension="overall",
                        code=code,
                        severity="warning" if has_review else "blocking",
                        message=message,
                        requirement_snapshot=requirement,
                        **values,
                    )
                )
                gaps += 1
        run.candidate_count = count
        run.gap_count = gaps
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        self._resolve_stale(revision, [j.id for j in joints])
        self.db.commit()
        self.db.refresh(run)
        return run

    def _resolve_stale(self, revision, joint_ids):
        for state in (
            self.db.query(EngineeringDependencyState)
            .filter(
                EngineeringDependencyState.revision_id == revision.id,
                EngineeringDependencyState.dependency_type == "matching",
                EngineeringDependencyState.status == "stale",
            )
            .all()
        ):
            affected = set(state.affected_joint_ids or [])
            if state.scope == "all" or affected & set(joint_ids):
                state.status = "fresh"
                state.resolved_at = datetime.utcnow()

    def detail(self, run_id: str, user, context) -> dict[str, Any]:
        run = self._get(WPSMatchRun, run_id, user, context)
        candidates = (
            self.db.query(WPSMatchCandidate)
            .filter(WPSMatchCandidate.run_id == run.id)
            .order_by(WPSMatchCandidate.weld_joint_id, WPSMatchCandidate.rank)
            .all()
        )
        ids = [c.id for c in candidates]
        criteria = (
            self.db.query(WPSMatchCriterion)
            .filter(WPSMatchCriterion.candidate_id.in_(ids or ["-"]))
            .order_by(WPSMatchCriterion.sort_order)
            .all()
        )
        by_candidate = {cid: [] for cid in ids}
        for item in criteria:
            by_candidate[item.candidate_id].append(item)
        gaps = (
            self.db.query(WPSCapabilityGap)
            .filter(WPSCapabilityGap.run_id == run.id)
            .all()
        )
        freezes = (
            self.db.query(WPSMatchFreeze).filter(WPSMatchFreeze.run_id == run.id).all()
        )
        return {
            "run": run,
            "candidates": candidates,
            "criteria": by_candidate,
            "gaps": gaps,
            "freezes": freezes,
        }

    def list_runs(self, revision_id: str, user, context):
        self._get(ProductRevision, revision_id, user, context)
        return (
            self.db.query(WPSMatchRun)
            .filter(WPSMatchRun.revision_id == revision_id)
            .order_by(WPSMatchRun.created_at.desc())
            .all()
        )

    def approved_freezes(self, revision_id: str, user, context):
        self._get(ProductRevision, revision_id, user, context)
        rows = (
            self.db.query(WPSMatchFreeze)
            .join(WPSMatchRun, WPSMatchRun.id == WPSMatchFreeze.run_id)
            .filter(
                WPSMatchFreeze.revision_id == revision_id,
                WPSMatchRun.status == "approved",
            )
            .order_by(WPSMatchFreeze.frozen_at.desc())
            .all()
        )
        latest = {}
        for item in rows:
            latest.setdefault(item.weld_joint_id, item)
        return list(latest.values())

    def confirm(self, candidate_id: str, status: str, note: str | None, user, context):
        candidate = self._get(WPSMatchCandidate, candidate_id, user, context, True)
        run = self._get(WPSMatchRun, candidate.run_id, user, context, True)
        if run.status != "completed":
            raise HTTPException(409, "当前匹配运行不可确认")
        if status == "confirmed" and candidate.decision == "not_eligible":
            raise HTTPException(409, "存在明确不通过项的候选不能确认")
        if (
            status == "confirmed"
            and candidate.decision == "needs_confirmation"
            and not (note or "").strip()
        ):
            raise HTTPException(422, "边界或信息不足候选必须填写确认依据")
        if status == "confirmed":
            self.db.query(WPSMatchCandidate).filter(
                WPSMatchCandidate.run_id == run.id,
                WPSMatchCandidate.weld_joint_id == candidate.weld_joint_id,
                WPSMatchCandidate.id != candidate.id,
                WPSMatchCandidate.confirmation_status == "confirmed",
            ).update(
                {"confirmation_status": "rejected", "confirmation_note": "由另一候选替代"},
                synchronize_session=False,
            )
        candidate.confirmation_status = status
        candidate.confirmation_note = note
        candidate.confirmed_by = user.id
        candidate.confirmed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def approve(self, run_id: str, note: str | None, user, context):
        run = self._get(WPSMatchRun, run_id, user, context, True)
        if run.status != "completed":
            raise HTTPException(409, "当前匹配运行不可批准")
        revision = self._get(ProductRevision, run.revision_id, user, context)
        if revision.status != "approved":
            raise HTTPException(409, "产品图纸版本批准后才能批准匹配结果")
        if revision.data_version != run.source_data_version:
            raise HTTPException(409, "焊缝需求已变化，请重新运行匹配")
        confirmed = (
            self.db.query(WPSMatchCandidate)
            .filter(
                WPSMatchCandidate.run_id == run.id,
                WPSMatchCandidate.confirmation_status == "confirmed",
            )
            .all()
        )
        by_joint = {c.weld_joint_id: c for c in confirmed}
        missing = [jid for jid in run.target_joint_ids if jid not in by_joint]
        if missing:
            raise HTTPException(
                409, {"message": "每条焊缝必须人工确认一个候选", "joint_ids": missing}
            )
        current_capabilities = CapabilityLibraryService(self.db).overview(
            user, context, CapabilityFilters(factory_id=revision.factory_id)
        )["process_capabilities"]
        current_by_link = {item["link_id"]: item for item in current_capabilities}
        values = workspace_values(user, context, run.access_level)
        for joint_id, candidate in by_joint.items():
            current_wps = self.db.query(WPS).filter(WPS.id == candidate.wps_id).first()
            current_pqr = self.db.query(PQR).filter(PQR.id == candidate.pqr_id).first()
            current_link = (
                self.db.query(WPSPQRSupportLink)
                .filter(WPSPQRSupportLink.id == candidate.support_link_id)
                .first()
            )
            current_capability = current_by_link.get(candidate.support_link_id)
            if (
                current_wps is None
                or current_pqr is None
                or current_link is None
                or current_wps.status != "approved"
                or not current_wps.is_active
                or current_pqr.status != "approved"
                or not current_pqr.is_active
                or current_link.confirmation_status != "confirmed"
                or not current_link.is_active
                or current_capability is None
                or _hash(
                    {
                        "scope": current_capability.get("qualified_scope"),
                        "evidence": current_capability.get("evidence"),
                    }
                )
                != _hash(candidate.qualification_snapshot)
                or str(current_capability.get("rule_pack_version"))
                != str(candidate.rule_snapshot.get("rule_pack_version"))
                or _hash(_record_snapshot(current_wps)) != _hash(candidate.wps_snapshot)
                or _hash(_record_snapshot(current_pqr)) != _hash(candidate.pqr_snapshot)
            ):
                raise HTTPException(409, "候选 WPS/PQR 或支持关系已变化，请重新匹配")
            snapshot = {
                "revision": {
                    "id": revision.id,
                    "revision_number": revision.revision_number,
                    "drawing_sha256": revision.drawing_sha256,
                    "data_version": revision.data_version,
                },
                "requirement": candidate.requirement_snapshot,
                "wps": candidate.wps_snapshot,
                "pqr": candidate.pqr_snapshot,
                "qualification": candidate.qualification_snapshot,
                "rule": candidate.rule_snapshot,
                "confirmation": {
                    "user_id": user.id,
                    "note": candidate.confirmation_note or note,
                },
            }
            self.db.add(
                WPSMatchFreeze(
                    id=str(uuid4()),
                    run_id=run.id,
                    candidate_id=candidate.id,
                    revision_id=revision.id,
                    weld_joint_id=joint_id,
                    frozen_by=user.id,
                    weld_requirement_hash=_hash(candidate.requirement_snapshot),
                    wps_snapshot_hash=_hash(candidate.wps_snapshot),
                    pqr_snapshot_hash=_hash(candidate.pqr_snapshot),
                    rule_snapshot_hash=_hash(candidate.rule_snapshot),
                    frozen_snapshot=snapshot,
                    **values,
                )
            )
        run.status = "approved"
        run.approved_by = user.id
        run.approved_at = datetime.utcnow()
        active_joint_count = (
            self.db.query(WeldJoint)
            .filter(
                WeldJoint.revision_id == revision.id,
                WeldJoint.is_deleted.is_(False),
            )
            .count()
        )
        # A partial recalculation only replaces the selected joints. Keep older
        # approved runs available for unaffected joints; consumers select the
        # newest approved freeze per weld joint.
        if len(set(run.target_joint_ids or [])) == active_joint_count:
            self.db.query(WPSMatchRun).filter(
                WPSMatchRun.revision_id == run.revision_id,
                WPSMatchRun.status == "approved",
                WPSMatchRun.id != run.id,
            ).update({"status": "superseded"}, synchronize_session=False)
        self.db.commit()
        self.db.refresh(run)
        return run

    def link_gap(
        self, gap_id: str, ppqr_id: int | None, reference: str | None, user, context
    ):
        gap = self._get(WPSCapabilityGap, gap_id, user, context, True)
        if ppqr_id is not None:
            self._get(PPQR, ppqr_id, user, context)
        gap.linked_ppqr_id = ppqr_id
        gap.qualification_plan_reference = reference
        gap.status = "linked"
        self.db.commit()
        self.db.refresh(gap)
        return gap

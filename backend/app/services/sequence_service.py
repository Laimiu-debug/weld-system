"""P5 deterministic pressure-vessel weld sequence planning and validation."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.data_access import (
    DataAccessAction,
    DataAccessMiddleware,
    WorkspaceContext,
)
from app.models.approval import ApprovalInstance, ApprovalStatus
from app.models.engineering import (
    EngineeringDependencyState,
    Part,
    Product,
    ProductRevision,
    WeldJoint,
    WeldRequirement,
)
from app.models.matching import WPSMatchFreeze, WPSMatchRun
from app.models.sequence import StepDependency, WeldSequenceRevision, WeldSequenceStep
from app.models.production_release import (
    ProductionReleaseBatch,
    ProductionSequenceChangeRequest,
)
from app.models.user import User
from app.services.approval_service import ApprovalService
from app.services.engineering_service import workspace_values
from app.services.sequence_structure_service import (
    resolve_structure,
    structure_joint_family,
    expand_weld_strategies,
)
from app.services.sequence_change_service import sync_change_approval


TEMPLATE_CODE = "PRESSURE_VESSEL_V1"
TEMPLATE_VERSION = "1.0.0"
DEFAULT_STRATEGIES = {
    "symmetric": True,
    "segmented": False,
    "skip_weld": False,
    "closed_space_first": True,
}


def change_request_allows_recalculation(release_id: str, request) -> bool:
    """Only an approved request for the exact release unlocks recalculation."""
    return bool(
        request
        and request.production_release_id == release_id
        and request.status == "approved"
    )


def snapshot_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _norm(value: Any) -> str:
    return re.sub(r"[\s_\-/]+", "", str(value or "")).casefold()


def classify_joint(joint: Any, parts: dict[str, Any]) -> tuple[str, int, str]:
    names = " ".join(
        str(getattr(parts.get(part_id), "name", "") or "")
        for part_id in (
            getattr(joint, "part_a_id", None),
            getattr(joint, "part_b_id", None),
        )
    )
    value = _norm(names + " " + str(getattr(joint, "weld_number", "")))
    if any(key in value for key in ("接管", "管口", "nozzle")):
        return "接管安装", 40, "nozzle"
    if any(key in value for key in ("封头", "head")):
        return "封头组装", 30, "head"
    if any(key in value for key in ("纵缝", "longitudinal")):
        return "筒节制造", 10, "shell"
    if any(key in value for key in ("环缝", "circumferential")):
        return "筒体组装", 20, "shell"
    if any(key in value for key in ("筒体", "筒节", "shell")):
        return "筒体组装", 20, "shell"
    return "主体焊接", 25, "general"


def _is_internal(requirement: Any) -> bool:
    text = _norm(getattr(requirement, "special_requirements", None))
    return any(key in text for key in ("封闭前", "内侧", "内部", "不可达", "closedspace"))


def _strategy_tags(strategies: dict[str, bool]) -> list[str]:
    labels = {
        "symmetric": "symmetric",
        "segmented": "segmented",
        "skip_weld": "skip_weld",
        "closed_space_first": "closed_space_first",
    }
    return [
        labels[key] for key, active in strategies.items() if active and key in labels
    ]


def topological_order(
    step_codes: list[str],
    edges: list[tuple[str, str]],
    preferred: list[str] | None = None,
    priorities: dict[str, tuple[int, str]] | None = None,
) -> tuple[list[str], list[str]]:
    """Stable Kahn sort. Candidate/AI order is only a tie-breaker."""
    nodes = set(step_codes)
    incoming = {code: 0 for code in nodes}
    outgoing: dict[str, set[str]] = defaultdict(set)
    errors = []
    for before, after in edges:
        if before not in nodes or after not in nodes:
            errors.append(f"依赖引用不存在步骤：{before} -> {after}")
            continue
        if before == after:
            errors.append(f"步骤不能依赖自身：{before}")
            continue
        if after not in outgoing[before]:
            outgoing[before].add(after)
            incoming[after] += 1
    preferred_rank = {code: index for index, code in enumerate(preferred or [])}
    default_rank = len(preferred_rank) + len(nodes)
    priorities = priorities or {}

    def key(code: str):
        return (
            preferred_rank.get(code, default_rank),
            priorities.get(code, (999, code)),
            code,
        )

    ready = sorted((code for code, count in incoming.items() if count == 0), key=key)
    ordered = []
    while ready:
        current = ready.pop(0)
        ordered.append(current)
        for child in sorted(outgoing[current]):
            incoming[child] -= 1
            if incoming[child] == 0:
                ready.append(child)
                ready.sort(key=key)
    if len(ordered) != len(nodes):
        cyclic = sorted(code for code, count in incoming.items() if count > 0)
        errors.append(f"检测到循环依赖：{', '.join(cyclic)}")
    return ordered, errors


def validate_sequence(
    steps: list[dict[str, Any]], dependencies: list[dict[str, Any]]
) -> dict[str, Any]:
    codes = [item["step_code"] for item in steps]
    issues: list[dict[str, Any]] = []
    if len(codes) != len(set(codes)):
        issues.append(
            {"code": "DUPLICATE_STEP", "severity": "error", "message": "步骤编码重复"}
        )
    edges = [
        (item["predecessor_code"], item["successor_code"]) for item in dependencies
    ]
    _, graph_errors = topological_order(codes, edges)
    issues.extend(
        {"code": "INVALID_GRAPH", "severity": "error", "message": message}
        for message in graph_errors
    )
    by_code = {item["step_code"]: item for item in steps}
    order = {item["step_code"]: item["order_index"] for item in steps}
    for before, after in edges:
        if before in order and after in order and order[before] >= order[after]:
            issues.append(
                {
                    "code": "ORDER_VIOLATION",
                    "severity": "error",
                    "message": f"{before} 必须先于 {after}",
                    "step_codes": [before, after],
                }
            )
    incoming: dict[str, list[str]] = defaultdict(list)
    for before, after in edges:
        incoming[after].append(before)
    for step in steps:
        code = step["step_code"]
        if step["step_type"] == "weld" and not step.get("match_freeze_id"):
            issues.append(
                {
                    "code": "MISSING_APPROVED_WPS",
                    "severity": "error",
                    "message": f"{code} 缺少已批准的 WPS/PQR 匹配快照",
                    "step_codes": [code],
                }
            )
        if step["step_type"] == "weld" and not any(
            by_code.get(item, {}).get("step_type") == "assembly"
            for item in incoming.get(code, [])
        ):
            issues.append(
                {
                    "code": "MISSING_ASSEMBLY_PREREQUISITE",
                    "severity": "error",
                    "message": f"{code} 缺少装配前置步骤",
                    "step_codes": [code],
                }
            )
        if step["step_type"] in {"pwht", "inspection"} and not incoming.get(code):
            issues.append(
                {
                    "code": "MISSING_PROCESS_PREREQUISITE",
                    "severity": "error",
                    "message": f"{code} 缺少制造或检验前置步骤",
                    "step_codes": [code],
                }
            )
        if step["step_type"] == "nde" and not any(
            by_code.get(item, {}).get("step_type") == "weld"
            for item in incoming.get(code, [])
        ):
            issues.append(
                {
                    "code": "MISSING_WELD_PREREQUISITE",
                    "severity": "error",
                    "message": f"{code} 缺少焊接前置步骤",
                    "step_codes": [code],
                }
            )
    return {
        "valid": not any(item["severity"] == "error" for item in issues),
        "issues": issues,
        "step_count": len(steps),
        "dependency_count": len(dependencies),
        "checked_at": "deterministic",
    }


def compare_sequence_steps(
    left_steps: list[dict[str, Any]], right_steps: list[dict[str, Any]]
) -> dict[str, Any]:
    left = {item["step_code"]: item for item in left_steps}
    right = {item["step_code"]: item for item in right_steps}
    return {
        "added": sorted(set(right) - set(left)),
        "removed": sorted(set(left) - set(right)),
        "moved": [
            {
                "step_code": code,
                "from": left[code]["order_index"],
                "to": right[code]["order_index"],
            }
            for code in sorted(set(left) & set(right))
            if left[code]["order_index"] != right[code]["order_index"]
        ],
    }


def is_production_eligible(
    status: str,
    frozen_hash: str | None,
    source_data_version: int,
    current_data_version: int,
) -> bool:
    return bool(
        status == "approved"
        and frozen_hash
        and source_data_version == current_data_version
    )


def build_pressure_vessel_blueprint(
    joints: list[Any],
    requirements: dict[str, Any],
    parts: dict[str, Any],
    freezes: dict[str, Any],
    strategies: dict[str, bool] | None = None,
    preferred_codes: list[str] | None = None,
    structure: dict | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    policy = {**DEFAULT_STRATEGIES, **(strategies or {})}
    steps: list[dict[str, Any]] = []
    dependencies: list[dict[str, Any]] = []
    priorities: dict[str, tuple[int, str]] = {}
    family_of = (
        lambda joint: structure_joint_family(joint, structure)
        if structure
        else classify_joint(joint, parts)
    )
    generic = bool(structure and structure["template"] == "generic")

    def add_step(code, step_type, title, phase, priority, **extra):
        steps.append(
            {
                "step_code": code,
                "step_type": step_type,
                "title": title,
                "phase": phase,
                "order_index": 0,
                "weld_joint_id": extra.get("weld_joint_id"),
                "match_freeze_id": extra.get("match_freeze_id"),
                "is_locked": extra.get("is_locked", False),
                "constraint_tags": extra.get("constraint_tags", []),
                "process_parameters": extra.get("process_parameters", {}),
                "inspection_node": extra.get("inspection_node", {}),
                "explanation": extra.get("explanation", "由已选结构模板确定"),
                "source_snapshot": extra.get("source_snapshot", {}),
            }
        )
        priorities[code] = (priority, code)

    def add_edge(before, after, dependency_type, explanation):
        dependencies.append(
            {
                "predecessor_code": before,
                "successor_code": after,
                "dependency_type": dependency_type,
                "is_mandatory": True,
                "explanation": explanation,
            }
        )

    if generic:
        add_step("PREP-GENERAL", "assembly", "零件备料与坡口准备", "材料与成形", 1, is_locked=True)
    else:
        add_step("PREP-SHELL", "assembly", "筒板下料、卷制与校圆", "材料与成形", 1, is_locked=True)
        add_step("PREP-HEAD", "assembly", "封头成形与坡口准备", "材料与成形", 2, is_locked=True)
        add_step("PREP-NOZZLE", "assembly", "接管与开孔件预制", "材料与成形", 3, is_locked=True)
    terminals = []
    closure_sensitive = []
    head_welds = []
    shared_treatments = {}
    sorted_joints = sorted(
        joints, key=lambda item: (family_of(item)[1], item.weld_number)
    )
    if policy["symmetric"]:
        grouped: dict[int, list[Any]] = defaultdict(list)
        for item in sorted_joints:
            grouped[family_of(item)[1]].append(item)
        sorted_joints = []
        for key in sorted(grouped):
            group = grouped[key]
            while group:
                sorted_joints.append(group.pop(0))
                if group:
                    sorted_joints.append(group.pop(-1))

    for joint in sorted_joints:
        requirement = requirements.get(joint.id)
        freeze = freezes.get(joint.id)
        phase, priority, family = family_of(joint)
        asm = f"ASM-{joint.id}"
        weld = f"WELD-{joint.id}"
        base = (
            "PREP-NOZZLE"
            if family == "nozzle"
            else "PREP-HEAD"
            if family == "head"
            else "PREP-SHELL"
        )
        if generic:
            base = "PREP-GENERAL"
        part_names = [
            getattr(parts.get(joint.part_a_id), "name", None),
            getattr(parts.get(joint.part_b_id), "name", None),
        ]
        add_step(
            asm,
            "assembly",
            f"组对焊缝 {joint.weld_number}",
            phase,
            priority * 10,
            weld_joint_id=joint.id,
            explanation=f"按{phase}模板完成定位、间隙和错边检查",
            source_snapshot={"parts": part_names, "joint": joint.weld_number},
        )
        tags = _strategy_tags(policy)
        if _is_internal(requirement):
            tags.append("closed_space")
        frozen = getattr(freeze, "frozen_snapshot", {}) if freeze else {}
        add_step(
            weld,
            "weld",
            f"焊接 {joint.weld_number}",
            phase,
            priority * 10 + 1,
            weld_joint_id=joint.id,
            match_freeze_id=getattr(freeze, "id", None),
            constraint_tags=tags,
            process_parameters={
                "strategy": [item for item in tags if item != "closed_space"],
                "wps": frozen.get("wps", {}),
                "pqr": frozen.get("pqr", {}),
                "requirement": frozen.get("requirement", {}),
            },
            explanation="采用已批准 P4 匹配快照；策略只改变施工方式，不绕过资格约束",
            source_snapshot=frozen,
        )
        add_edge(base, asm, "assembly", "零件成形和坡口准备完成后才能组对")
        add_edge(asm, weld, "assembly", "组对尺寸检查合格后才能焊接")
        terminal = weld
        methods = list(getattr(requirement, "nde_methods", None) or [])
        needs_pwht = bool(getattr(requirement, "pwht_required", False))
        if getattr(requirement, "treatment_plan", None) and not needs_pwht:
            raise HTTPException(422, "热处理计划与是否需要热处理的要求冲突")
        if methods and not needs_pwht:
            nde = f"NDE-{joint.id}"
            add_step(
                nde,
                "nde",
                f"{joint.weld_number} 无损检测",
                "无损检测",
                priority * 10 + 2,
                weld_joint_id=joint.id,
                match_freeze_id=getattr(freeze, "id", None),
                inspection_node={
                    "methods": methods,
                    "rate": getattr(requirement, "nde_rate", None),
                },
                explanation="检测方法和比例来自已审核焊缝要求",
            )
            add_edge(weld, nde, "nde", "焊接完成后执行规定的无损检测")
            terminal = nde
        if needs_pwht:
            from app.services.sequence_treatment_service import add_treatment_steps
            terminal = add_treatment_steps(joint, requirement, freeze, add_step, add_edge,
                shared_treatments, [f"WELD-{item.id}" for item in joints])
        is_closing = (
            joint.id in structure.get("closure_joint_ids", [])
            if structure
            else family == "head"
        )
        if _is_internal(requirement) and not is_closing:
            closure_sensitive.append(terminal)
        terminals.append(terminal)
        if is_closing:
            head_welds.append(weld)

    if head_welds:
        add_step(
            "CLOSE-VESSEL",
            "closure",
            "最终封闭空间确认",
            "封闭确认",
            295,
            is_locked=True,
            constraint_tags=["closed_space"],
            explanation="确认所有内侧焊接和检查完成后方可最终封闭",
        )
        for code in closure_sensitive:
            add_edge(code, "CLOSE-VESSEL", "closed_space", "封闭后不可达工作必须提前完成")
        for code in head_welds:
            add_edge("CLOSE-VESSEL", code, "accessibility", "封闭确认是最终封头焊接的前置条件")
    final_inputs = terminals
    add_step(
        "FINAL-INSPECTION",
        "inspection",
        "最终检验与文件核对",
        "最终检验",
        999,
        is_locked=True,
        inspection_node={"type": "final_release"},
        explanation="汇总焊接、NDE、PWHT记录并确认放行条件",
    )
    for code in final_inputs:
        add_edge(code, "FINAL-INSPECTION", "nde", "所有制造与检验节点完成后才能最终检验")

    if structure is not None:
        steps, dependencies = expand_weld_strategies(
            steps, dependencies, joints, policy, structure.get("segment_length_mm", 500)
        )
    if len(steps) > 2000:
        raise HTTPException(422, "焊序超过 2000 步，请调整分段长度或拆分产品")
    codes = [item["step_code"] for item in steps]
    valid_preferred = [code for code in (preferred_codes or []) if code in set(codes)]
    if policy["symmetric"]:
        # Keep the interleaved construction order as the fallback preference.
        # Mandatory edges still win; explicit AI/user preferences remain first.
        selected = set(valid_preferred)
        valid_preferred.extend(code for code in codes if code not in selected)
    order, graph_errors = topological_order(
        codes,
        [(item["predecessor_code"], item["successor_code"]) for item in dependencies],
        valid_preferred,
        priorities,
    )
    if graph_errors:
        raise ValueError("；".join(graph_errors))
    by_code = {item["step_code"]: item for item in steps}
    ordered_steps = []
    for index, code in enumerate(order, 1):
        item = by_code[code]
        item["order_index"] = index
        ordered_steps.append(item)
    return ordered_steps, dependencies, validate_sequence(ordered_steps, dependencies)


class WeldSequenceService:
    def __init__(self, db: Session):
        self.db = db
        self.access = DataAccessMiddleware(db)

    def _get(
        self, model, item_id: str, user: User, context: WorkspaceContext, edit=False
    ):
        item = self.db.query(model).filter(model.id == item_id).first()
        if item is None:
            raise HTTPException(404, "焊序数据不存在")
        self.access.check_access(
            user,
            item,
            DataAccessAction.EDIT if edit else DataAccessAction.VIEW,
            context,
        )
        return item

    def _approved_freezes(self, revision_id: str) -> dict[str, WPSMatchFreeze]:
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
        result = {}
        for item in rows:
            result.setdefault(item.weld_joint_id, item)
        return result

    def generate(
        self,
        revision_id: str,
        strategies: dict[str, bool],
        ai_step_codes: list[str] | None,
        ai_explanation: str | None,
        user: User,
        context: WorkspaceContext,
        parent_id: str | None = None,
        change_summary: str | None = None,
        change_request_id: str | None = None,
        structure: dict | None = None,
    ) -> WeldSequenceRevision:
        revision = self._get(ProductRevision, revision_id, user, context, True)
        self.db.refresh(revision, with_for_update=True)
        approved_change = None
        released = (
            self.db.query(ProductionReleaseBatch)
            .filter(
                ProductionReleaseBatch.product_revision_id == revision.id,
                ProductionReleaseBatch.status == "released",
            )
            .with_for_update()
            .first()
        )
        if released:
            approved_change = (
                self.db.query(ProductionSequenceChangeRequest)
                .filter(
                    ProductionSequenceChangeRequest.id == change_request_id,
                    ProductionSequenceChangeRequest.production_release_id
                    == released.id,
                )
                .first()
            )
            sync_change_approval(self.db, approved_change)
            if (
                not change_request_allows_recalculation(released.id, approved_change)
                or parent_id
                not in {
                    released.sequence_revision_id,
                    getattr(approved_change, "proposed_sequence_revision_id", None),
                }
                or not parent_id
            ):
                raise HTTPException(409, "已发布焊序重算必须绑定已批准的变更申请")
        if revision.status != "approved":
            raise HTTPException(409, "产品图纸版本批准后才能生成正式候选焊序")
        product = (
            self.db.query(Product).filter(Product.id == revision.product_id).first()
        )
        joints = (
            self.db.query(WeldJoint)
            .filter(
                WeldJoint.revision_id == revision.id, WeldJoint.is_deleted.is_(False)
            )
            .order_by(WeldJoint.weld_number)
            .all()
        )
        if not joints:
            raise HTTPException(422, "产品版本没有可编排焊缝")
        parts = {
            item.id: item
            for item in self.db.query(Part)
            .filter(Part.revision_id == revision.id, Part.is_deleted.is_(False))
            .all()
        }
        requirements = {
            item.weld_joint_id: item
            for item in self.db.query(WeldRequirement)
            .filter(WeldRequirement.revision_id == revision.id)
            .all()
        }
        freezes = self._approved_freezes(revision.id)
        structure = resolve_structure(parts, joints, structure)
        steps, dependencies, validation = build_pressure_vessel_blueprint(
            joints, requirements, parts, freezes, strategies, ai_step_codes, structure
        )
        from app.services.sequence_source_service import rule_baseline
        source_matches = [
            {
                "id": item.id,
                "joint_id": item.weld_joint_id,
                "frozen_hash": snapshot_hash(item.frozen_snapshot),
                "snapshot": item.frozen_snapshot,
                "rule_baseline": rule_baseline(self.db, item.frozen_snapshot),
            }
            for item in sorted(freezes.values(), key=lambda value: value.weld_joint_id)
        ]
        version = (
            self.db.query(func.max(WeldSequenceRevision.version_number))
            .filter(WeldSequenceRevision.product_revision_id == revision.id)
            .scalar()
            or 0
        ) + 1
        values = workspace_values(user, context, revision.access_level)
        sequence = WeldSequenceRevision(
            id=str(uuid4()),
            product_revision_id=revision.id,
            version_number=version,
            parent_revision_id=parent_id,
            status="draft",
            source_data_version=revision.data_version,
            template_code=TEMPLATE_CODE
            if structure["template"] == "pressure_vessel"
            else "GENERIC_WELDMENT_V1",
            template_version="3.0.0",
            strategy_snapshot={
                **DEFAULT_STRATEGIES,
                **strategies,
                "_structure": structure,
            },
            source_match_snapshot=source_matches,
            source_match_hash=snapshot_hash([{k:v for k,v in item.items() if k != "rule_baseline"} for item in source_matches]),
            candidate_source="ai_assisted" if ai_step_codes else "deterministic",
            candidate_explanation=ai_explanation,
            validation_result=validation,
            validation_hash=snapshot_hash(validation),
            change_summary=change_summary or f"{product.product_type or '压力容器'}初版焊序",
            **values,
        )
        self.db.add(sequence)
        self.db.flush()
        if approved_change is not None:
            approved_change.proposed_sequence_revision_id = sequence.id
        step_by_code = {}
        for item in steps:
            step = WeldSequenceStep(
                id=str(uuid4()), sequence_revision_id=sequence.id, **item, **values
            )
            self.db.add(step)
            self.db.flush()
            step_by_code[item["step_code"]] = step
        for item in dependencies:
            self.db.add(
                StepDependency(
                    id=str(uuid4()),
                    sequence_revision_id=sequence.id,
                    predecessor_step_id=step_by_code[item["predecessor_code"]].id,
                    successor_step_id=step_by_code[item["successor_code"]].id,
                    dependency_type=item["dependency_type"],
                    is_mandatory=item["is_mandatory"],
                    explanation=item["explanation"],
                    **values,
                )
            )
        self._resolve_dependency(revision)
        self.db.commit()
        self.db.refresh(sequence)
        return sequence

    def _resolve_dependency(self, revision):
        for item in self.db.query(EngineeringDependencyState).filter(
            EngineeringDependencyState.revision_id == revision.id,
            EngineeringDependencyState.dependency_type == "sequence",
            EngineeringDependencyState.status == "stale",
        ):
            item.status = "fresh"
            item.resolved_at = datetime.utcnow()

    def list_revisions(self, product_revision_id: str, user, context):
        self._get(ProductRevision, product_revision_id, user, context)
        return (
            self.db.query(WeldSequenceRevision)
            .filter(WeldSequenceRevision.product_revision_id == product_revision_id)
            .order_by(WeldSequenceRevision.version_number.desc())
            .all()
        )

    def detail(self, sequence_id: str, user, context) -> dict[str, Any]:
        sequence = self._get(WeldSequenceRevision, sequence_id, user, context)
        self._sync_status(sequence)
        steps = (
            self.db.query(WeldSequenceStep)
            .filter(WeldSequenceStep.sequence_revision_id == sequence.id)
            .order_by(WeldSequenceStep.order_index)
            .all()
        )
        dependencies = (
            self.db.query(StepDependency)
            .filter(StepDependency.sequence_revision_id == sequence.id)
            .all()
        )
        from app.services.sequence_source_service import source_impact
        return {"revision": sequence, "steps": steps, "dependencies": dependencies, "source_impact": source_impact(self.db, sequence)}

    def _blueprint(self, sequence_id: str):
        steps = (
            self.db.query(WeldSequenceStep)
            .filter(WeldSequenceStep.sequence_revision_id == sequence_id)
            .order_by(WeldSequenceStep.order_index)
            .all()
        )
        dependencies = (
            self.db.query(StepDependency)
            .filter(StepDependency.sequence_revision_id == sequence_id)
            .all()
        )
        code_by_id = {item.id: item.step_code for item in steps}
        step_values = [
            {
                key: getattr(item, key)
                for key in (
                    "step_code",
                    "step_type",
                    "title",
                    "order_index",
                    "phase",
                    "weld_joint_id",
                    "match_freeze_id",
                    "is_locked",
                    "constraint_tags",
                    "process_parameters",
                    "inspection_node",
                    "explanation",
                    "source_snapshot",
                )
            }
            for item in steps
        ]
        dep_values = [
            {
                "predecessor_code": code_by_id.get(item.predecessor_step_id),
                "successor_code": code_by_id.get(item.successor_step_id),
                "dependency_type": item.dependency_type,
                "is_mandatory": item.is_mandatory,
                "explanation": item.explanation,
            }
            for item in dependencies
        ]
        return steps, dependencies, step_values, dep_values

    def reorder(
        self,
        sequence_id: str,
        ordered_step_ids: list[str],
        locked_step_ids: list[str],
        summary: str,
        user,
        context,
    ):
        parent = self._get(WeldSequenceRevision, sequence_id, user, context, True)
        if parent.status not in {"draft", "rejected", "returned"}:
            raise HTTPException(409, "待审批或已批准焊序不能直接调整")
        steps, dependencies, _, _ = self._blueprint(parent.id)
        by_id = {item.id: item for item in steps}
        if set(ordered_step_ids) != set(by_id):
            raise HTTPException(422, "调整顺序必须完整包含当前方案全部步骤")
        old_order = {item.id: item.order_index for item in steps}
        new_order = {
            item_id: index for index, item_id in enumerate(ordered_step_ids, 1)
        }
        moved_locked = [
            item.step_code
            for item in steps
            if item.is_locked and old_order[item.id] != new_order[item.id]
        ]
        if moved_locked:
            raise HTTPException(422, {"message": "锁定步骤不能移动", "steps": moved_locked})
        code_by_id = {item.id: item.step_code for item in steps}
        violations = [
            (code_by_id[item.predecessor_step_id], code_by_id[item.successor_step_id])
            for item in dependencies
            if item.is_mandatory
            and new_order[item.predecessor_step_id] >= new_order[item.successor_step_id]
        ]
        if violations:
            raise HTTPException(422, {"message": "调整违反确定性依赖", "edges": violations})
        version = (
            self.db.query(func.max(WeldSequenceRevision.version_number))
            .filter(
                WeldSequenceRevision.product_revision_id == parent.product_revision_id
            )
            .scalar()
            or 0
        ) + 1
        values = workspace_values(user, context, parent.access_level)
        child = WeldSequenceRevision(
            id=str(uuid4()),
            product_revision_id=parent.product_revision_id,
            version_number=version,
            parent_revision_id=parent.id,
            status="draft",
            source_data_version=parent.source_data_version,
            template_code=parent.template_code,
            template_version=parent.template_version,
            strategy_snapshot=parent.strategy_snapshot,
            source_match_snapshot=parent.source_match_snapshot,
            source_match_hash=parent.source_match_hash,
            candidate_source="manual",
            candidate_explanation="工程师在确定性依赖允许范围内调整",
            change_summary=summary,
            **values,
        )
        self.db.add(child)
        self.db.flush()
        new_by_old = {}
        step_values = []
        for old_id in ordered_step_ids:
            old = by_id[old_id]
            data = {
                key: getattr(old, key)
                for key in (
                    "step_code",
                    "step_type",
                    "title",
                    "phase",
                    "weld_joint_id",
                    "match_freeze_id",
                    "constraint_tags",
                    "process_parameters",
                    "inspection_node",
                    "explanation",
                    "source_snapshot",
                )
            }
            data["order_index"] = new_order[old_id]
            data["is_locked"] = old.is_locked or old_id in set(locked_step_ids)
            new = WeldSequenceStep(
                id=str(uuid4()), sequence_revision_id=child.id, **data, **values
            )
            self.db.add(new)
            self.db.flush()
            new_by_old[old_id] = new
            step_values.append(data)
        dep_values = []
        for old in dependencies:
            data = {
                "dependency_type": old.dependency_type,
                "is_mandatory": old.is_mandatory,
                "explanation": old.explanation,
            }
            self.db.add(
                StepDependency(
                    id=str(uuid4()),
                    sequence_revision_id=child.id,
                    predecessor_step_id=new_by_old[old.predecessor_step_id].id,
                    successor_step_id=new_by_old[old.successor_step_id].id,
                    **data,
                    **values,
                )
            )
            dep_values.append(
                {
                    **data,
                    "predecessor_code": code_by_id[old.predecessor_step_id],
                    "successor_code": code_by_id[old.successor_step_id],
                }
            )
        for request in (
            self.db.query(ProductionSequenceChangeRequest)
            .filter(
                ProductionSequenceChangeRequest.proposed_sequence_revision_id
                == parent.id,
                ProductionSequenceChangeRequest.status == "approved",
            )
            .all()
        ):
            request.proposed_sequence_revision_id = child.id
        child.validation_result = validate_sequence(step_values, dep_values)
        child.validation_hash = snapshot_hash(child.validation_result)
        self.db.commit()
        self.db.refresh(child)
        return child

    def compare(self, left_id: str, right_id: str, user, context):
        left = self._get(WeldSequenceRevision, left_id, user, context)
        right = self._get(WeldSequenceRevision, right_id, user, context)
        if left.product_revision_id != right.product_revision_id:
            raise HTTPException(422, "只能比较同一产品版本的焊序")
        left_steps = self._blueprint(left.id)[2]
        right_steps = self._blueprint(right.id)[2]
        difference = compare_sequence_steps(left_steps, right_steps)
        return {
            "left_id": left.id,
            "right_id": right.id,
            **difference,
            "strategy_changed": left.strategy_snapshot != right.strategy_snapshot,
        }

    def approval_snapshot(self, sequence_id: str) -> dict[str, Any]:
        sequence = (
            self.db.query(WeldSequenceRevision)
            .filter(WeldSequenceRevision.id == sequence_id)
            .one()
        )
        _, _, steps, dependencies = self._blueprint(sequence.id)
        return {
            "sequence": {
                "id": sequence.id,
                "product_revision_id": sequence.product_revision_id,
                "version_number": sequence.version_number,
                "source_data_version": sequence.source_data_version,
                "template_code": sequence.template_code,
                "template_version": sequence.template_version,
                "strategy_snapshot": sequence.strategy_snapshot,
                "source_match_hash": sequence.source_match_hash,
                "validation_hash": sequence.validation_hash,
            },
            "steps": steps,
            "dependencies": dependencies,
        }

    def submit(self, sequence_id: str, notes, priority, workflow_id, user, context):
        sequence = self._get(WeldSequenceRevision, sequence_id, user, context, True)
        if sequence.status not in {"draft", "rejected", "returned"}:
            raise HTTPException(409, "当前焊序版本不能提交审批")
        product_revision = self._get(
            ProductRevision, sequence.product_revision_id, user, context
        )
        if product_revision.data_version != sequence.source_data_version:
            raise HTTPException(409, "焊缝数据已变化，请重新计算焊序")
        current_matches = self._approved_freezes(product_revision.id)
        current_snapshot = [
            {
                "id": item.id,
                "joint_id": item.weld_joint_id,
                "frozen_hash": snapshot_hash(item.frozen_snapshot),
                "snapshot": item.frozen_snapshot,
            }
            for item in sorted(
                current_matches.values(), key=lambda value: value.weld_joint_id
            )
        ]
        if snapshot_hash(current_snapshot) != sequence.source_match_hash:
            raise HTTPException(409, "已批准 WPS/PQR 匹配已变化，请重新计算焊序")
        from app.services.sequence_source_service import source_impact
        impact = source_impact(self.db, sequence)
        if impact["stale"]:
            raise HTTPException(409, {"message":"焊序来源已变化，请重新匹配并计算", "source_impact":impact})
        _, _, steps, dependencies = self._blueprint(sequence.id)
        validation = validate_sequence(steps, dependencies)
        sequence.validation_result = validation
        sequence.validation_hash = snapshot_hash(validation)
        if not validation["valid"]:
            raise HTTPException(422, {"message": "焊序约束校验未通过", "validation": validation})
        snapshot = self.approval_snapshot(sequence.id)
        digest = snapshot_hash(snapshot)
        approval = ApprovalService(self.db)
        if approval.should_require_approval("weld_sequence_version", context):
            instance = approval.submit_for_approval(
                document_type="weld_sequence_version",
                document_id=sequence.id,
                document_number=f"SEQ-{product_revision.revision_number}-V{sequence.version_number}",
                document_title="压力容器焊序版本审批",
                current_user=user,
                workspace_context=context,
                notes=notes,
                priority=priority,
                workflow_id=workflow_id,
                version_snapshot=snapshot,
                version_key=f"{sequence.id}:v{sequence.version_number}",
            )
            sequence.approval_instance_id = instance.id
            sequence.status = "pending"
            sequence.approval_snapshot_hash = digest
            sequence.submitted_at = datetime.utcnow()
        else:
            sequence.status = "approved"
            sequence.approval_snapshot_hash = digest
            sequence.frozen_snapshot = snapshot
            sequence.frozen_hash = digest
            sequence.approved_at = datetime.utcnow()
            sequence.approved_by = user.id
            self._supersede_older(sequence)
        self.db.commit()
        self.db.refresh(sequence)
        return sequence

    def _sync_status(self, sequence):
        if not sequence.approval_instance_id or sequence.status not in {
            "pending",
            "returned",
        }:
            return
        instance = (
            self.db.query(ApprovalInstance)
            .filter(ApprovalInstance.id == sequence.approval_instance_id)
            .first()
        )
        if not instance:
            return
        status_value = (
            instance.status.value
            if hasattr(instance.status, "value")
            else str(instance.status)
        )
        if status_value == ApprovalStatus.APPROVED.value:
            sequence.status = "approved"
            sequence.frozen_snapshot = instance.version_snapshot
            sequence.frozen_hash = instance.snapshot_hash
            sequence.approved_at = instance.completed_at
            sequence.approved_by = instance.final_approver_id
            self._supersede_older(sequence)
        elif status_value in {"rejected", "returned"}:
            sequence.status = status_value
        self.db.commit()

    def _supersede_older(self, sequence):
        self.db.query(WeldSequenceRevision).filter(
            WeldSequenceRevision.product_revision_id == sequence.product_revision_id,
            WeldSequenceRevision.status == "approved",
            WeldSequenceRevision.id != sequence.id,
        ).update({"status": "superseded"}, synchronize_session=False)

    def production_release(self, product_revision_id: str, user, context):
        product_revision = self._get(
            ProductRevision, product_revision_id, user, context
        )
        sequences = (
            self.db.query(WeldSequenceRevision)
            .filter(
                WeldSequenceRevision.product_revision_id == product_revision_id,
                WeldSequenceRevision.status.in_(["pending", "approved"]),
            )
            .order_by(WeldSequenceRevision.version_number.desc())
            .all()
        )
        for item in sequences:
            self._sync_status(item)
        approved = next((item for item in sequences if item.status == "approved"), None)
        eligible = bool(
            approved
            and is_production_eligible(
                approved.status,
                approved.frozen_hash,
                approved.source_data_version,
                product_revision.data_version,
            )
        )
        from app.services.sequence_source_service import source_impact
        impact = source_impact(self.db, approved) if approved else None
        eligible = eligible and not (impact and impact["stale"])
        return {
            "source_impact": impact,
            "eligible": eligible,
            "sequence_revision_id": approved.id if eligible else None,
            "frozen_hash": approved.frozen_hash if eligible else None,
            "reason": "已批准并冻结" if eligible else "不存在与当前产品数据一致的已批准冻结焊序",
        }

"""P6 parameter validation, frozen quota runs, overrides and explicit reruns."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Iterable

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.consumable_calculation import ConsumableCalculationError
from app.models.consumable import (
    ConsumableQuotaOperation,
    ConsumableQuotaOverrideAudit,
    ConsumableQuotaRun,
    ConsumableQuotaSummary,
    ConsumableRuleSet,
)


STALE_INPUT_GROUPS = {
    "groove",
    "length",
    "welding_method",
    "material",
    "enterprise_coefficient",
}

SYSTEM_TYPICAL_GROOVE_PRESETS = tuple(
    {
        "preset_code": f"TYPICAL-{groove_type}",
        "name": f"{groove_type}型参考模板",
        "groove_type": groove_type,
        "parameter_values": values,
        "approval_status": "draft",
        "requires_engineer_validation": True,
    }
    for groove_type, values in (
        ("I", {"root_gap_mm": 0.0, "reinforcement_mm": 0.0}),
        ("V", {"included_angle_deg": 60.0, "root_face_mm": 2.0}),
        (
            "X",
            {
                "included_angle_deg": 60.0,
                "upper_bevel_height_mm": 0.0,
                "lower_bevel_height_mm": 0.0,
            },
        ),
        ("U", {"radius_mm": 0.0, "root_face_mm": 0.0}),
        ("FILLET", {"leg_size_mm": 0.0}),
        ("LAP", {"leg_size_mm": 0.0}),
    )
)


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_material_compatibility(
    welding_method: str,
    material_type: str,
    compatible_material_types: Iterable[str],
) -> None:
    allowed = {str(item).casefold() for item in compatible_material_types}
    if material_type.casefold() not in allowed:
        raise ConsumableCalculationError(f"焊接方法{welding_method}不适用于焊材类型{material_type}")


def require_approved_effective_parameter(parameter: Any, at: Any) -> None:
    status = getattr(parameter, "approval_status", getattr(parameter, "status", None))
    if status != "approved" or not getattr(parameter, "is_active", False):
        raise ConsumableCalculationError("只能使用已批准且启用的参数版本")
    effective_from = getattr(parameter, "effective_from", None)
    effective_to = getattr(parameter, "effective_to", None)
    if effective_from is not None and at < effective_from:
        raise ConsumableCalculationError("参数版本尚未生效")
    if effective_to is not None and at >= effective_to:
        raise ConsumableCalculationError("参数版本已经失效")


def assert_parameter_deletable(reference_count: int) -> None:
    if reference_count:
        raise ConsumableCalculationError("正式定额已引用该参数，只能停用或创建新版本")


def freeze_quota_input(
    *,
    formula_version: str,
    geometry: dict,
    length: dict,
    operations: list[dict],
    methods: list[dict],
    materials: list[dict],
    enterprise_rule: dict,
) -> tuple[dict, str]:
    if not operations:
        raise ConsumableCalculationError("定额运行至少需要一道完整工序")
    snapshot = {
        "formula_version": formula_version,
        "geometry": deepcopy(geometry),
        "length": deepcopy(length),
        "operations": deepcopy(operations),
        "methods": deepcopy(methods),
        "materials": deepcopy(materials),
        "enterprise_rule": deepcopy(enterprise_rule),
    }
    return snapshot, canonical_hash(snapshot)


def validate_frozen_snapshot_for_formal_run(snapshot: dict) -> None:
    for group in ("methods", "materials"):
        for item in snapshot.get(group) or []:
            status = item.get("approval_status", item.get("parameter_approval_status"))
            if status != "approved":
                raise ConsumableCalculationError(f"正式定额中的{group}参数必须为已批准版本")
    enterprise_rule = snapshot.get("enterprise_rule") or {}
    if enterprise_rule.get("status") != "approved":
        raise ConsumableCalculationError("正式定额中的企业规则必须为已批准版本")
    if enterprise_rule.get("uses_reference_defaults") and not enterprise_rule.get(
        "engineer_validated"
    ):
        raise ConsumableCalculationError("未经工程校核的默认系数不能进入正式定额")
    geometry = snapshot.get("geometry") or {}
    geometry_input = geometry.get("input_snapshot", geometry)
    if geometry_input.get(
        "gouge_strategy"
    ) == "reference_trapezoid" and not geometry_input.get("engineer_confirmed"):
        raise ConsumableCalculationError("未经工程校核的清根近似公式不能进入正式定额")


def make_idempotency_key(
    product_revision_id: str,
    sequence_revision_id: str,
    input_version_hash: str,
    rule_snapshot_hash: str,
) -> str:
    return canonical_hash(
        {
            "product_revision_id": product_revision_id,
            "sequence_revision_id": sequence_revision_id,
            "input_version_hash": input_version_hash,
            "rule_snapshot_hash": rule_snapshot_hash,
        }
    )


def apply_manual_override(
    result: dict,
    field_name: str,
    override_value: float,
    reason: str,
) -> tuple[dict, dict]:
    if not reason.strip():
        raise ConsumableCalculationError("人工覆盖必须填写原因")
    if field_name not in result or not isinstance(result[field_name], (int, float)):
        raise ConsumableCalculationError("人工覆盖字段不存在或不是数值结果")
    if override_value < 0:
        raise ConsumableCalculationError("人工覆盖值不能小于0")
    overridden = deepcopy(result)
    previous = float(overridden[field_name])
    overridden[field_name] = float(override_value)
    sources = dict(overridden.get("result_sources") or {})
    sources[field_name] = "manual_override"
    overridden["result_sources"] = sources
    audit = {
        "field_name": field_name,
        "previous_value": previous,
        "override_value": float(override_value),
        "reason": reason.strip(),
        "review_status": "pending",
    }
    return overridden, audit


def quota_result_diff(previous: dict, current: dict) -> dict:
    fields = sorted(set(previous) | set(current))
    return {
        field: {"previous": previous.get(field), "current": current.get(field)}
        for field in fields
        if previous.get(field) != current.get(field)
    }


def stale_reasons_for_changes(changed_groups: Iterable[str]) -> list[str]:
    return sorted(STALE_INPUT_GROUPS.intersection(set(changed_groups)))


def ensure_rerun_allowed(previous_status: str) -> None:
    if previous_status not in {
        "calculated",
        "pending",
        "approved",
        "issued",
        "stale",
    }:
        raise ConsumableCalculationError("当前定额状态不允许重算")


def legacy_single_operation_payload(source: dict) -> tuple[dict, dict]:
    """Explicit compatibility conversion with an audit; no inferred defaults."""
    required = {
        "source_type",
        "source_id",
        "welding_method",
        "area_mm2",
        "length_mm",
        "density_g_cm3",
        "deposition_efficiency",
    }
    missing = sorted(required.difference(source))
    if missing:
        raise ConsumableCalculationError(f"旧数据单工序迁移缺少显式字段：{','.join(missing)}")
    operation = {
        "operation_order": 1,
        "operation_role": "custom",
        "area_source": "independent",
        **{
            key: deepcopy(value)
            for key, value in source.items()
            if key not in {"source_type", "source_id"}
        },
    }
    audit = {
        "source_type": source["source_type"],
        "source_id": str(source["source_id"]),
        "migration_version": "P6-LEGACY-1.0.0",
        "source_snapshot": deepcopy(source),
        "warnings": ["旧单工序已显式转换为custom角色，请工程师复核"],
    }
    return operation, audit


class ConsumableQuotaService:
    """Persistence orchestration; every run stores immutable input/result copies."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _scope(source: Any) -> dict:
        return {
            "user_id": source.user_id,
            "workspace_type": source.workspace_type,
            "company_id": source.company_id,
            "factory_id": source.factory_id,
            "access_level": source.access_level,
            "created_by": source.created_by,
        }

    def create_run(
        self,
        *,
        product_revision_id: str,
        sequence_revision_id: str,
        rule_set: ConsumableRuleSet,
        frozen_input_snapshot: dict,
        operation_rows: list[dict],
        summary_result: dict,
        parent_run: ConsumableQuotaRun | None = None,
    ) -> tuple[ConsumableQuotaRun, bool]:
        if rule_set.status != "approved" or not rule_set.is_active:
            raise ConsumableCalculationError("定额运行只能使用已批准且启用的企业规则")
        if not operation_rows:
            raise ConsumableCalculationError("定额运行至少需要一道工序结果")
        validate_frozen_snapshot_for_formal_run(frozen_input_snapshot)
        input_hash = canonical_hash(frozen_input_snapshot)
        key = make_idempotency_key(
            product_revision_id,
            sequence_revision_id,
            input_hash,
            rule_set.snapshot_hash,
        )
        existing = (
            self.db.query(ConsumableQuotaRun)
            .filter(ConsumableQuotaRun.idempotency_key == key)
            .first()
        )
        if existing is not None:
            return existing, False
        version = (
            self.db.query(func.max(ConsumableQuotaRun.run_version))
            .filter(
                ConsumableQuotaRun.product_revision_id == product_revision_id,
                ConsumableQuotaRun.sequence_revision_id == sequence_revision_id,
            )
            .scalar()
            or 0
        ) + 1
        diff = (
            quota_result_diff(parent_run.result_snapshot or {}, summary_result)
            if parent_run is not None
            else {}
        )
        run = ConsumableQuotaRun(
            product_revision_id=product_revision_id,
            sequence_revision_id=sequence_revision_id,
            rule_set_id=rule_set.id,
            parent_run_id=parent_run.id if parent_run is not None else None,
            run_version=version,
            status="calculated",
            input_version_hash=input_hash,
            idempotency_key=key,
            formula_version=rule_set.formula_version,
            frozen_input_snapshot=deepcopy(frozen_input_snapshot),
            result_snapshot=deepcopy(summary_result),
            diff_snapshot=diff,
            stale_reasons=[],
            **self._scope(rule_set),
        )
        self.db.add(run)
        self.db.flush()
        required = {
            "source_operation_id",
            "weld_joint_id",
            "sequence_step_id",
            "operation_order",
            "operation_role",
            "welding_method",
            "theoretical_deposit_kg",
            "process_primary_kg",
            "enterprise_primary_kg",
            "package_rounded_primary_kg",
            "suggested_primary_issue_kg",
            "input_snapshot",
            "method_snapshot",
            "material_snapshot",
            "result_snapshot",
            "result_sources",
        }
        for payload in operation_rows:
            missing = sorted(required.difference(payload))
            if missing:
                raise ConsumableCalculationError("定额工序冻结字段不完整：" + ",".join(missing))
            self.db.add(
                ConsumableQuotaOperation(
                    run_id=run.id,
                    **deepcopy(payload),
                    **self._scope(rule_set),
                )
            )
        self.db.add(
            ConsumableQuotaSummary(
                run_id=run.id,
                summary_type="run_total",
                material_id=None,
                material_type="mixed",
                theoretical_kg=summary_result.get("deposit_mass_kg", 0),
                process_kg=summary_result.get("process_primary_consumable_kg", 0),
                enterprise_quota_kg=summary_result.get(
                    "enterprise_primary_consumable_kg", 0
                ),
                package_rounded_kg=summary_result.get("package_rounded_primary_kg", 0),
                suggested_issue_kg=summary_result.get("suggested_primary_issue_kg", 0),
                gas_l=summary_result.get("gas_volume_l", 0),
                total_time_h=summary_result.get("total_operation_time_h", 0),
                trace_snapshot={
                    "operation_ids": [
                        item["source_operation_id"] for item in operation_rows
                    ]
                },
                **self._scope(rule_set),
            )
        )
        self.db.commit()
        return run, True

    def rerun(
        self,
        *,
        previous_run: ConsumableQuotaRun,
        rule_set: ConsumableRuleSet,
        frozen_input_snapshot: dict,
        operation_rows: list[dict],
        summary_result: dict,
    ) -> tuple[ConsumableQuotaRun, bool]:
        ensure_rerun_allowed(previous_run.status)
        return self.create_run(
            product_revision_id=previous_run.product_revision_id,
            sequence_revision_id=previous_run.sequence_revision_id,
            rule_set=rule_set,
            frozen_input_snapshot=frozen_input_snapshot,
            operation_rows=operation_rows,
            summary_result=summary_result,
            parent_run=previous_run,
        )

    def request_override(
        self,
        *,
        run: ConsumableQuotaRun,
        quota_operation_id: str | None,
        field_name: str,
        previous_value: float,
        override_value: float,
        reason: str,
    ) -> ConsumableQuotaOverrideAudit:
        _, audit = apply_manual_override(
            {field_name: previous_value}, field_name, override_value, reason
        )
        record = ConsumableQuotaOverrideAudit(
            run_id=run.id,
            quota_operation_id=quota_operation_id,
            **audit,
            **self._scope(run),
        )
        self.db.add(record)
        self.db.commit()
        return record

    def mark_runs_stale(
        self,
        *,
        product_revision_id: str,
        changed_groups: Iterable[str],
    ) -> int:
        reasons = stale_reasons_for_changes(changed_groups)
        if not reasons:
            return 0
        rows = (
            self.db.query(ConsumableQuotaRun)
            .filter(
                ConsumableQuotaRun.product_revision_id == product_revision_id,
                ConsumableQuotaRun.status.in_(
                    ["calculated", "pending", "approved", "issued"]
                ),
            )
            .all()
        )
        for row in rows:
            row.status = "stale"
            row.stale_reasons = sorted(set(row.stale_reasons or []).union(reasons))
        self.db.commit()
        return len(rows)

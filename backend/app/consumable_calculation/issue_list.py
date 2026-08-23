"""Deterministic issue-list grouping, shortages and calibration suggestions."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .errors import ConsumableCalculationError


def _positive_quantity(value: Any, label: str) -> float:
    try:
        result = float(value or 0)
    except (TypeError, ValueError) as exc:
        raise ConsumableCalculationError(f"{label}不是有效数值") from exc
    if result < 0:
        raise ConsumableCalculationError(f"{label}不能小于0")
    return result


def build_consumable_issue_items(
    operations: list[dict],
    materials: dict[int, dict],
) -> list[dict]:
    """Group by material/spec/batch/factory while retaining operation-level trace."""
    if not operations:
        raise ConsumableCalculationError("领用清单至少需要一道定额工序")
    grouped: dict[tuple, dict] = {}

    def add_item(
        operation: dict,
        *,
        category: str,
        material_field: str,
        quantity_field: str,
        theoretical_field: str,
        quota_field: str,
        unit: str,
    ) -> None:
        quantity = _positive_quantity(operation.get(quantity_field), quantity_field)
        if quantity == 0:
            return
        material_id = operation.get(material_field)
        if material_id is None or material_id not in materials:
            raise ConsumableCalculationError(
                f"工序{operation.get('id') or operation.get('source_operation_id')}的{category}缺少明确焊材，禁止自动替换"
            )
        material = materials[material_id]
        frozen_materials = operation.get("material_snapshot") or {}
        frozen = frozen_materials.get(category) or (
            frozen_materials if category == "solid_consumable" else {}
        )
        material_unit = str(material.get("unit") or unit)
        if material_unit.casefold() != unit.casefold():
            raise ConsumableCalculationError(
                f"焊材{material_id}库存单位{material_unit}与领用单位{unit}不一致"
            )
        specification = frozen.get("specification", material.get("specification"))
        batch_requirement = (
            frozen.get("batch_requirement")
            or material.get("batch_requirement")
            or "按正式领用时指定"
        )
        factory_id = frozen.get(
            "factory_id", operation.get("factory_id", material.get("factory_id"))
        )
        key = (
            category,
            material_id,
            specification,
            batch_requirement,
            factory_id,
            unit,
        )
        item = grouped.setdefault(
            key,
            {
                "category": category,
                "material_id": material_id,
                "material_code": frozen.get(
                    "material_code", material.get("material_code")
                ),
                "material_name": frozen.get(
                    "material_name", material.get("material_name")
                ),
                "specification": specification,
                "batch_requirement": batch_requirement,
                "factory_id": factory_id,
                "unit": unit,
                "suggested_quantity": 0.0,
                "theoretical_quantity": 0.0,
                "quota_quantity": 0.0,
                "available_stock": 0.0,
                "shortage_quantity": 0.0,
                "trace": {
                    "quota_operation_ids": [],
                    "source_operation_ids": [],
                    "weld_joint_ids": [],
                    "sequence_step_ids": [],
                    "method_snapshots": [],
                    "material_snapshots": [],
                    "result_snapshots": [],
                },
            },
        )
        item["suggested_quantity"] += quantity
        result_snapshot = operation.get("result_snapshot") or {}
        item["theoretical_quantity"] += _positive_quantity(
            operation.get(theoretical_field, result_snapshot.get(theoretical_field)),
            theoretical_field,
        )
        item["quota_quantity"] += _positive_quantity(
            operation.get(quota_field, result_snapshot.get(quota_field, quantity)),
            quota_field,
        )
        trace = item["trace"]
        for field, trace_field in (
            ("id", "quota_operation_ids"),
            ("source_operation_id", "source_operation_ids"),
            ("weld_joint_id", "weld_joint_ids"),
            ("sequence_step_id", "sequence_step_ids"),
        ):
            value = operation.get(field)
            if value is not None and value not in trace[trace_field]:
                trace[trace_field].append(value)
        for field, trace_field in (
            ("method_snapshot", "method_snapshots"),
            ("material_snapshot", "material_snapshots"),
            ("result_snapshot", "result_snapshots"),
        ):
            value = operation.get(field)
            if value and value not in trace[trace_field]:
                trace[trace_field].append(deepcopy(value))

    for operation in operations:
        add_item(
            operation,
            category="solid_consumable",
            material_field="material_id",
            quantity_field="suggested_primary_issue_kg",
            theoretical_field="theoretical_deposit_kg",
            quota_field="enterprise_primary_kg",
            unit="kg",
        )
        add_item(
            operation,
            category="flux",
            material_field="flux_material_id",
            quantity_field="flux_kg",
            theoretical_field="flux_kg",
            quota_field="enterprise_flux_kg",
            unit="kg",
        )
        add_item(
            operation,
            category="shielding_gas",
            material_field="gas_material_id",
            quantity_field="gas_l",
            theoretical_field="gas_l",
            quota_field="gas_l",
            unit="L",
        )

    items = sorted(
        grouped.values(),
        key=lambda item: (
            item["category"],
            str(item["material_code"] or ""),
            str(item["specification"] or ""),
            str(item["batch_requirement"]),
            item["factory_id"] or 0,
        ),
    )
    remaining_stock = {
        material_id: _positive_quantity(material.get("current_stock"), "当前库存")
        for material_id, material in materials.items()
    }
    for item in items:
        available = remaining_stock[item["material_id"]]
        allocated = min(available, item["suggested_quantity"])
        item["available_stock"] = allocated
        item["shortage_quantity"] = max(item["suggested_quantity"] - allocated, 0)
        remaining_stock[item["material_id"]] = available - allocated
    return items


def summarize_issue_items(items: list[dict]) -> dict:
    categories = {
        category: {"suggested_quantity": 0.0, "shortage_quantity": 0.0}
        for category in ("solid_consumable", "flux", "shielding_gas")
    }
    for item in items:
        category = item["category"]
        categories[category]["suggested_quantity"] += float(item["suggested_quantity"])
        categories[category]["shortage_quantity"] += float(item["shortage_quantity"])
    return {"item_count": len(items), "categories": categories}


def build_calibration_suggestion(
    *,
    theoretical_quantity: float,
    quota_quantity: float,
    actual_consumed_quantity: float,
) -> dict:
    theoretical = _positive_quantity(theoretical_quantity, "理论量")
    quota = _positive_quantity(quota_quantity, "定额量")
    actual = _positive_quantity(actual_consumed_quantity, "实际消耗量")
    variance = actual - quota
    ratio = variance / quota if quota else None
    return {
        "theoretical_quantity": theoretical,
        "quota_quantity": quota,
        "actual_consumed_quantity": actual,
        "actual_minus_quota": variance,
        "variance_ratio": ratio,
        "suggested_correction_factor": actual / theoretical if theoretical else None,
        "advisory_only": True,
        "automatic_rule_update": False,
    }

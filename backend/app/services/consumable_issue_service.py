"""P6 issue-list persistence, inventory suggestions and actual usage recording."""
from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.consumable_calculation import (
    ConsumableCalculationError,
    build_calibration_suggestion,
    build_consumable_issue_items,
    summarize_issue_items,
)
from app.core.data_access import (
    DataAccessAction,
    DataAccessMiddleware,
    WorkspaceContext,
)
from app.models.consumable import (
    ConsumableActualUsageEvent,
    ConsumableIssueItem,
    ConsumableIssueList,
    ConsumableQuotaOperation,
    ConsumableQuotaRun,
)
from app.models.material import MaterialTransaction, WeldingMaterial
from app.models.user import User
from app.services.consumable_quota_service import canonical_hash


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class ConsumableIssueService:
    def __init__(self, db: Session):
        self.db = db
        self.access = DataAccessMiddleware(db)

    @staticmethod
    def _scope(source: Any, factory_id: int | None = None) -> dict:
        return {
            "user_id": source.user_id,
            "workspace_type": source.workspace_type,
            "company_id": source.company_id,
            "factory_id": source.factory_id if factory_id is None else factory_id,
            "access_level": source.access_level,
            "created_by": source.created_by,
        }

    def _get(
        self, model, item_id: str, user: User, context: WorkspaceContext, edit=False
    ):
        item = self.db.query(model).filter(model.id == item_id).first()
        if item is None:
            raise HTTPException(404, "焊材领用数据不存在")
        self.access.check_access(
            user,
            item,
            DataAccessAction.EDIT if edit else DataAccessAction.VIEW,
            context,
        )
        return item

    @staticmethod
    def _operation_dict(operation: ConsumableQuotaOperation) -> dict:
        return {
            column.name: getattr(operation, column.name)
            for column in operation.__table__.columns
        }

    def generate_issue_list(
        self,
        run_id: str,
        user: User,
        context: WorkspaceContext,
    ) -> tuple[ConsumableIssueList, bool]:
        run = self._get(ConsumableQuotaRun, run_id, user, context, True)
        if run.status not in {"approved", "issued"}:
            raise HTTPException(409, "只有已批准的定额运行可以生成正式领用建议")
        existing = (
            self.db.query(ConsumableIssueList)
            .filter(
                ConsumableIssueList.quota_run_id == run.id,
                ConsumableIssueList.version_number == 1,
            )
            .first()
        )
        if existing is not None:
            return existing, False
        operations = (
            self.db.query(ConsumableQuotaOperation)
            .filter(ConsumableQuotaOperation.run_id == run.id)
            .order_by(
                ConsumableQuotaOperation.weld_joint_id,
                ConsumableQuotaOperation.operation_order,
            )
            .all()
        )
        operation_dicts = [self._operation_dict(item) for item in operations]
        material_ids = {
            material_id
            for operation in operations
            for material_id in (
                operation.material_id,
                operation.flux_material_id,
                operation.gas_material_id,
            )
            if material_id is not None
        }
        material_rows = (
            self.db.query(WeldingMaterial)
            .filter(WeldingMaterial.id.in_(material_ids))
            .all()
            if material_ids
            else []
        )
        for material in material_rows:
            self.access.check_access(user, material, DataAccessAction.VIEW, context)
        materials = {
            item.id: {
                "material_code": item.material_code,
                "material_name": item.material_name,
                "specification": item.specification,
                "batch_requirement": item.batch_number,
                "factory_id": item.factory_id,
                "unit": item.unit,
                "current_stock": item.current_stock or 0,
            }
            for item in material_rows
        }
        try:
            item_payloads = build_consumable_issue_items(operation_dicts, materials)
        except ConsumableCalculationError as exc:
            raise HTTPException(422, str(exc)) from exc
        summary = summarize_issue_items(item_payloads)
        source = {
            "quota_run_id": run.id,
            "product_revision_id": run.product_revision_id,
            "sequence_revision_id": run.sequence_revision_id,
            "formula_version": run.formula_version,
            "input_version_hash": run.input_version_hash,
            "rule_set_id": run.rule_set_id,
            "quota_snapshot": run.result_snapshot,
            "operation_ids": [item.id for item in operations],
        }
        snapshot_hash = canonical_hash({"source": source, "items": item_payloads})
        result = ConsumableIssueList(
            quota_run_id=run.id,
            product_revision_id=run.product_revision_id,
            sequence_revision_id=run.sequence_revision_id,
            document_number=f"CL-{run.id[:12].upper()}-V1",
            version_number=1,
            status="suggested",
            source_snapshot=source,
            summary_snapshot=summary,
            snapshot_hash=snapshot_hash,
            **self._scope(run),
        )
        self.db.add(result)
        self.db.flush()
        for line_number, payload in enumerate(item_payloads, 1):
            self.db.add(
                ConsumableIssueItem(
                    issue_list_id=result.id,
                    line_number=line_number,
                    category=payload["category"],
                    material_id=payload["material_id"],
                    material_code=payload["material_code"],
                    material_name=payload["material_name"],
                    specification=payload["specification"],
                    batch_requirement=payload["batch_requirement"],
                    unit=payload["unit"],
                    theoretical_quantity=payload["theoretical_quantity"],
                    quota_quantity=payload["quota_quantity"],
                    suggested_quantity=payload["suggested_quantity"],
                    available_stock_snapshot=payload["available_stock"],
                    shortage_quantity=payload["shortage_quantity"],
                    trace_snapshot=payload["trace"],
                    **self._scope(run, payload["factory_id"]),
                )
            )
        self.db.commit()
        self.db.refresh(result)
        return result, True

    def detail(self, issue_list_id: str, user: User, context: WorkspaceContext) -> dict:
        issue_list = self._get(ConsumableIssueList, issue_list_id, user, context)
        items = (
            self.db.query(ConsumableIssueItem)
            .filter(ConsumableIssueItem.issue_list_id == issue_list.id)
            .order_by(ConsumableIssueItem.line_number)
            .all()
        )
        events = (
            self.db.query(ConsumableActualUsageEvent)
            .filter(ConsumableActualUsageEvent.issue_list_id == issue_list.id)
            .order_by(ConsumableActualUsageEvent.recorded_at)
            .all()
        )
        return {"issue_list": issue_list, "items": items, "events": events}

    def approve(
        self, issue_list_id: str, user: User, context: WorkspaceContext
    ) -> ConsumableIssueList:
        issue_list = self._get(ConsumableIssueList, issue_list_id, user, context, True)
        if issue_list.status != "suggested":
            raise HTTPException(409, "只有建议状态的领用清单可以批准")
        issue_list.status = "approved"
        issue_list.approved_by = user.id
        issue_list.approved_at = _utcnow_naive()
        self.db.commit()
        return issue_list

    def record_actual_event(
        self,
        *,
        issue_item_id: str,
        event_type: str,
        quantity: float,
        unit: str,
        client_idempotency_key: str,
        batch_number: str | None,
        notes: str | None,
        quota_operation_id: str | None,
        user: User,
        context: WorkspaceContext,
    ) -> tuple[ConsumableActualUsageEvent, bool]:
        if event_type not in {"issue", "return", "consume"}:
            raise HTTPException(422, "实际记录类型必须为issue、return或consume")
        if not math.isfinite(quantity) or quantity <= 0:
            raise HTTPException(422, "实际数量必须大于0")
        event_key = canonical_hash(
            {
                "issue_item_id": issue_item_id,
                "event_type": event_type,
                "client_key": client_idempotency_key,
            }
        )
        existing = (
            self.db.query(ConsumableActualUsageEvent)
            .filter(ConsumableActualUsageEvent.idempotency_key == event_key)
            .first()
        )
        if existing is not None:
            return existing, False
        item = self._get(ConsumableIssueItem, issue_item_id, user, context, True)
        issue_list = self._get(
            ConsumableIssueList, item.issue_list_id, user, context, True
        )
        if issue_list.status not in {"approved", "issued"}:
            raise HTTPException(409, "领用清单批准后才能记录实际领退料或消耗")
        if unit.casefold() != item.unit.casefold():
            raise HTTPException(422, f"实际单位必须为{item.unit}")
        if (
            item.batch_requirement != "按正式领用时指定"
            and batch_number != item.batch_requirement
        ):
            raise HTTPException(422, "实际批次不满足正式领用清单要求")
        traced_operation_ids = set(
            (item.trace_snapshot or {}).get("quota_operation_ids") or []
        )
        if (
            quota_operation_id is not None
            and quota_operation_id not in traced_operation_ids
        ):
            raise HTTPException(422, "实际记录关联的定额工序不属于该领用清单行")
        material = (
            self.db.query(WeldingMaterial)
            .filter(WeldingMaterial.id == item.material_id)
            .with_for_update()
            .first()
        )
        if material is None:
            raise HTTPException(404, "领用清单关联焊材不存在")
        self.access.check_access(user, material, DataAccessAction.EDIT, context)
        stock_before = float(material.current_stock or 0)
        transaction = None
        if event_type == "issue":
            if stock_before < quantity:
                raise HTTPException(
                    409,
                    f"库存不足：当前{stock_before}{item.unit}，需要{quantity}{item.unit}；系统不会自动替换焊材",
                )
            stock_after = stock_before - quantity
            item.actual_issued_quantity += quantity
            transaction = self._material_transaction(
                material,
                issue_list,
                user,
                context,
                "out",
                -quantity,
                stock_before,
                stock_after,
                batch_number,
                notes,
            )
            material.current_stock = stock_after
            issue_list.status = "issued"
            issue_list.issued_at = issue_list.issued_at or _utcnow_naive()
        elif event_type == "return":
            if item.actual_returned_quantity + quantity > item.actual_issued_quantity:
                raise HTTPException(409, "累计退料量不能超过累计实际领用量")
            stock_after = stock_before + quantity
            item.actual_returned_quantity += quantity
            transaction = self._material_transaction(
                material,
                issue_list,
                user,
                context,
                "return",
                quantity,
                stock_before,
                stock_after,
                batch_number,
                notes,
            )
            material.current_stock = stock_after
        else:
            net_issued = item.actual_issued_quantity - item.actual_returned_quantity
            if item.actual_consumed_quantity + quantity > net_issued:
                raise HTTPException(409, "累计实际消耗量不能超过净领用量")
            item.actual_consumed_quantity += quantity
            material.usage_count = (material.usage_count or 0) + 1
            material.total_consumed = (material.total_consumed or 0) + quantity
            material.last_used_date = _utcnow_naive()
        material.updated_by = user.id
        material.updated_at = _utcnow_naive()
        if transaction is not None:
            self.db.add(transaction)
            self.db.flush()
        event = ConsumableActualUsageEvent(
            issue_list_id=issue_list.id,
            issue_item_id=item.id,
            quota_operation_id=quota_operation_id,
            material_id=item.material_id,
            material_transaction_id=transaction.id if transaction is not None else None,
            event_type=event_type,
            quantity=quantity,
            unit=item.unit,
            batch_number=batch_number,
            idempotency_key=event_key,
            source="manual",
            notes=notes,
            recorded_by=user.id,
            trace_snapshot={
                "product_revision_id": issue_list.product_revision_id,
                "sequence_revision_id": issue_list.sequence_revision_id,
                "issue_list_id": issue_list.id,
                "issue_item_id": item.id,
                "quota_operation_id": quota_operation_id,
            },
            **self._scope(issue_list, item.factory_id),
        )
        self.db.add(event)
        self.db.commit()
        return event, True

    @staticmethod
    def _material_transaction(
        material,
        issue_list,
        user,
        context,
        transaction_type,
        quantity,
        stock_before,
        stock_after,
        batch_number,
        notes,
    ) -> MaterialTransaction:
        return MaterialTransaction(
            user_id=user.id,
            workspace_type=context.workspace_type,
            company_id=context.company_id,
            factory_id=material.factory_id,
            material_id=material.id,
            transaction_type=transaction_type,
            transaction_number=f"CL-{uuid4().hex[:16].upper()}",
            transaction_date=_utcnow_naive(),
            quantity=quantity,
            unit=material.unit,
            stock_before=stock_before,
            stock_after=stock_after,
            destination="焊材定额领用" if transaction_type == "out" else None,
            source="焊材定额退料" if transaction_type == "return" else None,
            reference_type="consumable_issue_list",
            reference_number=issue_list.document_number,
            batch_number=batch_number,
            operator=user.username,
            notes=notes,
            created_by=user.id,
            updated_by=user.id,
        )

    def calibration_report(
        self, issue_list_id: str, user: User, context: WorkspaceContext
    ) -> list[dict]:
        detail = self.detail(issue_list_id, user, context)
        return [
            {
                "issue_item_id": item.id,
                "material_id": item.material_id,
                "category": item.category,
                **build_calibration_suggestion(
                    theoretical_quantity=item.theoretical_quantity,
                    quota_quantity=item.quota_quantity,
                    actual_consumed_quantity=item.actual_consumed_quantity,
                ),
            }
            for item in detail["items"]
        ]

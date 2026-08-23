from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi import HTTPException

from app.api.v1.api import api_router
from app.consumable_calculation import (
    ConsumableCalculationError,
    build_calibration_suggestion,
    build_consumable_issue_items,
    summarize_issue_items,
)
from app.core.data_access import WorkspaceContext
from app.models.consumable import (
    ConsumableActualUsageEvent,
    ConsumableIssueItem,
    ConsumableIssueList,
    ConsumableQuotaOperation,
    ConsumableQuotaRun,
    WeldConsumableOperation,
)
from app.models.material import MaterialTransaction, WeldingMaterial
from app.services.consumable_export_service import ConsumableExportService
from app.services.consumable_issue_service import ConsumableIssueService


def _operation(**overrides):
    values = {
        "id": "quota-op-1",
        "source_operation_id": "source-op-1",
        "weld_joint_id": "joint-1",
        "sequence_step_id": "step-1",
        "factory_id": 9,
        "material_id": 1,
        "flux_material_id": 2,
        "gas_material_id": 3,
        "theoretical_deposit_kg": 8,
        "enterprise_primary_kg": 10,
        "suggested_primary_issue_kg": 12,
        "flux_kg": 5,
        "gas_l": 600,
        "method_snapshot": {"method": "SAW+GTAW", "version": 2},
        "material_snapshot": {
            "solid_consumable": {
                "material_code": "WIRE-1",
                "specification": "φ3.2",
                "batch_requirement": "B-2026",
            },
            "flux": {"batch_requirement": "F-2026"},
            "shielding_gas": {"batch_requirement": "G-2026"},
        },
        "result_snapshot": {
            "enterprise_flux_kg": 5,
            "formula_version": "P6-CONSUMABLE-1.0.0",
        },
    }
    values.update(overrides)
    return values


def _materials():
    return {
        1: {
            "material_code": "DB-WIRE",
            "material_name": "焊丝",
            "specification": "φ4.0",
            "unit": "kg",
            "current_stock": 7,
            "factory_id": 9,
        },
        2: {
            "material_code": "FLUX-1",
            "material_name": "焊剂",
            "specification": "SJ101",
            "unit": "kg",
            "current_stock": 10,
            "factory_id": 9,
        },
        3: {
            "material_code": "AR-1",
            "material_name": "氩气",
            "specification": "99.99%",
            "unit": "L",
            "current_stock": 400,
            "factory_id": 9,
        },
    }


def test_issue_list_separates_wire_flux_gas_and_keeps_full_trace():
    items = build_consumable_issue_items([_operation()], _materials())
    assert [item["category"] for item in items] == [
        "flux",
        "shielding_gas",
        "solid_consumable",
    ]
    by_category = {item["category"]: item for item in items}
    solid = by_category["solid_consumable"]
    assert solid["material_code"] == "WIRE-1"
    assert solid["specification"] == "φ3.2"
    assert solid["batch_requirement"] == "B-2026"
    assert solid["theoretical_quantity"] == 8
    assert solid["quota_quantity"] == 10
    assert solid["suggested_quantity"] == 12
    assert solid["available_stock"] == 7
    assert solid["shortage_quantity"] == 5
    assert solid["trace"]["quota_operation_ids"] == ["quota-op-1"]
    assert solid["trace"]["weld_joint_ids"] == ["joint-1"]
    assert solid["trace"]["sequence_step_ids"] == ["step-1"]
    assert by_category["flux"]["shortage_quantity"] == 0
    assert by_category["shielding_gas"]["shortage_quantity"] == 200


def test_issue_grouping_is_deterministic_and_does_not_double_count_stock():
    first = _operation(id="a", suggested_primary_issue_kg=5, flux_kg=0, gas_l=0)
    second = _operation(
        id="b",
        source_operation_id="source-b",
        suggested_primary_issue_kg=5,
        flux_kg=0,
        gas_l=0,
    )
    one = build_consumable_issue_items([first, second], _materials())
    two = build_consumable_issue_items([first, second], _materials())
    assert one == two
    assert len(one) == 1
    assert one[0]["suggested_quantity"] == 10
    assert one[0]["available_stock"] == 7
    assert one[0]["shortage_quantity"] == 3
    assert one[0]["trace"]["quota_operation_ids"] == ["a", "b"]


def test_missing_or_unit_mismatched_material_never_auto_substitutes():
    with pytest.raises(ConsumableCalculationError, match="禁止自动替换"):
        build_consumable_issue_items([_operation(material_id=99)], _materials())
    materials = _materials()
    materials[3]["unit"] = "kg"
    with pytest.raises(ConsumableCalculationError, match="单位"):
        build_consumable_issue_items([_operation()], materials)


def test_product_summary_keeps_categories_separate():
    summary = summarize_issue_items(
        build_consumable_issue_items([_operation()], _materials())
    )
    assert summary["item_count"] == 3
    assert summary["categories"]["solid_consumable"]["suggested_quantity"] == 12
    assert summary["categories"]["flux"]["suggested_quantity"] == 5
    assert summary["categories"]["shielding_gas"]["suggested_quantity"] == 600


def test_actual_deviation_is_advisory_and_never_changes_rule_automatically():
    result = build_calibration_suggestion(
        theoretical_quantity=10, quota_quantity=12, actual_consumed_quantity=11
    )
    assert result["actual_minus_quota"] == -1
    assert result["suggested_correction_factor"] == 1.1
    assert result["advisory_only"] is True
    assert result["automatic_rule_update"] is False


def _row(**values):
    defaults = {
        "id": "item-1",
        "issue_list_id": "list-1",
        "line_number": 1,
        "category": "solid_consumable",
        "material_id": 1,
        "material_code": "=WIRE",
        "material_name": "焊丝",
        "specification": "φ1.2",
        "batch_requirement": "按正式领用时指定",
        "unit": "kg",
        "theoretical_quantity": 8.0,
        "quota_quantity": 9.0,
        "suggested_quantity": 10.0,
        "available_stock_snapshot": 6.0,
        "shortage_quantity": 4.0,
        "actual_issued_quantity": 0.0,
        "actual_returned_quantity": 0.0,
        "actual_consumed_quantity": 0.0,
        "factory_id": 9,
        "trace_snapshot": {
            "quota_operation_ids": ["op-1"],
            "weld_joint_ids": ["joint-1"],
            "sequence_step_ids": ["step-1"],
        },
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def _detail(status="approved"):
    return {
        "issue_list": SimpleNamespace(
            document_number="CL-001",
            product_revision_id="product-1",
            status=status,
        ),
        "items": [_row()],
        "events": [],
    }


def test_three_csv_exports_include_trace_shortage_actuals_and_formula_injection_guard():
    weld = ConsumableExportService.weld_detail(_detail()).decode("utf-8-sig")
    summary = ConsumableExportService.product_summary(_detail()).decode("utf-8-sig")
    formal = ConsumableExportService.formal_issue_list(_detail()).decode("utf-8-sig")
    assert "定额工序ID" in weld and "joint-1" in weld and "step-1" in weld
    assert "库存缺口" in summary and "4.0" in summary
    assert "实际领用量" in formal
    assert "'=WIRE" in weld
    with pytest.raises(HTTPException, match="必须先批准"):
        ConsumableExportService.formal_issue_list(_detail("suggested"))


class FakeQuery:
    def __init__(self, session, model):
        self.session = session
        self.model = model
        self.conditions = []

    def filter(self, *conditions):
        self.conditions.extend(conditions)
        return self

    def with_for_update(self):
        return self

    def order_by(self, *args):
        return self

    def _rows(self):
        rows = list(self.session.rows.get(self.model, []))
        for condition in self.conditions:
            left = getattr(condition, "left", None)
            right = getattr(condition, "right", None)
            if left is None or right is None or not hasattr(right, "value"):
                continue
            name = getattr(left, "name", None)
            expected = right.value
            if isinstance(expected, (list, tuple, set, frozenset)):
                rows = [row for row in rows if getattr(row, name, None) in expected]
            else:
                rows = [row for row in rows if getattr(row, name, None) == expected]
        return rows

    def first(self):
        rows = self._rows()
        return rows[0] if rows else None

    def all(self):
        return self._rows()


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.added = []
        self.commits = 0

    def query(self, model):
        return FakeQuery(self, model)

    def add(self, value):
        self.added.append(value)
        self.rows.setdefault(type(value), []).append(value)

    def flush(self):
        for index, value in enumerate(self.added, 1):
            if getattr(value, "id", None) is None:
                value.id = (
                    index if isinstance(value, MaterialTransaction) else f"new-{index}"
                )

    def commit(self):
        self.commits += 1
        self.flush()

    def refresh(self, value):
        return None


def test_generating_suggestion_freezes_shortage_without_deducting_inventory():
    common = dict(
        user_id=7,
        workspace_type="personal",
        company_id=None,
        factory_id=None,
        access_level="private",
        created_by=7,
    )
    run = SimpleNamespace(
        id="run-1234567890123456",
        status="approved",
        product_revision_id="product-1",
        sequence_revision_id="sequence-1",
        formula_version="P6-CONSUMABLE-1.0.0",
        input_version_hash="input-hash",
        rule_set_id="rule-1",
        result_snapshot={"suggested_primary_issue_kg": 8},
        run_version=1,
        **common,
    )
    operation = ConsumableQuotaOperation(
        id="quota-op-1",
        run_id=run.id,
        source_operation_id="source-op-1",
        weld_joint_id="joint-1",
        sequence_step_id="step-1",
        operation_order=1,
        operation_role="face_fill",
        welding_method="SMAW",
        material_id=1,
        flux_material_id=None,
        gas_material_id=None,
        theoretical_deposit_kg=6,
        process_primary_kg=7,
        enterprise_primary_kg=7.5,
        package_rounded_primary_kg=8,
        suggested_primary_issue_kg=8,
        flux_kg=0,
        gas_l=0,
        arc_time_h=1,
        total_time_h=2,
        input_snapshot={},
        method_snapshot={"method": "SMAW"},
        material_snapshot={"material_code": "E5015"},
        result_snapshot={},
        result_sources={},
        **common,
    )
    material = SimpleNamespace(
        id=1,
        material_code="E5015",
        material_name="焊条",
        specification="φ4.0",
        batch_number=None,
        unit="kg",
        current_stock=5.0,
        **common,
    )
    session = FakeSession(
        {
            ConsumableQuotaRun: [run],
            ConsumableIssueList: [],
            ConsumableQuotaOperation: [operation],
            WeldingMaterial: [material],
            MaterialTransaction: [],
        }
    )
    service = ConsumableIssueService(session)
    user = SimpleNamespace(id=7, username="engineer")
    context = WorkspaceContext(user_id=7, workspace_type="personal")
    result, created = service.generate_issue_list(run.id, user, context)
    assert created is True
    assert result.status == "suggested"
    assert material.current_stock == 5
    assert session.rows[MaterialTransaction] == []
    saved_item = session.rows[ConsumableIssueItem][0]
    assert saved_item.suggested_quantity == 8
    assert saved_item.available_stock_snapshot == 5
    assert saved_item.shortage_quantity == 3


def _actual_service_state():
    common = dict(
        user_id=7,
        workspace_type="personal",
        company_id=None,
        factory_id=None,
        access_level="private",
        created_by=7,
    )
    item_values = {**_row(material_code="WIRE").__dict__, **common}
    item = SimpleNamespace(**item_values)
    issue_list = SimpleNamespace(
        id="list-1",
        status="approved",
        document_number="CL-001",
        product_revision_id="product-1",
        sequence_revision_id="sequence-1",
        issued_at=None,
        **common,
    )
    material = SimpleNamespace(
        id=1,
        current_stock=10.0,
        unit="kg",
        usage_count=0,
        total_consumed=0.0,
        last_used_date=None,
        updated_by=None,
        updated_at=None,
        **common,
    )
    session = FakeSession(
        {
            ConsumableActualUsageEvent: [],
            ConsumableIssueItem: [item],
            ConsumableIssueList: [issue_list],
            WeldingMaterial: [material],
            MaterialTransaction: [],
        }
    )
    service = ConsumableIssueService(session)
    user = SimpleNamespace(id=7, username="engineer")
    context = WorkspaceContext(user_id=7, workspace_type="personal")
    return service, session, item, issue_list, material, user, context


def test_actual_issue_return_consume_are_idempotent_and_inventory_safe():
    (
        service,
        session,
        item,
        issue_list,
        material,
        user,
        context,
    ) = _actual_service_state()
    issue, created = service.record_actual_event(
        issue_item_id=item.id,
        event_type="issue",
        quantity=5,
        unit="kg",
        client_idempotency_key="issue-key-0001",
        batch_number="B1",
        notes=None,
        quota_operation_id="op-1",
        user=user,
        context=context,
    )
    assert created is True
    assert material.current_stock == 5
    assert item.actual_issued_quantity == 5
    assert issue_list.status == "issued"
    transaction = session.rows[MaterialTransaction][0]
    assert transaction.transaction_type == "out"
    assert transaction.quantity == -5
    repeated, created = service.record_actual_event(
        issue_item_id=item.id,
        event_type="issue",
        quantity=5,
        unit="kg",
        client_idempotency_key="issue-key-0001",
        batch_number="B1",
        notes=None,
        quota_operation_id="op-1",
        user=user,
        context=context,
    )
    assert created is False and repeated is issue
    assert material.current_stock == 5

    returned, created = service.record_actual_event(
        issue_item_id=item.id,
        event_type="return",
        quantity=1,
        unit="kg",
        client_idempotency_key="return-key-001",
        batch_number="B1",
        notes=None,
        quota_operation_id="op-1",
        user=user,
        context=context,
    )
    assert created is True and returned.event_type == "return"
    assert material.current_stock == 6
    assert item.actual_returned_quantity == 1
    service.record_actual_event(
        issue_item_id=item.id,
        event_type="consume",
        quantity=4,
        unit="kg",
        client_idempotency_key="consume-key-01",
        batch_number="B1",
        notes=None,
        quota_operation_id="op-1",
        user=user,
        context=context,
    )
    assert material.current_stock == 6
    assert item.actual_consumed_quantity == 4
    assert material.total_consumed == 4
    assert len(session.rows[MaterialTransaction]) == 2


def test_actual_issue_rejects_shortage_wrong_trace_and_overconsumption():
    service, _, item, _, material, user, context = _actual_service_state()
    with pytest.raises(HTTPException, match="库存不足"):
        service.record_actual_event(
            issue_item_id=item.id,
            event_type="issue",
            quantity=11,
            unit="kg",
            client_idempotency_key="issue-key-9999",
            batch_number=None,
            notes=None,
            quota_operation_id="op-1",
            user=user,
            context=context,
        )
    assert material.current_stock == 10
    with pytest.raises(HTTPException, match="不属于"):
        service.record_actual_event(
            issue_item_id=item.id,
            event_type="issue",
            quantity=1,
            unit="kg",
            client_idempotency_key="issue-key-8888",
            batch_number=None,
            notes=None,
            quota_operation_id="wrong-op",
            user=user,
            context=context,
        )


def test_models_and_api_expose_issue_trace_inventory_and_actual_usage():
    assert {"gas_material_id"} <= set(WeldConsumableOperation.__table__.columns.keys())
    assert {"gas_material_id"} <= set(ConsumableQuotaOperation.__table__.columns.keys())
    assert ConsumableIssueList.__tablename__ == "consumable_issue_lists"
    assert ConsumableIssueItem.__tablename__ == "consumable_issue_items"
    assert ConsumableActualUsageEvent.__tablename__ == "consumable_actual_usage_events"
    assert {
        "product_revision_id",
        "sequence_revision_id",
        "source_snapshot",
        "summary_snapshot",
        "snapshot_hash",
    } <= set(ConsumableIssueList.__table__.columns.keys())
    assert {
        "material_id",
        "batch_requirement",
        "shortage_quantity",
        "trace_snapshot",
        "actual_issued_quantity",
        "actual_returned_quantity",
        "actual_consumed_quantity",
    } <= set(ConsumableIssueItem.__table__.columns.keys())
    probe = FastAPI()
    probe.include_router(api_router)
    paths = set(probe.openapi()["paths"])
    assert "/consumables/quota-runs/{run_id}/issue-list" in paths
    assert "/consumables/issue-items/{issue_item_id}/actual-events" in paths
    assert "/consumables/issue-lists/{issue_list_id}/export/{export_type}" in paths

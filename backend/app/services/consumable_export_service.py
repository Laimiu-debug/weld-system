"""UTF-8 CSV exports for P6 weld detail, product summary and formal issue list."""
from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import HTTPException


def _safe(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _csv(headers: list[str], rows: list[list[Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_safe(value) for value in row])
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


class ConsumableExportService:
    @staticmethod
    def weld_detail(detail: dict) -> bytes:
        issue_list = detail["issue_list"]
        rows = []
        for item in detail["items"]:
            trace = item.trace_snapshot or {}
            operation_ids = trace.get("quota_operation_ids") or [""]
            for index, operation_id in enumerate(operation_ids):
                joints = trace.get("weld_joint_ids") or []
                steps = trace.get("sequence_step_ids") or []
                rows.append(
                    [
                        issue_list.document_number,
                        item.line_number,
                        item.category,
                        item.material_code,
                        item.material_name,
                        item.specification,
                        item.batch_requirement,
                        item.theoretical_quantity,
                        item.quota_quantity,
                        item.suggested_quantity,
                        item.unit,
                        operation_id,
                        joints[index] if index < len(joints) else "",
                        steps[index] if index < len(steps) else "",
                    ]
                )
        return _csv(
            [
                "清单编号",
                "行号",
                "分类",
                "焊材牌号",
                "焊材名称",
                "规格",
                "批次要求",
                "理论量",
                "企业定额量",
                "建议领用量",
                "单位",
                "定额工序ID",
                "焊缝ID",
                "焊序步骤ID",
            ],
            rows,
        )

    @staticmethod
    def product_summary(detail: dict) -> bytes:
        issue_list = detail["issue_list"]
        return _csv(
            [
                "清单编号",
                "产品版本ID",
                "工厂ID",
                "分类",
                "焊材牌号",
                "焊材名称",
                "规格",
                "批次要求",
                "理论量",
                "企业定额量",
                "建议领用量",
                "可用库存快照",
                "库存缺口",
                "单位",
            ],
            [
                [
                    issue_list.document_number,
                    issue_list.product_revision_id,
                    item.factory_id,
                    item.category,
                    item.material_code,
                    item.material_name,
                    item.specification,
                    item.batch_requirement,
                    item.theoretical_quantity,
                    item.quota_quantity,
                    item.suggested_quantity,
                    item.available_stock_snapshot,
                    item.shortage_quantity,
                    item.unit,
                ]
                for item in detail["items"]
            ],
        )

    @staticmethod
    def formal_issue_list(detail: dict) -> bytes:
        issue_list = detail["issue_list"]
        if issue_list.status not in {"approved", "issued", "closed"}:
            raise HTTPException(409, "正式领用清单必须先批准")
        return _csv(
            [
                "正式清单编号",
                "状态",
                "行号",
                "分类",
                "焊材牌号",
                "焊材名称",
                "规格",
                "批次要求",
                "建议领用量",
                "实际领用量",
                "实际退料量",
                "实际消耗量",
                "单位",
            ],
            [
                [
                    issue_list.document_number,
                    issue_list.status,
                    item.line_number,
                    item.category,
                    item.material_code,
                    item.material_name,
                    item.specification,
                    item.batch_requirement,
                    item.suggested_quantity,
                    item.actual_issued_quantity,
                    item.actual_returned_quantity,
                    item.actual_consumed_quantity,
                    item.unit,
                ]
                for item in detail["items"]
            ],
        )

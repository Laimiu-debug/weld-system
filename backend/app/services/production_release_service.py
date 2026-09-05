"""P7 approved-sequence release and immutable production execution layer."""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.data_access import (
    DataAccessAction,
    DataAccessMiddleware,
    WorkspaceContext,
)
from app.models.approval import ApprovalStatus
from app.models.consumable import ConsumableActualUsageEvent, ConsumableIssueList
from app.models.engineering import ProductRevision, WeldJoint
from app.models.equipment import Equipment
from app.models.production import ProductionTask
from app.models.production_release import (
    ProductionExecutionTrace,
    ProductionQualityNode,
    ProductionReleaseBatch,
    ProductionResourceAuthorization,
    ProductionSequenceChangeRequest,
)
from app.models.quality import QualityInspection
from app.models.sequence import WeldSequenceRevision, WeldSequenceStep
from app.models.user import User
from app.models.welder import Welder, WelderCertification
from app.models.wps import WPS
from app.services.approval_service import ApprovalService
from app.services.sequence_change_service import sync_change_approval


def canonical_hash(value: Any) -> str:
    raw = json.dumps(
        value, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sequence_step_to_task_kind(step_type: str) -> str:
    """Stable P7 conversion contract used by API and tests."""
    return {
        "assembly": "assembly",
        "weld": "welding",
        "nde": "quality_nde",
        "pwht": "process_pwht",
        "inspection": "quality_inspection",
        "closure": "quality_closure",
    }[step_type]


def _tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    try:
        parsed = json.loads(value)
        values = parsed if isinstance(parsed, list) else [parsed]
    except (TypeError, ValueError):
        values = value.replace(";", ",").split(",")
    return {str(item).strip().upper() for item in values if str(item).strip()}


def evaluate_welder_qualification(
    welder: Welder,
    certifications: list[WelderCertification],
    wps: WPS,
    position: str | None,
    today: date | None = None,
) -> dict:
    """Conservative qualification gate: unknown scope is not silently accepted."""
    today = today or date.today()
    reasons: list[str] = []
    if not welder.is_active or str(welder.status) != "active":
        reasons.append("焊工状态不可用")
    if welder.primary_expiry_date and welder.primary_expiry_date < today:
        reasons.append("焊工主证书已过期")
    valid = [
        item
        for item in certifications
        if item.is_active
        and str(item.status) in {"valid", "expiring_soon"}
        and (item.expiry_date is None or item.expiry_date >= today)
    ]
    process = str(wps.welding_process or "").strip().upper()
    requested_position = str(position or "").strip().upper()
    process_ok = (
        not process
        or (not certifications and process in _tokens(welder.qualified_processes))
        or any(process in _tokens(item.qualified_process) for item in valid)
    )
    position_ok = (
        not requested_position
        or (
            not certifications
            and requested_position in _tokens(welder.qualified_positions)
        )
        or any(requested_position in _tokens(item.qualified_position) for item in valid)
    )
    if not process_ok:
        reasons.append(f"缺少 {process or '指定'} 焊接方法资格")
    if not position_ok:
        reasons.append(f"缺少 {requested_position} 焊位资格")
    if not valid and (
        certifications
        or not (
            _tokens(welder.qualified_processes) or _tokens(welder.qualified_positions)
        )
    ):
        reasons.append("没有可验证的有效资格范围")
    return {
        "qualified": not reasons,
        "reasons": reasons,
        "wps_id": wps.id,
        "wps_number": wps.wps_number,
        "welding_process": process or None,
        "welding_position": requested_position or None,
        "welder_id": welder.id,
        "certification_ids": [item.id for item in valid],
        "evaluated_on": today.isoformat(),
    }


class ProductionReleaseService:
    def __init__(self, db: Session):
        self.db = db
        self.access = DataAccessMiddleware(db)

    @staticmethod
    def _scope(source: Any, user_id: int) -> dict:
        return {
            "user_id": source.user_id,
            "workspace_type": source.workspace_type,
            "company_id": source.company_id,
            "factory_id": source.factory_id,
            "access_level": source.access_level,
            "created_by": user_id,
        }

    def _get(self, model, item_id, user: User, context: WorkspaceContext, edit=False):
        item = self.db.query(model).filter(model.id == item_id).first()
        if item is None:
            raise HTTPException(404, "生产发布数据不存在")
        self.access.check_access(
            user,
            item,
            DataAccessAction.EDIT if edit else DataAccessAction.VIEW,
            context,
        )
        return item

    @staticmethod
    def _step_snapshot(step: WeldSequenceStep) -> dict:
        return {
            "id": step.id,
            "step_code": step.step_code,
            "step_type": step.step_type,
            "title": step.title,
            "order_index": step.order_index,
            "phase": step.phase,
            "weld_joint_id": step.weld_joint_id,
            "match_freeze_id": step.match_freeze_id,
            "process_parameters": step.process_parameters,
            "inspection_node": step.inspection_node,
            "source_snapshot": step.source_snapshot,
        }

    def release(
        self,
        sequence_id: str,
        issue_list_id: str | None,
        user: User,
        context: WorkspaceContext,
    ):
        sequence = self._get(WeldSequenceRevision, sequence_id, user, context, True)
        if (
            sequence.status != "approved"
            or not sequence.frozen_hash
            or not sequence.frozen_snapshot
        ):
            raise HTTPException(409, "只有已批准且已冻结的焊序可以下发生产")
        product = self._get(
            ProductRevision, sequence.product_revision_id, user, context
        )
        self.db.refresh(product, with_for_update=True)
        if product.data_version != sequence.source_data_version:
            raise HTTPException(409, "产品数据已变化，当前批准焊序不能下发")
        issue_list = None
        if issue_list_id:
            issue_list = self._get(ConsumableIssueList, issue_list_id, user, context)
            if (
                issue_list.sequence_revision_id != sequence.id
                or issue_list.status not in {"approved", "issued", "closed"}
            ):
                raise HTTPException(409, "焊材领用单未批准或不属于当前焊序")
        idem = canonical_hash(
            {"sequence_id": sequence.id, "frozen_hash": sequence.frozen_hash}
        )
        existing = (
            self.db.query(ProductionReleaseBatch)
            .filter(ProductionReleaseBatch.idempotency_key == idem)
            .first()
        )
        if existing:
            if existing.consumable_issue_list_id != issue_list_id:
                raise HTTPException(409, "该焊序已下发且领用单已冻结，请刷新查看原批次")
            return existing, False
        active = (
            self.db.query(ProductionReleaseBatch)
            .filter(
                ProductionReleaseBatch.product_revision_id == product.id,
                ProductionReleaseBatch.status == "released",
            )
            .first()
        )
        if active:
            raise HTTPException(409, "已有在用生产批次，请先批准并应用变更")
        unapplied = (
            self.db.query(ProductionSequenceChangeRequest)
            .filter(
                ProductionSequenceChangeRequest.proposed_sequence_revision_id
                == sequence.id,
                ProductionSequenceChangeRequest.status != "applied",
            )
            .first()
        )
        if unapplied:
            raise HTTPException(409, "变更方案尚未应用，不能下发")
        scope = self._scope(sequence, user.id)
        batch = ProductionReleaseBatch(
            id=str(uuid4()),
            product_revision_id=product.id,
            sequence_revision_id=sequence.id,
            consumable_issue_list_id=issue_list.id if issue_list else None,
            idempotency_key=idem,
            sequence_frozen_hash=sequence.frozen_hash,
            source_snapshot={
                "sequence": sequence.frozen_snapshot,
                "issue_list_hash": getattr(issue_list, "snapshot_hash", None),
            },
            released_by=user.id,
            **scope,
        )
        self.db.add(batch)
        self.db.flush()
        steps = (
            self.db.query(WeldSequenceStep)
            .filter(WeldSequenceStep.sequence_revision_id == sequence.id)
            .order_by(WeldSequenceStep.order_index)
            .all()
        )
        for step in steps:
            snapshot = self._step_snapshot(step)
            wps_data = (step.process_parameters or {}).get("wps") or {}
            pqr_data = (step.process_parameters or {}).get("pqr") or {}
            task = ProductionTask(
                user_id=sequence.user_id,
                workspace_type=sequence.workspace_type,
                company_id=sequence.company_id,
                factory_id=sequence.factory_id,
                access_level=sequence.access_level,
                task_number=f"SEQ-{sequence.id[:8]}-{step.order_index:04d}",
                task_name=step.title,
                task_type=sequence_step_to_task_kind(step.step_type),
                wps_id=wps_data.get("id"),
                pqr_id=pqr_data.get("id"),
                status="pending",
                priority="normal",
                progress_percentage=0,
                is_active=True,
                quality_inspection_required=step.step_type
                in {"nde", "pwht", "inspection", "closure"},
                technical_requirements=json.dumps(
                    step.process_parameters or {}, ensure_ascii=False
                ),
                quality_requirements=json.dumps(
                    step.inspection_node or {}, ensure_ascii=False
                ),
                work_description=step.explanation,
                created_by=user.id,
                source_product_revision_id=product.id,
                source_sequence_revision_id=sequence.id,
                source_sequence_step_id=step.id,
                source_weld_joint_id=step.weld_joint_id,
                source_match_freeze_id=step.match_freeze_id,
                production_release_id=batch.id,
                consumable_issue_list_id=issue_list.id if issue_list else None,
                source_sequence_frozen_hash=sequence.frozen_hash,
                source_step_snapshot=snapshot,
            )
            self.db.add(task)
            self.db.flush()
            if step.step_type in {"nde", "pwht", "inspection", "closure"}:
                joint = (
                    self.db.query(WeldJoint)
                    .filter(WeldJoint.id == step.weld_joint_id)
                    .first()
                    if step.weld_joint_id
                    else None
                )
                inspection = QualityInspection(
                    owner_id=user.id,
                    company_id=sequence.company_id,
                    factory_id=sequence.factory_id,
                    inspection_number=f"QI-{sequence.id[:8]}-{step.order_index:04d}",
                    inspection_type=step.step_type,
                    inspection_result="pending",
                    production_task_id=task.id,
                    weld_joint_number=getattr(joint, "weld_number", None),
                    status="pending",
                    notes=json.dumps(step.inspection_node or {}, ensure_ascii=False),
                )
                self.db.add(inspection)
                self.db.flush()
                self.db.add(
                    ProductionQualityNode(
                        id=str(uuid4()),
                        production_release_id=batch.id,
                        production_task_id=task.id,
                        sequence_step_id=step.id,
                        quality_inspection_id=inspection.id,
                        node_type=step.step_type,
                        frozen_snapshot=snapshot,
                        **scope,
                    )
                )
        self.db.commit()
        self.db.refresh(batch)
        return batch, True

    def for_sequence(self, sequence_id: str, user: User, context: WorkspaceContext):
        self._get(WeldSequenceRevision, sequence_id, user, context)
        batch = (
            self.db.query(ProductionReleaseBatch)
            .filter(ProductionReleaseBatch.sequence_revision_id == sequence_id)
            .first()
        )
        return self.detail(batch.id, user, context) if batch else None

    def issue_lists(self, sequence_id, user, context):
        self._get(WeldSequenceRevision, sequence_id, user, context)
        query = self.access.apply_workspace_filter(
            self.db.query(ConsumableIssueList), ConsumableIssueList, user, context
        )
        return [
            self._row(item)
            for item in query.filter(
                ConsumableIssueList.sequence_revision_id == sequence_id,
                ConsumableIssueList.status.in_(["approved", "issued", "closed"]),
            )
            .order_by(ConsumableIssueList.generated_at.desc())
            .all()
        ]

    def detail(self, release_id: str, user: User, context: WorkspaceContext) -> dict:
        batch = self._get(ProductionReleaseBatch, release_id, user, context)
        changes = (
            self.db.query(ProductionSequenceChangeRequest)
            .filter(ProductionSequenceChangeRequest.production_release_id == batch.id)
            .order_by(ProductionSequenceChangeRequest.requested_at.desc())
            .all()
        )
        for change in changes:
            sync_change_approval(self.db, change)
        self.db.flush()
        tasks = (
            self.db.query(ProductionTask)
            .filter(ProductionTask.production_release_id == batch.id)
            .order_by(ProductionTask.id)
            .all()
        )
        return {
            "release": self._row(batch),
            "tasks": [self._row(item) for item in tasks],
            "change_requests": [self._row(item) for item in changes],
            "executions": [
                self._row(item)
                for item in self.db.query(ProductionExecutionTrace)
                .filter(ProductionExecutionTrace.production_release_id == batch.id)
                .order_by(ProductionExecutionTrace.recorded_at.desc())
                .all()
            ],
            "quality_nodes": [
                self._row(item)
                for item in self.db.query(ProductionQualityNode)
                .filter(ProductionQualityNode.production_release_id == batch.id)
                .all()
            ],
            "usage_events": [
                self._row(item)
                for item in self.db.query(ConsumableActualUsageEvent)
                .filter(
                    ConsumableActualUsageEvent.issue_list_id
                    == batch.consumable_issue_list_id
                )
                .all()
            ]
            if batch.consumable_issue_list_id
            else [],
            "authorizations": [
                self._row(item)
                for item in self.db.query(ProductionResourceAuthorization)
                .filter(
                    ProductionResourceAuthorization.production_task_id.in_(
                        [task.id for task in tasks]
                    )
                )
                .order_by(ProductionResourceAuthorization.created_at.desc())
                .all()
            ]
            if tasks
            else [],
        }

    @staticmethod
    def _row(item) -> dict:
        return {
            column.name: getattr(item, column.name) for column in item.__table__.columns
        }

    def assign(
        self,
        task_id: int,
        welder_id: int,
        equipment_id: int | None,
        override_reason: str | None,
        user: User,
        context: WorkspaceContext,
    ):
        task = (
            self.db.query(ProductionTask).filter(ProductionTask.id == task_id).first()
        )
        if not task or not task.production_release_id:
            raise HTTPException(404, "P7 生产任务不存在")
        self.access.check_access(user, task, DataAccessAction.EDIT, context)
        if task.task_type != "welding" or not task.wps_id:
            raise HTTPException(409, "只有绑定批准 WPS 的焊接任务需要焊工资格分配")
        self.db.refresh(task, with_for_update=True)
        wps = self.db.query(WPS).filter(WPS.id == task.wps_id).first()
        welder = self.db.query(Welder).filter(Welder.id == welder_id).first()
        if not wps or wps.status != "approved" or not welder:
            raise HTTPException(409, "WPS 未批准或焊工不存在")
        self.access.check_access(user, wps, DataAccessAction.VIEW, context)
        self.access.check_access(user, welder, DataAccessAction.VIEW, context)
        equipment = (
            self.db.query(Equipment).filter(Equipment.id == equipment_id).first()
            if equipment_id
            else None
        )
        if equipment_id and (
            not equipment
            or not equipment.is_active
            or str(equipment.status) not in {"operational", "idle"}
        ):
            raise HTTPException(409, "设备不可用")
        if equipment:
            self.access.check_access(user, equipment, DataAccessAction.VIEW, context)
        if (
            equipment
            and equipment.calibration_due_date
            and equipment.calibration_due_date < date.today()
        ):
            raise HTTPException(409, "设备校准已过期")
        certs = (
            self.db.query(WelderCertification)
            .filter(WelderCertification.welder_id == welder.id)
            .all()
        )
        position = (
            ((task.source_step_snapshot or {}).get("process_parameters") or {})
            .get("requirement", {})
            .get("weld_position")
        )
        result = evaluate_welder_qualification(welder, certs, wps, position)
        batch = self._get(
            ProductionReleaseBatch, task.production_release_id, user, context
        )
        self.db.refresh(batch, with_for_update=True)
        if (
            batch.status != "released"
            or not task.is_active
            or task.status in {"completed", "cancelled"}
        ):
            raise HTTPException(409, "任务或生产批次已结束，不能重新派工")
        status = "qualified" if result["qualified"] else "pending_override"
        authorization = ProductionResourceAuthorization(
            id=str(uuid4()),
            production_task_id=task.id,
            welder_id=welder.id,
            equipment_id=equipment_id,
            wps_id=wps.id,
            qualification_status=status,
            qualification_snapshot=result,
            override_reason=override_reason,
            **self._scope(batch, user.id),
        )
        self.db.add(authorization)
        if result["qualified"]:
            task.assigned_welder_id = welder.id
            task.assigned_equipment_id = equipment_id
        elif not override_reason:
            self.db.rollback()
            raise HTTPException(
                409, {"message": "焊工资格不满足，任务未分配", "qualification": result}
            )
        self.db.commit()
        self.db.refresh(authorization)
        return authorization

    def authorize_override(
        self,
        authorization_id: str,
        approve: bool,
        user: User,
        context: WorkspaceContext,
    ):
        item = self._get(
            ProductionResourceAuthorization, authorization_id, user, context, True
        )
        if item.qualification_status != "pending_override":
            raise HTTPException(409, "当前资格记录无需授权")
        task = None
        if approve:
            task = self._get(
                ProductionTask, item.production_task_id, user, context, True
            )
            latest = (
                self.db.query(ProductionResourceAuthorization)
                .filter(ProductionResourceAuthorization.production_task_id == task.id)
                .order_by(ProductionResourceAuthorization.created_at.desc())
                .first()
            )
            if not latest or latest.id != item.id:
                raise HTTPException(409, "已有更新的派工申请，请处理最新申请")
            batch = self._get(
                ProductionReleaseBatch, task.production_release_id, user, context
            )
            if (
                not task.is_active
                or task.status in {"completed", "cancelled"}
                or batch.status != "released"
            ):
                raise HTTPException(409, "任务或发布批次已失效，不能批准派工特批")
            from types import SimpleNamespace

            proposed_task = SimpleNamespace(
                wps_id=task.wps_id,
                assigned_welder_id=item.welder_id,
                assigned_equipment_id=item.equipment_id,
                source_step_snapshot=task.source_step_snapshot,
            )
            proposed_authorization = SimpleNamespace(
                wps_id=item.wps_id,
                qualification_status="authorized",
                qualification_snapshot=item.qualification_snapshot,
                authorized_by=user.id,
                authorized_at=datetime.utcnow(),
            )
            self._recheck_execution_resources(
                proposed_task, proposed_authorization, user, context
            )
        item.qualification_status = "authorized" if approve else "rejected"
        item.authorized_by = user.id
        item.authorized_at = datetime.utcnow()
        if approve:
            task.assigned_welder_id, task.assigned_equipment_id = (
                item.welder_id,
                item.equipment_id,
            )
        self.db.commit()
        self.db.refresh(item)
        return item

    def _check_execution_dependencies(self, task, batch, completing: bool):
        """Use the released graph, not a subsequently edited design revision."""
        if batch.status != "released" or not task.is_active:
            raise HTTPException(409, "发布批次或生产任务已失效，不能继续执行")
        snapshot = (batch.source_snapshot or {}).get("sequence") or {}
        code = (task.source_step_snapshot or {}).get("step_code")
        if (
            not code
            or "dependencies" not in snapshot
            or not any(
                step.get("step_code") == code for step in snapshot.get("steps", [])
            )
        ):
            raise HTTPException(409, "发布快照缺少工序依赖信息，不能确认执行条件")
        required = {
            edge["predecessor_code"]
            for edge in snapshot["dependencies"]
            if edge.get("successor_code") == code and edge.get("is_mandatory", True)
        }
        tasks = (
            self.db.query(ProductionTask)
            .filter(ProductionTask.production_release_id == batch.id)
            .all()
        )
        by_code = {
            (item.source_step_snapshot or {}).get("step_code"): item for item in tasks
        }
        for predecessor in required:
            previous = by_code.get(predecessor)
            if not previous or not previous.is_active or previous.status != "completed":
                raise HTTPException(409, f"前置工序 {predecessor} 尚未完成")
            self._check_task_quality(previous)
        if completing:
            self._check_task_quality(task)

    def _check_task_quality(self, task):
        if not task.quality_inspection_required:
            return
        nodes = (
            self.db.query(ProductionQualityNode)
            .filter(
                ProductionQualityNode.production_release_id
                == task.production_release_id,
                ProductionQualityNode.production_task_id == task.id,
            )
            .all()
        )
        if not nodes:
            raise HTTPException(409, "工序缺少关联的质量检验节点")
        for node in nodes:
            inspection = (
                self.db.query(QualityInspection)
                .filter(
                    QualityInspection.id == node.quality_inspection_id,
                    QualityInspection.production_task_id == task.id,
                )
                .first()
            )
            if not inspection or inspection.inspection_result != "pass":
                raise HTTPException(409, "工序关联的质量检验尚未合格")

    def _recheck_execution_resources(self, task, authorization, user, context):
        if authorization.wps_id != task.wps_id:
            raise HTTPException(409, "任务 WPS 与资格授权记录不一致，请重新派工")
        wps = self._get(WPS, task.wps_id, user, context)
        welder = self._get(Welder, task.assigned_welder_id, user, context)
        if (
            wps.status != "approved"
            or not welder.is_active
            or welder.status != "active"
        ):
            raise HTTPException(409, "WPS 或焊工当前状态不可用")
        if task.assigned_equipment_id:
            equipment = self._get(Equipment, task.assigned_equipment_id, user, context)
            if not equipment.is_active or equipment.status not in {
                "operational",
                "idle",
            }:
                raise HTTPException(409, "设备当前不可用")
            if (
                equipment.calibration_due_date
                and equipment.calibration_due_date < date.today()
            ):
                raise HTTPException(409, "设备校准已过期")
        certs = (
            self.db.query(WelderCertification)
            .filter(WelderCertification.welder_id == welder.id)
            .all()
        )
        position = (
            ((task.source_step_snapshot or {}).get("process_parameters") or {}).get(
                "requirement"
            )
            or {}
        ).get("weld_position")
        result = evaluate_welder_qualification(welder, certs, wps, position)
        previous = authorization.qualification_snapshot or {}
        if previous.get("certification_ids") and not certs:
            raise HTTPException(409, "派工时的证书记录已不存在，请重新核验资格")
        # Overrides cover the reviewed exception only, not subsequent scope/expiry changes.
        unchanged_override = (
            authorization.qualification_status == "authorized"
            and authorization.authorized_by is not None
            and authorization.authorized_at is not None
            and all(
                result.get(key) == previous.get(key)
                for key in (
                    "reasons",
                    "certification_ids",
                    "welding_process",
                    "welding_position",
                    "wps_id",
                    "welder_id",
                )
            )
        )
        if not result["qualified"] and not unchanged_override:
            raise HTTPException(
                409, {"message": "焊工资格已不满足，请重新派工或申请授权", "qualification": result}
            )

    def record_execution(
        self, task_id: int, payload: dict, user: User, context: WorkspaceContext
    ):
        task = (
            self.db.query(ProductionTask).filter(ProductionTask.id == task_id).first()
        )
        if not task or not task.production_release_id:
            raise HTTPException(404, "P7 生产任务不存在")
        self.access.check_access(user, task, DataAccessAction.EDIT, context)
        key = payload["idempotency_key"]
        self.db.refresh(task, with_for_update=True)
        existing = (
            self.db.query(ProductionExecutionTrace)
            .filter(
                ProductionExecutionTrace.production_task_id == task.id,
                ProductionExecutionTrace.idempotency_key == key,
            )
            .first()
        )
        if existing:
            return existing, False
        if getattr(task, "status", None) in {"completed", "cancelled"}:
            raise HTTPException(409, "已完成或取消的任务不能重复登记，请查看执行记录")
        if task.task_type == "welding":
            if not task.assigned_welder_id:
                raise HTTPException(409, "焊接任务必须先分配具备资格或已授权的焊工")
            authorization = (
                self.db.query(ProductionResourceAuthorization)
                .filter(
                    ProductionResourceAuthorization.production_task_id == task.id,
                    ProductionResourceAuthorization.welder_id
                    == task.assigned_welder_id,
                    ProductionResourceAuthorization.qualification_status.in_(
                        ["qualified", "authorized"]
                    ),
                )
                .order_by(ProductionResourceAuthorization.created_at.desc())
                .first()
            )
            if not authorization:
                raise HTTPException(409, "焊接任务缺少有效的焊工资格授权")
            if authorization.equipment_id != task.assigned_equipment_id:
                raise HTTPException(409, "任务设备与焊工资格授权记录不一致")
            self._recheck_execution_resources(task, authorization, user, context)
        batch = self._get(
            ProductionReleaseBatch, task.production_release_id, user, context
        )
        self.db.refresh(batch, with_for_update=True)
        self._check_execution_dependencies(
            task, batch, payload.get("status") == "completed"
        )
        event_ids = payload.get("consumable_usage_event_ids", [])
        events = (
            self.db.query(ConsumableActualUsageEvent)
            .filter(ConsumableActualUsageEvent.id.in_(event_ids))
            .all()
            if event_ids
            else []
        )
        if len(events) != len(set(event_ids)) or any(
            event.issue_list_id != task.consumable_issue_list_id for event in events
        ):
            raise HTTPException(409, "实际焊材记录不属于本任务关联的领用单")
        trace = ProductionExecutionTrace(
            id=str(uuid4()),
            production_release_id=task.production_release_id,
            production_task_id=task.id,
            sequence_revision_id=task.source_sequence_revision_id,
            sequence_step_id=task.source_sequence_step_id,
            weld_joint_id=task.source_weld_joint_id,
            welder_id=task.assigned_welder_id,
            equipment_id=task.assigned_equipment_id,
            wps_id=task.wps_id,
            status=payload.get("status", "recorded"),
            design_snapshot_hash=task.source_sequence_frozen_hash,
            actual_parameters=payload.get("actual_parameters", {}),
            consumable_usage_event_ids=event_ids,
            repair_snapshot=payload.get("repair_snapshot", {}),
            quality_snapshot=payload.get("quality_snapshot", {}),
            idempotency_key=key,
            recorded_by=user.id,
            **self._scope(batch, user.id),
        )
        self.db.add(trace)
        if trace.status == "completed":
            task.status, task.progress_percentage = "completed", 100
        self.db.commit()
        self.db.refresh(trace)
        return trace, True

    def request_change(
        self,
        release_id: str,
        reason: str,
        impact: dict,
        workflow_id: int | None,
        user: User,
        context: WorkspaceContext,
    ):
        batch = self._get(ProductionReleaseBatch, release_id, user, context, True)
        self.db.refresh(batch, with_for_update=True)
        if batch.status != "released":
            raise HTTPException(409, "已失效的生产批次不能申请变更")
        existing = (
            self.db.query(ProductionSequenceChangeRequest)
            .filter(
                ProductionSequenceChangeRequest.production_release_id == batch.id,
                ProductionSequenceChangeRequest.status.in_(["pending", "approved"]),
            )
            .all()
        )
        for previous in existing:
            sync_change_approval(self.db, previous)
            if previous.status in {"pending", "approved"}:
                raise HTTPException(409, "已有未完成的变更申请，请先处理该申请")
        snapshot = {
            "release_id": batch.id,
            "sequence_revision_id": batch.sequence_revision_id,
            "sequence_frozen_hash": batch.sequence_frozen_hash,
            "reason": reason,
            "impact": impact,
        }
        item = ProductionSequenceChangeRequest(
            id=str(uuid4()),
            production_release_id=batch.id,
            source_sequence_revision_id=batch.sequence_revision_id,
            reason=reason,
            impact_snapshot=impact,
            requested_by=user.id,
            **self._scope(batch, user.id),
        )
        self.db.add(item)
        self.db.flush()
        approval = ApprovalService(self.db)
        if approval.should_require_approval("production", context):
            instance = approval.submit_for_approval(
                document_type="production",
                document_id=item.id,
                document_number=f"PCR-{item.id[:8]}",
                document_title="已发布焊序变更申请",
                current_user=user,
                workspace_context=context,
                workflow_id=workflow_id,
                notes=reason,
                version_snapshot=snapshot,
                version_key=f"{item.id}:v1",
            )
            item.approval_instance_id = instance.id
        else:
            item.status, item.decided_by, item.decided_at = (
                "approved",
                user.id,
                datetime.utcnow(),
            )
        self.db.commit()
        self.db.refresh(item)
        return item

    def apply_change(
        self,
        request_id: str,
        proposed_sequence_id: str,
        user: User,
        context: WorkspaceContext,
    ):
        item = self._get(
            ProductionSequenceChangeRequest, request_id, user, context, True
        )
        if (
            item.status == "applied"
            and item.proposed_sequence_revision_id == proposed_sequence_id
        ):
            return item
        sync_change_approval(self.db, item)
        if item.status != "approved":
            raise HTTPException(409, "焊序变更尚未批准")
        proposed = self._get(WeldSequenceRevision, proposed_sequence_id, user, context)
        from app.services.sequence_service import WeldSequenceService

        WeldSequenceService(self.db)._sync_status(proposed)
        batch = self._get(
            ProductionReleaseBatch, item.production_release_id, user, context, True
        )
        self.db.refresh(batch, with_for_update=True)
        revision = self._get(ProductRevision, batch.product_revision_id, user, context)
        self.db.refresh(item, with_for_update=True)
        sync_change_approval(self.db, item)
        if (
            item.status == "applied"
            and item.proposed_sequence_revision_id == proposed_sequence_id
        ):
            return item
        if item.status != "approved":
            raise HTTPException(409, "变更申请状态已变化，请刷新")
        if batch.status != "released":
            raise HTTPException(409, "原生产批次已经失效")
        if proposed.id != item.proposed_sequence_revision_id:
            raise HTTPException(422, "新焊序不是该变更申请生成的方案")
        if (
            proposed.status != "approved"
            or not proposed.frozen_hash
            or not proposed.frozen_snapshot
        ):
            raise HTTPException(409, "变更方案必须先批准并冻结")
        if proposed.source_data_version != revision.data_version:
            raise HTTPException(409, "产品数据已变化，请重新计算变更方案")
        if (
            proposed.id == item.source_sequence_revision_id
            or proposed.product_revision_id
            != self.db.query(ProductionReleaseBatch)
            .filter(ProductionReleaseBatch.id == item.production_release_id)
            .one()
            .product_revision_id
        ):
            raise HTTPException(422, "新焊序必须是同一产品的新版本")
        item.proposed_sequence_revision_id, item.status = proposed.id, "applied"
        batch.status = "superseded"
        # Preserve old task states and provenance; the superseded batch prevents execution.
        self.db.commit()
        self.db.refresh(item)
        return item

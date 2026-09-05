"""Business rules for plans, standards and employee performance reviews."""
import calendar
import json
from datetime import date, datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, case

from app.models.company import CompanyEmployee
from app.models.user import User
from app.models.production import ProductionTask
from app.models.quality import QualityInspection, QualityStandard
from app.schemas.production_plan import ProductionPlanCreate
from app.schemas.business_workflows import StandardInput, PerformanceInput, ReportInput
from app.services.workspace_entity_service import WorkspaceEntityService, _model_to_dict


def validated(schema, payload, item=None):
    unknown = set(payload) - schema.model_fields.keys()
    if unknown:
        raise HTTPException(422, '不允许修改字段：' + ', '.join(sorted(unknown)))
    merged = {k: getattr(item, k) for k in schema.model_fields if item is not None and hasattr(item, k)}
    merged.update(payload)
    try:
        return schema.model_validate(merged).model_dump()
    except ValidationError as exc:
        raise HTTPException(422, '; '.join(e['msg'] for e in exc.errors())) from exc


def same_workspace(item, ctx):
    if item.workspace_type != ctx.workspace_type:
        return False
    if ctx.workspace_type == 'personal':
        return item.user_id == ctx.user_id
    return item.company_id == ctx.company_id and (ctx.factory_id is None or item.factory_id == ctx.factory_id)


PLAN_TRANSITIONS = {'draft': {'approved', 'cancelled'}, 'approved': {'in_progress', 'cancelled'},
                    'in_progress': {'completed', 'cancelled'}, 'completed': set(), 'cancelled': set()}


class PlanService(WorkspaceEntityService):
    def tasks(self, plan_id):
        return self.db.query(ProductionTask).filter(ProductionTask.plan_id == plan_id, ProductionTask.is_active == True)

    def progress(self, plan_id):
        tasks = self.tasks(plan_id).filter(ProductionTask.status != 'cancelled')
        count, completed, progress = tasks.with_entities(
            func.count(ProductionTask.id),
            func.sum(case((ProductionTask.status == 'completed', 1), else_=0)),
            func.avg(case((ProductionTask.status == 'completed', 100.0), else_=func.coalesce(ProductionTask.progress_percentage, 0))),
        ).one()
        return {'task_count': count, 'completed_tasks': completed or 0,
                'progress_percentage': round(float(progress or 0), 2)}

    def prepare(self, payload, user, ctx, item=None):
        if 'progress_percentage' in payload and (item is not None or payload['progress_percentage'] != 0):
            raise HTTPException(422, '计划进度由关联任务自动汇总，不能手工修改')
        if 'tasks' in payload:
            raise HTTPException(422, '请通过关联任务操作维护计划任务')
        # Stored legacy progress is superseded by the live task aggregate.
        merged = dict(payload)
        current = self.progress(item.id) if item else {'progress_percentage': 0, 'task_count': 0, 'completed_tasks': 0}
        merged['progress_percentage'] = current['progress_percentage']
        data = validated(ProductionPlanCreate, merged, item)
        next_status = data['status']
        if item is None and next_status != 'draft':
            raise HTTPException(422, '新计划必须从草稿开始')
        if item and next_status != item.status and next_status not in PLAN_TRANSITIONS.get(item.status, set()):
            raise HTTPException(409, '不允许该计划状态流转')
        if item and item.status in ('completed', 'cancelled'):
            raise HTTPException(409, '已完成或已取消的计划不能修改')
        if next_status == 'completed' and (not current['task_count'] or current['completed_tasks'] != current['task_count']):
            raise HTTPException(409, '所有有效关联任务完成后才能完成计划')
        return data

    def serialize(self, item, user, ctx):
        data = _model_to_dict(item)
        data.update(self.progress(item.id))
        data['overdue'] = item.plan_end_date < date.today() and item.status not in ('completed', 'cancelled')
        data['allowed_statuses'] = sorted(PLAN_TRANSITIONS.get(item.status, set()))
        return data

    def before_delete(self, item, user, ctx):
        if item.status != 'draft' or self.tasks(item.id).count():
            raise HTTPException(409, '只能删除未关联任务的草稿计划')

    def set_tasks(self, plan_id, task_ids, user, ctx):
        item = self.db.query(self.model).filter(self.model.id == plan_id).with_for_update().first()
        if not item or not item.is_active:
            raise HTTPException(404, '计划不存在')
        self.data_access.check_access(user, item, 'EDIT', ctx)
        if item.status in ('completed', 'cancelled'):
            raise HTTPException(409, '已结束计划不能更改任务')
        old = self.tasks(plan_id).with_for_update().all()
        selected = self.db.query(ProductionTask).filter(ProductionTask.id.in_(task_ids), ProductionTask.is_active == True).order_by(ProductionTask.id).with_for_update().all() if task_ids else []
        if len(selected) != len(task_ids):
            raise HTTPException(404, '部分任务不存在')
        for task in {task.id: task for task in old + selected}.values():
            self.data_access.check_access(user, task, 'EDIT', ctx)
            if not same_workspace(task, ctx) or task.factory_id != item.factory_id:
                raise HTTPException(403, '任务必须与计划属于同一工作区和工厂')
            if task.plan_id not in (None, plan_id):
                raise HTTPException(409, '任务已归属其他计划，请先解除原关联')
        for task in old:
            task.plan_id = None
        for task in selected:
            task.plan_id = plan_id
        item.updated_by = user.id
        item.updated_at = datetime.utcnow()
        self.db.commit()
        return self.serialize(item, user, ctx)


class StandardService(WorkspaceEntityService):
    def prepare(self, payload, user, ctx, item=None):
        data = validated(StandardInput, payload, item)
        if item and any(json.loads(data[k]) != json.loads(getattr(item, k) or '[]') for k in ('test_methods', 'acceptance_criteria')) and data['version'] == item.version:
            raise HTTPException(422, '变更检验方法或验收项时请更新标准版本')
        return data


def standard_snapshot(db, access, standard_id, inspection_date, user, ctx):
    item = db.query(QualityStandard).filter(QualityStandard.id == standard_id).first()
    if not item or not item.is_active:
        raise HTTPException(404, '质量标准不存在')
    access.check_access(user, item, 'VIEW', ctx)
    when = date.fromisoformat(inspection_date) if isinstance(inspection_date, str) else inspection_date
    if not when:
        raise HTTPException(422, '选用标准时必须填写检验日期')
    if item.status != 'active' or (item.effective_date and when < item.effective_date) or (item.expiry_date and when > item.expiry_date):
        raise HTTPException(422, '该标准在检验日期尚未生效、已失效或已停用')
    config = validated(StandardInput, {}, item)
    if not json.loads(config['acceptance_criteria']):
        raise HTTPException(422, '选用的标准必须包含版本和验收项')
    return {k: v for k, v in _model_to_dict(item).items() if k in (
        'id', 'standard_code', 'standard_name', 'version', 'effective_date', 'expiry_date',
        'test_methods', 'acceptance_criteria', 'category', 'level')}


def employee_options(db, user, ctx):
    from app.services.workspace_service import WorkspaceService
    WorkspaceService(db).validate_workspace_access(user, ctx)
    if ctx.workspace_type != 'enterprise':
        return [{'id': user.id, 'name': user.full_name or user.username, 'department': None, 'position': None}]
    query = db.query(CompanyEmployee, User).join(User, User.id == CompanyEmployee.user_id).filter(
        CompanyEmployee.company_id == ctx.company_id, CompanyEmployee.status == 'active', User.is_active == True)
    if ctx.factory_id is not None:
        query = query.filter(CompanyEmployee.factory_id == ctx.factory_id)
    return [{'id': member.user_id, 'name': employee.full_name or employee.username,
             'department': member.department, 'position': member.position} for member, employee in query.all()]


class PerformanceService(WorkspaceEntityService):
    def evidence(self, user, ctx, employee_id, start, end):
        def scoped(model):
            return self.data_access.apply_workspace_filter(self.db.query(model), model, user, ctx)
        # Explicit responsibility, not author/creator, determines whose work is counted.
        tasks = scoped(ProductionTask).filter(ProductionTask.is_active == True,
            ProductionTask.team_leader_id == employee_id, ProductionTask.actual_end_date >= start,
            ProductionTask.actual_end_date <= end)
        inspections = scoped(QualityInspection).filter(QualityInspection.inspector_id == employee_id,
            QualityInspection.inspection_date >= start, QualityInspection.inspection_date <= end)
        total = inspections.count()
        return {'period_start': start.isoformat(), 'period_end': end.isoformat(),
                'completed_tasks': tasks.filter(ProductionTask.status == 'completed').count(),
                'inspections': total, 'passed_inspections': inspections.filter(QualityInspection.inspection_result == 'pass').count(),
                'source_note': '当前可访问记录；生产按组长及实际完成日期，质检按检验员及检验日期归属。原始数量作为评审参考，不自动折算评分。',
                'captured_at': datetime.utcnow().isoformat()}

    def prepare(self, payload, user, ctx, item=None):
        data = validated(PerformanceInput, payload, item)
        employee = next((e for e in employee_options(self.db, user, ctx) if e['id'] == data['employee_user_id']), None)
        if not employee:
            raise HTTPException(403, '请选择当前工作区中的在职员工')
        if item and item.status == 'finalized':
            raise HTTPException(409, '已确认绩效不能修改，请创建新的评估记录')
        transitions = {'draft': {'submitted'}, 'submitted': {'draft', 'reviewed'}, 'reviewed': {'draft', 'finalized'}}
        if item is None and data['status'] != 'draft':
            raise HTTPException(422, '新评估必须为草稿')
        if item and data['status'] != item.status and data['status'] not in transitions.get(item.status, set()):
            raise HTTPException(409, '请按草稿、提交、评审、确认的顺序流转')
        score_fields = ('overall_score', 'quality_score', 'efficiency_score', 'safety_score', 'teamwork_score')
        scores_changed = item is not None and any(data[k] != getattr(item, k) for k in score_fields)
        if scores_changed and not str(payload.get('adjustment_reason') or '').strip():
            raise HTTPException(422, '修改评分必须填写本次人工调整理由')
        if data['status'] in ('reviewed', 'finalized') and not data['reviewer_comment']:
            raise HTTPException(422, '评审和确认必须填写评审意见')
        year, period = data['review_period'].split('-')
        year = int(year)
        month = (int(period[1]) - 1) * 3 + 1 if period.startswith('Q') else int(period)
        last_month = month + 2 if period.startswith('Q') else month
        start, end = date(year, month, 1), date(year, last_month, calendar.monthrange(year, last_month)[1])
        data.update(employee_name=employee['name'], department=employee['department'], position=employee['position'], period_start=start, period_end=end)
        if item is None or item.status != data['status'] or item.review_period != data['review_period'] or item.employee_user_id != data['employee_user_id']:
            data['evidence_snapshot'] = self.evidence(user, ctx, employee['id'], start, end)
        previous_evidence = (item.evidence_snapshot or {}) if item else {}
        evidence = dict(data.get('evidence_snapshot', previous_evidence))
        adjustments = list(previous_evidence.get('adjustments', []))
        if scores_changed:
            adjustments.append({'at': datetime.utcnow().isoformat(), 'by': user.id,
                                'reason': data['adjustment_reason'],
                                'before': {key: getattr(item, key) for key in score_fields},
                                'after': {key: data[key] for key in score_fields}})
        evidence['adjustments'] = adjustments
        data['evidence_snapshot'] = evidence
        if data['status'] in ('reviewed', 'finalized'):
            data.update(reviewed_by=user.id, reviewed_at=datetime.utcnow())
        return data

    def before_delete(self, item, user, ctx):
        if item.status != 'draft':
            raise HTTPException(409, '只能删除草稿绩效')


class ReportService(WorkspaceEntityService):
    def prepare(self, payload, user, ctx, item=None):
        from app.services.report_template_runner import report_config
        data = validated(ReportInput, payload, item)
        report_config(data)
        return data

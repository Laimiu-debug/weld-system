"""Strict, workspace-scoped count reports with declared fields and grouping."""
import json
import math
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func

from app.core.data_access import DataAccessMiddleware
from app.models.wps import WPS
from app.models.pqr import PQR
from app.models.production import ProductionTask
from app.models.quality import QualityInspection

SOURCES = {
    'wps': (WPS, 'WPS', ['status', 'welding_process', 'created_at']),
    'pqr': (PQR, 'PQR', ['status', 'welding_process', 'created_at']),
    'production': (ProductionTask, '生产任务', ['status', 'priority', 'task_type', 'project_name', 'progress_percentage', 'planned_start_date', 'planned_end_date', 'created_at']),
    'quality': (QualityInspection, '质量检验', ['inspection_result', 'inspection_type', 'project_name', 'inspection_date', 'created_at']),
}


def catalog():
    return [{'source': source, 'label': label, 'fields': [
        {'field': name, 'type': getattr(model, name).property.columns[0].type.python_type.__name__,
         'operators': ['eq', 'contains'] if getattr(model, name).property.columns[0].type.python_type is str else ['eq', 'gte', 'lte']}
        for name in fields], 'metric': 'count', 'definition': '工作区内可访问的有效记录数；每条记录计 1 次，数据源之间不合并去重。'}
        for source, (model, label, fields) in SOURCES.items()]


def parse_json(value, fallback):
    try:
        return json.loads(value) if value else fallback
    except (TypeError, ValueError) as exc:
        raise HTTPException(422, '报表配置必须是有效 JSON') from exc


def typed_value(model, field, value):
    kind = getattr(model, field).property.columns[0].type.python_type
    try:
        if value is None or value == '':
            raise ValueError()
        if kind is datetime:
            return datetime.fromisoformat(str(value))
        if kind is date:
            return date.fromisoformat(str(value))
        if kind in (int, float):
            result = kind(value)
            if not math.isfinite(result):
                raise ValueError()
            return result
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError()
        return str(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise HTTPException(422, f'筛选字段 {field} 的值无效，要求 {kind.__name__}') from exc


def report_config(template):
    sources = parse_json(template.get('data_sources'), [])
    filters = parse_json(template.get('filters'), [])
    metrics = parse_json(template.get('metrics'), ['count'])
    if not isinstance(sources, list) or not sources or len(sources) != len(set(str(x) for x in sources)) or any(not isinstance(x, str) or x not in SOURCES for x in sources):
        raise HTTPException(422, '请选择有效且不重复的数据源')
    if metrics != ['count']:
        raise HTTPException(422, '当前支持的统计指标为记录数量 count')
    if not isinstance(filters, list) or len(filters) > 30:
        raise HTTPException(422, '筛选条件必须是列表且不超过 30 项')
    if template.get('time_range'):
        raise HTTPException(422, '请使用所选数据源的日期字段设置时间筛选')
    group = template.get('group_by') or None
    compiled = {source: [] for source in sources}
    for source in sources:
        if group and group not in SOURCES[source][2]:
            raise HTTPException(422, f'数据源 {source} 不支持分组字段 {group}')
    for condition in filters:
        if not isinstance(condition, dict) or set(condition) - {'source', 'field', 'operator', 'value'}:
            raise HTTPException(422, '筛选条件格式无效')
        target = condition.get('source')
        if target is not None and target not in sources:
            raise HTTPException(422, '筛选条件引用了未选中的数据源')
        field, operator = condition.get('field'), condition.get('operator', 'eq')
        for source in ([target] if target else sources):
            model, _, fields = SOURCES[source]
            if field not in fields:
                raise HTTPException(422, f'数据源 {source} 不支持筛选字段 {field}')
            field_spec = next(x for x in next(x for x in catalog() if x['source'] == source)['fields'] if x['field'] == field)
            if operator not in field_spec['operators']:
                raise HTTPException(422, f'字段 {field} 不支持运算符 {operator}')
            value = typed_value(model, field, condition.get('value'))
            compiled[source].append((field, operator, value))
    return sources, compiled, group


def run_report(db, template, user, ctx):
    ctx.validate()
    sources, filters, group = report_config(template)
    access = DataAccessMiddleware(db)
    results = []
    for source in sources:
        model, label, _ = SOURCES[source]
        query = db.query(model)
        if hasattr(model, 'is_active'):
            query = query.filter(model.is_active == True)
        query = access.apply_workspace_filter(query, model, user, ctx)
        for field, operator, value in filters[source]:
            column = getattr(model, field)
            if operator == 'contains':
                query = query.filter(column.contains(value, autoescape=True))
            elif operator == 'gte':
                query = query.filter(column >= value)
            elif operator == 'lte':
                query = query.filter(column <= value)
            else:
                query = query.filter(column == value)
        note = f'{label}；已应用 {len(filters[source])} 个筛选条件；按记录计数'
        if group:
            column = getattr(model, group)
            grouped = query.with_entities(column, func.count(model.id)).group_by(column).order_by(column).limit(1001).all()
            if len(grouped) > 1000:
                raise HTTPException(422, '分组超过 1000 个，请缩小筛选范围')
            results.extend({'source': source, 'group': str(value) if value is not None else '未填写', 'total': count, 'note': note} for value, count in grouped)
        else:
            results.append({'source': source, 'group': '全部', 'total': query.count(), 'note': note})
    return {'template_id': template.get('id'), 'name': template.get('name'), 'chart_type': template.get('chart_type'),
            'group_by': group, 'results': results, 'generated_at': datetime.now(timezone.utc).isoformat(),
            'scope': {'workspace_type': ctx.workspace_type, 'company_id': ctx.company_id, 'factory_id': ctx.factory_id},
            'definition': '仅统计当前账号在所选工作区可访问的有效记录。各数据源独立计数，数量不代表产品产量或合格率。'}

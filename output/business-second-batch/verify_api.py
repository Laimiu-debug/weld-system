import json, os, time
from pathlib import Path
import httpx

creds = json.loads((Path(os.environ['TEMP']) / 'weld-f06-credentials.json').read_text())
c = httpx.Client(base_url='http://127.0.0.1:8000/api/v1', timeout=30)
sessions = []
for account in creds['accounts']:
    r = c.post('/auth/login-json', json={'account': account['email'], 'password': creds['password']})
    r.raise_for_status()
    sessions.append(r.json())
(Path(os.environ['TEMP']) / 'weld-f06-sessions.json').write_text(json.dumps(sessions))
reports = []
for index, kind in enumerate(['personal', 'enterprise']):
    ws = {'workspace_type': kind}
    if index: ws.update(company_id=1, factory_id=1)
    headers = {'Authorization': 'Bearer ' + sessions[index]['access_token']}
    def req(method, path, expected=200, **kwargs):
        r = c.request(method, path, headers=headers, params=kwargs.pop('params', ws), **kwargs)
        assert r.status_code == expected, (method, path, r.status_code, r.text[:600])
        return r.json().get('data', r.json())
    tag = str(time.time_ns())
    plan_body = {'plan_number': 'F06-' + tag, 'plan_name': 'F06 业务验收计划',
                 'plan_start_date': '2026-09-01', 'plan_end_date': '2026-09-04'}
    req('POST', '/production/plans', 422, json={**plan_body, 'plan_end_date': '2026-08-01'})
    plan = req('POST', '/production/plans', json=plan_body)
    pid = plan['id']
    req('PUT', f'/production/plans/{pid}', 422, json={'progress_percentage': 90})
    req('PUT', f'/production/plans/{pid}', 409, json={'status': 'in_progress'})
    task_ids = []
    for n in range(2):
        task = req('POST', '/production/tasks', json={'task_number': f'F06-T-{tag}-{n}', 'task_name': f'F06 任务 {n}', 'team_leader_id': index + 1})
        task_ids.append(task['id'])
    req('PUT', f'/production/plans/{pid}/tasks', json={'task_ids': task_ids})
    req('PUT', f'/production/plans/{pid}', json={'status': 'approved'})
    req('PUT', f'/production/plans/{pid}', json={'status': 'in_progress'})
    req('PUT', f'/production/tasks/{task_ids[0]}', json={'status': 'completed', 'progress_percentage': 100, 'actual_end_date': '2026-09-05'})
    plan = req('GET', f'/production/plans/{pid}')
    assert plan['progress_percentage'] == 50 and plan['task_count'] == 2, plan
    overdue = req('GET', '/production/plans', params={**ws, 'overdue': True})
    assert pid in [p['id'] for p in overdue['items']]
    req('PUT', f'/production/tasks/{task_ids[1]}', json={'status': 'completed', 'progress_percentage': 100, 'actual_end_date': '2026-09-05'})
    req('PUT', f'/production/plans/{pid}', json={'status': 'completed'})
    req('PUT', f'/production/plans/{pid}/tasks', 409, json={'task_ids': []})

    standard_body = {'standard_code': 'F07-' + tag, 'standard_name': 'F07 标准快照验收', 'version': '1.0',
                     'effective_date': '2026-09-01', 'expiry_date': '2026-09-30',
                     'test_methods': '["目视"]', 'acceptance_criteria': '["无可见裂纹"]'}
    req('POST', '/quality/standards', 422, json={**standard_body, 'expiry_date': '2026-08-01'})
    standard = req('POST', '/quality/standards', json=standard_body)
    sid = standard['id']
    inspection_body = {'inspection_number': 'F07-I-' + tag, 'inspection_type': 'visual', 'inspection_date': '2026-09-05',
                       'inspector_id': index + 1, 'standard_id': sid, 'result': 'pass'}
    req('POST', '/quality/inspections', 422, json={**inspection_body, 'inspection_date': '2026-10-01'})
    inspection = req('POST', '/quality/inspections', json=inspection_body)
    iid = inspection['id']
    assert inspection['standard_snapshot']['version'] == '1.0', inspection
    req('PUT', f'/quality/standards/{sid}', 422, json={'acceptance_criteria': '["新验收项"]'})
    req('PUT', f'/quality/standards/{sid}', json={'version': '2.0', 'acceptance_criteria': '["新验收项"]'})
    old = req('GET', f'/quality/inspections/{iid}')
    assert old['standard_snapshot']['version'] == '1.0' and '无可见裂纹' in old['standard_snapshot']['acceptance_criteria']
    req('PUT', f'/quality/inspections/{iid}', 409, json={'standard_id': None})

    options = req('GET', '/employees/performance-options')
    assert index + 1 in [e['id'] for e in options], options
    body = {'employee_user_id': index + 1, 'review_period': '2026-09', 'overall_score': 75}
    req('POST', '/employees/performances', 422, json={**body, 'overall_score': 101})
    req('POST', '/employees/performances', 403, json={**body, 'employee_user_id': 3})
    review = req('POST', '/employees/performances', json=body)
    rid = review['id']
    assert review['period_end'] == '2026-09-30' and review['evidence_snapshot']['inspections'] >= 1, review
    req('PUT', f'/employees/performances/{rid}', 422, json={'overall_score': 80})
    req('PUT', f'/employees/performances/{rid}', json={'overall_score': 80, 'adjustment_reason': '复核生产记录后调整'})
    for status in ['submitted', 'reviewed', 'finalized']:
        review = req('PUT', f'/employees/performances/{rid}', json={'status': status, 'reviewer_comment': '已核对原始记录'})
    assert len(review['evidence_snapshot']['adjustments']) == 1
    req('PUT', f'/employees/performances/{rid}', 409, json={'overall_score': 90, 'adjustment_reason': '不应修改'})

    template_body = {'name': 'F09 报表 ' + tag, 'data_sources': '["production"]', 'metrics': '["count"]',
                     'filters': json.dumps([{'source': 'production', 'field': 'status', 'operator': 'eq', 'value': 'completed'}]), 'group_by': 'status'}
    req('POST', '/reports/templates', 422, json={**template_body, 'filters': '[{"field":"unknown","value":"x"}]'})
    req('POST', '/reports/templates', 422, json={**template_body, 'filters': '[{"field":"progress_percentage","value":"NaN"}]'})
    template = req('POST', '/reports/templates', json=template_body)
    result = req('POST', f"/reports/templates/{template['id']}/run")
    assert result['results'][0]['group'] == 'completed' and result['results'][0]['total'] >= 2, result
    foreign = c.get(f'/production/plans/{pid}', headers={'Authorization': 'Bearer ' + sessions[2]['access_token']}, params={'workspace_type': 'personal'})
    assert foreign.status_code == 403
    reports.append({'workspace': kind, 'F06': 'passed', 'F07': 'passed', 'F08': 'passed', 'F09': 'passed', 'ids': {'plan': pid, 'standard': sid, 'inspection': iid, 'review': rid, 'template': template['id']}})
Path('output/business-second-batch/api-report.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(reports, ensure_ascii=False))

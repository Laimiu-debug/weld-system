import json, os
from pathlib import Path
import httpx
sessions=json.loads((Path(os.environ['TEMP'])/'weld-f06-sessions.json').read_text())
c=httpx.Client(base_url='http://127.0.0.1:8000/api/v1',headers={'Authorization':'Bearer '+sessions[1]['access_token']},timeout=20)
ws={'workspace_type':'enterprise','company_id':1,'factory_id':1}
r=c.put('/production/tasks/3/progress',params=ws,json={'progress_percentage':0})
assert r.status_code==409,(r.status_code,r.text[:300])
plan=c.get('/production/plans/4',params=ws).json()['data']
assert plan['task_count']==1,plan
options=c.get('/production/plan-task-options',params={**ws,'plan_id':4,'search':'NO_MATCH'}).json()['data']
assert len(options)==1 and options[0]['id']==5,options
r=c.post('/welders/2/work-histories',params=ws,json={'company_name':'F10 工作区隔离标记','position':'焊工','start_date':'2025-01-01'})
assert r.status_code==200,r.text[:300]
hid=r.json()['data']['id']
Path('output/business-second-batch/final-api-report.json').write_text(json.dumps({'closed_plan_task_guard':409,'plan_ui_linked_task_count':1,'assigned_tasks_retained_under_search':True,'workspace_marker_history_id':hid},ensure_ascii=False,indent=2),encoding='utf-8')
print('Final API assertions passed; history marker created',hid)

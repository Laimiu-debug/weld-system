import os,json
from pathlib import Path
import httpx
sessions=json.loads((Path(os.environ['TEMP'])/'weld-f05-sessions.json').read_text())
for index in [0,1]:
 ws={'workspace_type':'personal'}
 if index==1: ws={'workspace_type':'enterprise','company_id':1,'factory_id':1}
 with httpx.Client(base_url='http://127.0.0.1:8000/api/v1',headers={'Authorization':'Bearer '+sessions[index]['access_token']},timeout=15) as c:
  for tag in ['F04_ALPHA','F04_BETA']:
   for path,body in [('/production/plans',{'plan_number':tag,'plan_name':tag,'plan_start_date':'2026-09-05','plan_end_date':'2026-09-10'}),('/quality/standards',{'standard_code':tag,'standard_name':tag}),('/employees/performances',{'employee_name':tag,'review_period':'2026-09'}),('/reports/templates',{'name':tag,'data_sources':'["wps"]'})]:
    r=c.post(path,params=ws,json=body)
    assert r.status_code==200,(path,r.status_code,r.text[:200])
print('F04 search fixtures created in personal and enterprise workspaces')

import json, os, sys
from pathlib import Path
import httpx
sys.path.insert(0,str(Path('backend').resolve()))
os.environ['DEBUG']='false'
creds=json.loads((Path(os.environ['TEMP'])/'weld-f06-credentials.json').read_text())
report=json.loads(Path('output/business-second-batch/final-api-report.json').read_text(encoding='utf-8'))
with httpx.Client(base_url='http://127.0.0.1:8000/api/v1',timeout=20) as c:
    login=c.post('/auth/login-json',json={'account':creds['accounts'][1]['email'],'password':creds['password']})
    login.raise_for_status()
    c.headers['Authorization']='Bearer '+login.json()['access_token']
    r=c.delete('/welders/2/work-histories/'+str(report['workspace_marker_history_id']),params={'workspace_type':'enterprise','company_id':1,'factory_id':1})
    assert r.status_code==200,r.status_code
from app.core.database import engine
from sqlalchemy import text
engine.echo=False
with engine.begin() as c:
    c.execute(text('SET LOCAL search_path TO qa_business_f06_f11_20260905'))
    assert c.execute(text('SELECT current_schema()')).scalar()=='qa_business_f06_f11_20260905'
    count=c.execute(text("UPDATE users SET is_active=false WHERE email IN ('f06_personal@example.com','f06_enterprise@example.com','f06_outsider@example.com') RETURNING id")).all()
    assert len(count)==3,len(count)
    pending=c.execute(text("SELECT count(*) FROM company_invitations WHERE status='pending'")).scalar()
    assert pending==0,pending
for name in ['weld-f06-credentials.json','weld-f06-sessions.json','weld-f06-login.js']:
    path=Path(os.environ['TEMP'])/name
    if path.exists(): path.unlink()
Path('output/business-second-batch/cleanup-report.json').write_text(json.dumps({'test_accounts_disabled':3,'pending_invitations':0,'temporary_credentials_removed':True,'schema_retained':'qa_business_f06_f11_20260905'},indent=2),encoding='utf-8')
print('Three test accounts disabled, no pending invitations, temporary credentials removed.')

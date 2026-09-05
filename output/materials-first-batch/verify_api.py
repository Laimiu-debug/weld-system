import os,json,time
from pathlib import Path
import httpx
creds=json.loads((Path(os.environ['TEMP'])/'weld-f05-credentials.json').read_text())
report=[]
client=httpx.Client(base_url='http://127.0.0.1:8000/api/v1',timeout=20)
sessions=[]
for account in creds['accounts']:
 r=client.post('/auth/login-json',json={'account':account['email'],'password':creds['password']})
 assert r.status_code==200, (r.status_code,r.text[:200])
 sessions.append(r.json())
(Path(os.environ['TEMP'])/'weld-f05-sessions.json').write_text(json.dumps(sessions),encoding='utf-8')
for index,kind in enumerate(['personal','enterprise']):
 headers={'Authorization':'Bearer '+sessions[index]['access_token']}
 ws={'workspace_type':kind}
 if kind=='enterprise': ws.update(company_id=creds['company_id'],factory_id=creds['factory_id'])
 def req(method,path,expect=200,**kwargs):
  r=client.request(method,path,headers=headers,params=kwargs.pop('params',ws),**kwargs)
  assert r.status_code==expect, (method,path,r.status_code,r.text[:400])
  return r.json()
 data={'material_code':'F05-API-'+str(time.time_ns())+'-'+kind,'material_name':'F05 焊丝 '+kind,'material_type':'wire','specification':'1.2mm','manufacturer':'F05 测试制造商','current_stock':10,'unit':'kg','min_stock_level':2,'unit_price':0,'currency':'USD','storage_location':'F05-A'}
 material=req('POST','/materials/',json=data)['data'];mid=material['id']
 assert material['workspace_type']==kind
 assert material['company_id']==ws.get('company_id')
 assert req('GET',f'/materials/{mid}')['data']['current_stock']==10
 req('PUT',f'/materials/{mid}',json={'material_name':'F05 修改后','notes':'真实接口测试'})
 req('PUT',f'/materials/{mid}',expect=422,json={'current_stock':999})
 req('PUT',f'/materials/{mid}',expect=422,json={'unit':'L'})
 req('POST','/materials/stock-in',params={**ws,'material_id':mid,'quantity':5,'unit_price':0})
 req('POST','/materials/stock-out',params={**ws,'material_id':mid,'quantity':3,'destination':'F05 测试车间'})
 req('POST','/materials/stock-out',expect=400,params={**ws,'material_id':mid,'quantity':1000})
 assert req('GET',f'/materials/{mid}')['data']['current_stock']==12
 history=req('GET','/materials/transactions',params={**ws,'material_id':mid,'skip':0,'limit':1})['data']
 assert history['total']==3, history
 assert history['items'][0]['quantity']==-3
 older=req('GET','/materials/transactions',params={**ws,'material_id':mid,'skip':1,'limit':1})['data']['items'][0]
 assert older['quantity']==5 and older['total_price']==0 and older['currency']=='USD',older
 foreign=client.get(f'/materials/{mid}',headers={'Authorization':'Bearer '+sessions[2]['access_token']},params={'workspace_type':'personal'})
 assert foreign.status_code==403, foreign.status_code
 req('DELETE',f'/materials/{mid}')
 req('GET',f'/materials/{mid}',expect=404)
 report.append({'workspace':kind,'flow':'create/detail/edit/in/out/paged_history/delete','initial_stock':10,'final_stock_before_delete':12,'transactions':3,'failed_out_did_not_change_stock':True,'cross_account_denied':True,'result':'passed'})
Path('output/materials-first-batch/api-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))

import json, os, time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import httpx

sessions = json.loads((Path(os.environ['TEMP']) / 'weld-f06-sessions.json').read_text())
c = httpx.Client(base_url='http://127.0.0.1:8000/api/v1', timeout=20)
report = []
for index, kind in enumerate(['personal', 'enterprise']):
    ws = {'workspace_type': kind}
    if index: ws.update(company_id=1, factory_id=1)
    headers = {'Authorization': 'Bearer ' + sessions[index]['access_token']}
    def req(method, path, expected=200, **kwargs):
        r = c.request(method, path, headers=headers, params=ws, **kwargs)
        assert r.status_code == expected, (path, r.status_code, r.text[:300])
        return r.json().get('data', r.json())
    welder = req('POST', '/welders/', json={'welder_code': 'F10-' + str(time.time_ns()), 'full_name': 'F10 履历验收焊工'})
    wid = welder['id']
    assert req('GET', f'/welders/{wid}/work-histories')['items'] == []
    history = req('POST', f'/welders/{wid}/work-histories', json={'company_name': 'F10 测试公司', 'position': '焊工', 'start_date': '2025-01-01', 'end_date': '2025-12-31'})
    hid = history['id']
    req('PUT', f'/welders/{wid}/work-histories/{hid}', 422, json={'start_date': '2026-01-01'})
    updated = req('PUT', f'/welders/{wid}/work-histories/{hid}', json={'end_date': None, 'position': '高级焊工'})
    assert updated['end_date'] is None and updated['position'] == '高级焊工'
    req('DELETE', f'/welders/{wid}/work-histories/{hid}')
    assert req('GET', f'/welders/{wid}/work-histories')['items'] == []
    report.append({'workspace': kind, 'welder_id': wid, 'F10': 'passed'})

headers = {'Authorization': 'Bearer ' + sessions[1]['access_token']}
r = c.post('/enterprise/invitations', headers=headers, json={'email': 'f06_outsider@example.com', 'role': 'employee', 'factory_id': 1})
assert r.status_code == 200, r.text[:400]
invitation = r.json()['data']
assert invitation['email_sent'] is False and invitation['invite_url']
listed = c.get('/enterprise/invitations', headers=headers).json()['data']['items']
assert any(x['id'] == invitation['id'] and x.get('invite_url') for x in listed), listed
r = c.post(f"/enterprise/invitations/{invitation['id']}/resend", headers=headers)
assert r.status_code == 200 and r.json()['data']['email_sent'] is False
token = parse_qs(urlparse(r.json()['data']['invite_url']).query)['invite'][0]
# The wrong account cannot accept; the invited existing account can.
r = c.post('/enterprise/invitations/accept', headers={'Authorization': 'Bearer ' + sessions[0]['access_token']}, json={'token': token})
assert r.status_code in (400, 403), (r.status_code, r.text[:200])
r = c.post('/enterprise/invitations/accept', headers={'Authorization': 'Bearer ' + sessions[2]['access_token']}, json={'token': token})
assert r.status_code == 200, (r.status_code, r.text[:400])
report.append({'F11': 'passed', 'invitation_id': invitation['id'], 'email_delivery': 'local sink returned false; no external mail sent', 'accepted_by_invited_test_account': True})
Path('output/business-second-batch/history-invitation-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))

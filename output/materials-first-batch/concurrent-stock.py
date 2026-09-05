import json, os, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
import httpx

sessions = json.loads((Path(os.environ['TEMP']) / 'weld-f05-sessions.json').read_text())
headers = {'Authorization': 'Bearer ' + sessions[0]['access_token']}
base = 'http://127.0.0.1:8000/api/v1'
ws = {'workspace_type': 'personal'}
with httpx.Client(base_url=base, headers=headers) as client:
    r = client.post('/materials/', params=ws, json={
        'material_code': 'F05-CONCURRENT-' + str(time.time_ns()),
        'material_name': 'F05 并发库存测试', 'material_type': 'wire',
        'current_stock': 10, 'unit': 'kg', 'currency': 'CNY',
    })
    r.raise_for_status()
    mid = r.json()['data']['id']
    barrier = Barrier(2)
    def take_stock(_):
        barrier.wait()
        return httpx.post(base + '/materials/stock-out', headers=headers,
                          params={**ws, 'material_id': mid, 'quantity': 7}, timeout=20).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(take_stock, range(2)))
    assert statuses == [200, 400], statuses
    stock = client.get(f'/materials/{mid}', params=ws).json()['data']['current_stock']
    assert stock == 3, stock
    history = client.get('/materials/transactions', params={**ws, 'material_id': mid}).json()['data']
    assert history['total'] == 2, history
    client.delete(f'/materials/{mid}', params=ws).raise_for_status()
    report = {'statuses': statuses, 'final_stock': stock, 'transactions': 2, 'result': 'passed'}
    Path('output/materials-first-batch/concurrency-report.json').write_text(json.dumps(report, indent=2))
    print(report)

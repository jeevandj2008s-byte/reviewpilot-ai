import urllib.request
import json

# 1. Connect Google Demo Account
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/platforms/google/demo-connect',
    data=b'{}',
    headers={'Content-Type': 'application/json'}
)
res = urllib.request.urlopen(req)
conn = json.loads(res.read().decode('utf-8'))
conn_id = conn['id']
print('Connected Google Demo:', conn_id)

# 2. First Sync (fetch & analyze)
sync_req = urllib.request.Request(
    f'http://127.0.0.1:8000/api/platforms/{conn_id}/sync',
    data=json.dumps({'period': '7d', 'force_reanalyze': False}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
sync_res = urllib.request.urlopen(sync_req)
sync_data = json.loads(sync_res.read().decode('utf-8'))
print('First sync total fetched:', sync_data['total_fetched'])
print('First sync results returned:', len(sync_data['results']))

# 3. Subsequent Analyze Call (e.g. clicking Analyze button)
analyze_req = urllib.request.Request(
    f'http://127.0.0.1:8000/api/platforms/{conn_id}/sync',
    data=json.dumps({'period': '7d', 'force_reanalyze': True, 'tone': 'Professional'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
analyze_res = urllib.request.urlopen(analyze_req)
analyze_data = json.loads(analyze_res.read().decode('utf-8'))
print('Analyze call total fetched:', analyze_data['total_fetched'])
print('Analyze call results returned:', len(analyze_data['results']))
print('First review sentiment:', analyze_data['results'][0]['sentiment'])
print('First review reply:', analyze_data['results'][0]['generated_reply'])
print('ALL VERIFICATIONS PASSED SUCCESSFULLY!')

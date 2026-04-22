import urllib.request
import json

BASE = 'http://localhost:8000'

# 1. Health check
health = json.loads(urllib.request.urlopen(f'{BASE}/health').read().decode())
print('Backend health:', health['status'])

# 2. Create project
req = urllib.request.Request(
    f'{BASE}/api/projects/',
    data=json.dumps({'name': 'Deployment Test', 'description': 'Verify full deployment'}).encode(),
    headers={'Content-Type': 'application/json'}
)
project = json.loads(urllib.request.urlopen(req).read().decode())
pid = project['id']
print('Created project:', pid, project['name'])

# 3. Create chapter
req = urllib.request.Request(
    f'{BASE}/api/chapters/{pid}',
    data=json.dumps({'title': 'Test Chapter', 'number': '1.1', 'content': '<p>Hello</p>'}).encode(),
    headers={'Content-Type': 'application/json'}
)
ch = json.loads(urllib.request.urlopen(req).read().decode())
cid = ch['id']
print('Created chapter:', ch['number'], ch['title'])

# 4. AI generate
req = urllib.request.Request(f'{BASE}/api/chapters/{pid}/{cid}/generate', method='POST')
gen = json.loads(urllib.request.urlopen(req).read().decode())
print('AI generate status:', gen['status'], 'content length:', len(gen['content']))

# 5. AI polish
req = urllib.request.Request(
    f'{BASE}/api/ai/polish?project_id={pid}',
    data=json.dumps({'chapter_id': cid, 'style': 'professional'}).encode(),
    headers={'Content-Type': 'application/json'}
)
polish = json.loads(urllib.request.urlopen(req).read().decode())
print('AI polish diff blocks:', len(polish['diff_blocks']))

# 6. Logs
logs = json.loads(urllib.request.urlopen(f'{BASE}/api/logs/{pid}').read().decode())
print('Logs count:', len(logs))
for log in logs:
    print('  -', log['action_type'], ':', log['description'])

# 7. Export
req = urllib.request.Request(f'{BASE}/api/export/{pid}')
resp = urllib.request.urlopen(req)
print('Export status:', resp.status, 'content-type:', resp.headers.get('content-type'))

print('\n=== Full deployment verification passed ===')

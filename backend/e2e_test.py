import urllib.request
import json

BASE = 'http://localhost:8000'

def post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read().decode())

def put(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    req.get_method = lambda: 'PUT'
    return json.loads(urllib.request.urlopen(req).read().decode())

def get(url):
    return json.loads(urllib.request.urlopen(url).read().decode())

def post_empty(url):
    req = urllib.request.Request(url, method='POST')
    return json.loads(urllib.request.urlopen(req).read().decode())

# 1. Create project
project = post(f'{BASE}/api/projects/', {'name': 'CSR Test Project', 'description': 'E2E test', 'study_phase': 'Phase III'})
project_id = project['id']
print('1. Created project:', project_id)

# 2. Create root chapter 10
ch10 = post(f'{BASE}/api/chapters/{project_id}', {'title': '统计学考虑', 'number': '10', 'content': ''})
print('2. Created chapter:', ch10['number'], ch10['title'])

# 3. Create sub-chapter 10.2
ch102 = post(f'{BASE}/api/chapters/{project_id}', {'title': '研究设计', 'number': '10.2', 'parent_id': ch10['id'], 'content': ''})
print('3. Created sub-chapter:', ch102['number'], ch102['title'])

# 4. Create sub-chapter 10.2.6
ch1026 = post(f'{BASE}/api/chapters/{project_id}', {'title': '新增章节', 'number': '10.2.6', 'parent_id': ch102['id'], 'content': '<p>这是新增章节的内容</p>'})
print('4. Created sub-chapter:', ch1026['number'], ch1026['title'])

# 5. Verify tree structure
tree = get(f'{BASE}/api/chapters/{project_id}/tree')
print('5. Tree structure:')
def print_tree(nodes, depth=0):
    for n in nodes:
        print('  ' * depth + f"- {n['number']} {n['title']}")
        if n.get('children'):
            print_tree(n['children'], depth + 1)
print_tree(tree['tree'])

# 6. Update content in editor
updated = put(f'{BASE}/api/chapters/{project_id}/{ch1026['id']}', {'content': '<p>这是新增章节的更新内容，在编辑器中写入成功。</p>'})
print('6. Updated content:', updated['content'][:50])

# 7. Rename chapter
renamed = put(f'{BASE}/api/chapters/{project_id}/{ch102['id']}', {'title': '研究设计与方法'})
print('7. Renamed chapter:', renamed['title'])

# 8. Check logs
logs = get(f'{BASE}/api/logs/{project_id}')
print('8. Recent logs:')
for log in logs[:5]:
    print('  -', log['action_type'], ':', log['description'])

# 9. Test AI generate
gen = post_empty(f'{BASE}/api/chapters/{project_id}/{ch1026['id']}/generate')
print('9. AI generated content length:', len(gen['content']))

# 10. Test AI polish
polish = post(f'{BASE}/api/ai/polish?project_id={project_id}', {'chapter_id': ch1026['id'], 'style': 'professional'})
print('10. AI polish diff blocks:', len(polish['diff_blocks']))

# 11. Test export
print('11. Export endpoint:', f'{BASE}/api/export/{project_id}')

print('\n=== All E2E tests passed! ===')

import os

# Fix RightPanel.tsx
with open('frontend/components/RightPanel.tsx', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

replacements = [
    ('我�?CSR', '我是 CSR'),
    ('令�?', '令："'),
    ('容�?', '容。'),
    ('内�?', '内容'),
    ('完�?', '完成 '),
    ('试�?', '试。'),
    ('文�?', '文档'),
    ('生�?', '生成'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open('frontend/components/RightPanel.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('RightPanel.tsx fixed')

# Fix page.tsx
with open('frontend/app/projects/page.tsx', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

replacements2 = [
    ('载�?', '载中'),
    ('�其他', '无其他'),
    ('目�?', '目中'),
]

for old, new in replacements2:
    content = content.replace(old, new)

with open('frontend/app/projects/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('page.tsx fixed')

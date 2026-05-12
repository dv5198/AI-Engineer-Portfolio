import json

with open('backend/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

p = data['profile']['personal']

# Fix 1: Language honesty — self_pr_ja fields → English
p['self_pr_ja'] = (
    'AI Engineer specializing in Healthcare AI and deep learning for biomedical signals. '
    'Experienced in ECG cardiac abnormality detection using 1D-CNN and ResNet architectures. '
    'Passionate about contributing to AI research at Japanese institutions.'
)
p['self_pr_ja_detailed'] = (
    'I am a Python and AI/ML Engineer with 4 years of hands-on experience designing and deploying '
    'production-grade machine learning systems. My core expertise is in biomedical signal processing — '
    'specifically ECG-based cardiac abnormality detection using deep learning (1D-CNN, ResNet). '
    'I also have extensive experience building scalable FastAPI backends with Redis caching and '
    'PostgreSQL pipelines. I am actively pursuing opportunities at Japanese AI research institutions '
    'and tech companies, and I am committed to continuous learning, including Japanese language study. '
    'My preferred working language is English.'
)
p['career_summary_ja'] = (
    'Python and AI/ML Engineer with 4 years of experience. Strong in both deep learning research '
    'for Healthcare AI and scalable backend system architecture. '
    'Actively pursuing career opportunities in Japan.'
)

# Fix 2: Commute time → overseas standard phrase
p['commute_time'] = '海外在住のため応相談'

data['profile']['personal'] = p

# Fix 3: Experience — add employment_type_ja
for exp in data['experience']:
    company = exp.get('company', '').lower()
    role = exp.get('role', '').lower()
    if 'freelance' in company or 'freelance' in role:
        exp['employment_type_ja'] = 'フリーランス'
    elif 'employment_type_ja' not in exp:
        exp['employment_type_ja'] = '正社員'

# Fix 4: Projects — add period field
for proj in data.get('projects', []):
    if not proj.get('period'):
        start = proj.get('startDate', '')
        end = proj.get('endDate', '')
        if start and end:
            proj['period'] = start + ' 〜 ' + end
        elif start:
            proj['period'] = start + ' 〜 現在'
        elif proj.get('year'):
            proj['period'] = str(proj['year'])
        else:
            proj['period'] = '—'

# Fix 5: Add Japanese as Beginner to languages
langs = data.get('languages', [])
ja_exists = any(l.get('name', '').lower() in ('japanese', '日本語') for l in langs)
if not ja_exists:
    langs.append({
        'id': 'lang_ja',
        'name': 'Japanese',
        'level': 'Beginner (Currently Learning)',
        'visible': True,
        'order': 5,
        'percentage': 10
    })
    data['languages'] = langs

with open('backend/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print('All fixes applied successfully.')
print()
print('Employment types:')
for e in data['experience']:
    print(' ', e['company'], '->', e.get('employment_type_ja', 'not set'))
print()
print('commute_time:', data['profile']['personal']['commute_time'])
print('self_pr_ja starts with:', data['profile']['personal']['self_pr_ja'][:60])
print('Japanese language added:', ja_exists == False)

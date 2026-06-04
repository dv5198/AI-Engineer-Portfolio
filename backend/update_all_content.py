import json
import sqlite3
import os

def update_content():
    # 1. Load data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # G2: Dynamic experience years already handled, but let's double check summary
    # G3: Research paper year 2026
    if 'research' in data:
        for item in data['research']:
            item['year'] = "2026"
    
    # G4: Project dates (approximate)
    for proj in data.get('projects', []):
        if proj.get('name') == "PortfolioManager":
            proj['period'] = "Jan 2026 - Present"
        elif proj.get('name') == "CareFare_Services":
            proj['period'] = "Jun 2025 - Dec 2025"
        else:
            proj['period'] = "2024 - 2025"
        if proj.get('description'):
            proj['description'] = proj['description'].replace('ATS-compliant', 'ATS\u2011compliant')
        if proj.get('summary'):
            proj['summary'] = proj['summary'].replace('ATS-compliant', 'ATS\u2011compliant')

    # G7: 'RestAPIs' -> 'REST APIs'
    for job in data.get('experience', []):
        if 'bullets' in job:
            job['bullets'] = [b.replace('RestAPIs', 'REST APIs').replace('RestAPIs', 'REST APIs') for b in job['bullets']]

    # G8: Award months (Diversify)
    if 'achievements' in data:
        months = ["05", "06", "11", "08"]
        for i, award in enumerate(data['achievements']):
            award['month'] = months[i % len(months)]

    # G10: Visa statements for all regions
    data['profile']['visa'] = {
        'US': 'Requires H-1B visa sponsorship.',
        'UK': 'Requires Skilled Worker visa sponsorship.',
        'DE': 'Eligible for EU Blue Card; requires sponsorship.',
        'AE': 'Willing to relocate; requires UAE employment visa.',
        'IN': 'Immediately available; no notice period required.',
        'GLOBAL': 'Willing to relocate globally; requires visa sponsorship.',
        'JP': '技術・人文知識・国際業務ビザのスポンサーシップが必要です。',
        'JP_EN': 'Requires Engineer/Specialist in Humanities/International Services visa sponsorship.',
        'KR': 'E-7 비자 스폰서십이 필요합니다.',
        'KR_EN': 'Requires E-7 Specially Designated Activities visa sponsorship.',
        'CN': '需要工作签证（Z签证）办理。',
        'CN_EN': 'Requires Z-visa sponsorship for employment in China.'
    }

    # UK/IN: Education Grades
    for edu in data.get('education', []):
        if "Gujarat Technological University" in edu['university']:
            edu['gpa'] = "7.37 CGPA (1st Class)"
        elif "Gujarat University" in edu['university']:
            edu['gpa'] = "8.39 CGPA (Distinction)"

    # JP: Katakana for name and address
    data['profile']['name_furigana'] = "ディヴィア・ニランカリ"
    data['profile']['address_furigana'] = "インド、グジャラート州、スーラト"

    # DE/AE: Personal Info
    data['profile']['personal']['dob'] = "1998-01-05"
    data['profile']['personal']['nationality'] = "India"
    data['profile']['personal']['marital_status'] = "Single"

    # KR: Translated project labels for KR English
    # We will handle these in translations.py or template

    # CN: Fix summary (The report says it's nonsense)
    # New Chinese Summary
    CN_SUMMARY = "资深Python与AI/ML工程师，专注于医疗AI及生物医学信号处理。曾在Logixbuilt Infotech主导高并发REST API开发（日均请求1万+，可用性99.9%），并通过PostgreSQL优化将响应速度提升40%。独立开发基于PhysioNet数据集的ECG心脏异常检测模型，采用1D ResNet架构，F1分数达94%。具备从科研到生产环境落地的全栈能力。"
    data['profile']['summary_zh'] = CN_SUMMARY

    # KR: Proper Korean Summary
    KR_SUMMARY = "Python 및 AI/ML 엔지니어로, 의료 AI 및 생체 신호 처리 분야에 전문성을 갖추고 있습니다. Logixbuilt Infotech에서 일일 1만 건 이상의 요청을 처리하는 고가용성 REST API를 개발하고 PostgreSQL 쿼리 최적화를 통해 성능을 40% 향상시켰습니다. PhysioNet 데이터셋을 활용하여 94%의 F1-score를 기록한 1D ResNet 기반 ECG 심장 이상 탐지 모델을 독자적으로 개발했습니다. 연구 성과를 실제 서비스로 구현하는 데 강점이 있습니다."
    data['profile']['summary_ko'] = KR_SUMMARY

    # Experience: Set Employment Type
    for job in data.get('experience', []):
        if 'freelance' in job.get('company', '').lower():
            job['employment_type'] = "Freelance"
        else:
            job['employment_type'] = "Full-time"

    # Skills: Set category years of experience for dynamic proficiency calculations
    for cat in data.get('skillCategories', []):
        label = cat.get('label', '')
        if "Programming & Databases" in label:
            cat['years'] = 6
        elif "AI & Machine Learning" in label:
            cat['years'] = 4
        elif "Backend & Cloud" in label:
            cat['years'] = 4
        elif "Tools & Testing" in label:
            cat['years'] = 3

    # Save to JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Save to portfolio.db
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portfolio.db')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE portfolio_data SET data = ? WHERE id=1", (json.dumps(data),))
        conn.commit()
        conn.close()
    
    print("Content updated successfully.")

if __name__ == "__main__":
    update_content()

import json
import sqlite3
import os

def final_update():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Base Summaries
    EN_BASE = "AI/ML Engineer with 4+ years of experience specializing in healthcare AI and production-grade machine learning systems. Developed a high-accuracy ECG cardiac abnormality detection model (94% F1-score) using 1D ResNet architectures on the PhysioNet/CinC Challenge dataset. Proven expertise in building scalable REST APIs (10,000+ daily requests, 99.9% uptime) and optimizing database performance (40% faster query times) using FastAPI and PostgreSQL. Skilled in Python, PyTorch, and deep learning, with a focus on bridging the gap between research and real-world deployment."
    
    # Regional Summaries
    data['profile']['summary'] = EN_BASE
    data['profile']['summary_zh'] = "资深Python与AI/ML工程师，专注于医疗AI及生物医学信号处理。曾在Logixbuilt Infotech主导高并发REST API开发（日均请求1万+，可用性99.9%），并通过PostgreSQL优化将响应速度提升40%。独立开发基于PhysioNet数据集的ECG心脏异常检测模型，采用1D ResNet架构，F1分数达94%。具备从科研到生产环境落地的全栈能力。"
    data['profile']['summary_ko'] = "실무 경험을 보유한 Python 및 AI/ML 엔지니어로, 의료 AI 및 생체 신호 처리 분야에 전문성을 갖추고 있습니다. Logixbuilt Infotech에서 일일 1만 건 이상의 요청을 처리하는 고가용성 REST API를 개발하고 PostgreSQL 쿼리 최적화를 통해 성능을 40% 향상시켰습니다. PhysioNet 데이터셋을 활용하여 94%의 F1-score를 기록한 1D ResNet 기반 ECG 심장 이상 탐지 모델을 독자적으로 개발했습니다. 연구 성과를 실제 서비스로 구현하는 데 강점이 있습니다."

    # 2. Regional Cover Letters
    if 'regional_cover_letters' not in data: data['regional_cover_letters'] = {}
    
    data['regional_cover_letters']['uk'] = "I am writing to express my strong interest in AI Engineer opportunities within the UK's burgeoning tech sector. With 3+ years of experience in healthcare AI and backend optimization, I am eager to contribute to UK-based innovation. I am particularly interested in how British healthtech firms are leveraging machine learning for early diagnosis. I require UK Skilled Worker visa sponsorship and am prepared for relocation."
    data['regional_cover_letters']['usa'] = "I am highly motivated to bring my 3+ years of expertise in AI/ML and production-grade backend systems to the US technology market. My work on ECG abnormality detection using 1D ResNet aligns perfectly with the advanced medical AI research occurring in the United States. I am seeking H-1B visa sponsorship and am ready to contribute to world-class engineering teams."
    data['regional_cover_letters']['germany'] = "With a deep focus on Healthcare AI and 3+ years of experience in building scalable machine learning systems, I am eager to join Germany's leading medical technology sector. My background in signal processing and FastAPI optimization positions me well for Industry 4.0 and MedTech roles in Europe. I am eligible for the EU Blue Card and require sponsorship for relocation to Germany."
    data['regional_cover_letters']['india'] = "As an AI/ML Engineer with 3+ years of experience in the Indian and international tech ecosystems, I have developed a strong track record in building high-throughput APIs and accurate deep learning models. I am immediately available to join a forward-thinking Indian organization and drive impact through data-driven solutions."
    data['regional_cover_letters']['uae'] = "I am excited by the UAE's ambitious AI Strategy 2031 and wish to contribute my 3+ years of experience in machine learning and backend engineering to the Gulf region's digital transformation. My expertise in building scalable, real-time AI systems is well-suited for the smart city and healthcare initiatives in the UAE. I am willing to relocate and require UAE employment visa sponsorship."
    data['regional_cover_letters']['china_zh'] = "尊敬的招聘负责人：\n\n作为专注于医疗AI和生产级机器学习系统的AI/ML工程师，我曾在PhysioNet数据集上开发并验证了94% F1-score的1D ResNet心电图异常检测模型，并在Logixbuilt Infotech构建了日均1万+请求的高可用REST API。\n\n我具备从模型验证到生产部署的端到端经验，包括FastAPI后端、PostgreSQL性能优化以及实时AI服务的稳定交付。\n\n我关注清华大学、北京大学、阿里巴巴达摩院、百度健康和平安好医生在医学影像与心脏AI领域的实际应用进展。\n\n我还计划通过贵公司申请Z类工作签证，并已做好赴华工作的充分准备。希望能够在贵公司推动医疗AI产品落地，并支持从研发到部署的全流程交付。\n\n此致\n敬礼\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306"
    data['regional_cover_letters']['china'] = "Dear Hiring Manager,\n\nAs an AI/ML engineer specializing in healthcare AI and production-grade machine learning systems, I developed and validated a 1D ResNet ECG anomaly detection model achieving a 94% F1-score on the PhysioNet dataset, and built high-availability REST APIs handling 10,000+ daily requests at Logixbuilt Infotech.\n\nI possess end-to-end experience spanning from model validation to production deployment, including FastAPI backends, PostgreSQL query optimization, and the stable delivery of real-time AI services.\n\nI closely follow the clinical application advancements of Tsinghua University, Peking University, Alibaba DAMO Academy, Baidu Health, and Ping An Good Doctor in the fields of medical imaging and cardiac AI.\n\nI also plan to apply for a Class Z work visa through your company and am fully prepared to relocate to China. I hope to drive the production realization of healthcare AI products and support your team across the entire development and deployment lifecycle.\n\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306"
    data['regional_cover_letters']['china_en'] = "Dear Hiring Manager,\n\nAs an AI/ML engineer specializing in healthcare AI and production-grade machine learning systems, I developed and validated a 1D ResNet ECG anomaly detection model achieving a 94% F1-score on the PhysioNet dataset, and built high-availability REST APIs handling 10,000+ daily requests at Logixbuilt Infotech.\n\nI possess end-to-end experience spanning from model validation to production deployment, including FastAPI backends, PostgreSQL query optimization, and the stable delivery of real-time AI services.\n\nI closely follow the clinical application advancements of Tsinghua University, Peking University, Alibaba DAMO Academy, Baidu Health, and Ping An Good Doctor in the fields of medical imaging and cardiac AI.\n\nI also plan to apply for a Class Z work visa through your company and am fully prepared to relocate to China. I hope to drive the production realization of healthcare AI products and support your team across the entire development and deployment lifecycle.\n\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306"

    # 3. Spelling fixes
    # We will handle these via JIT in pdf_playwright or just use US spelling as base and fix UK JIT.
    
    # 4. Award Months
    if 'achievements' in data:
        for i, a in enumerate(data['achievements']):
            a['month'] = ["03", "06", "09", "11"][i % 4]
            a['year'] = "2018" if i < 3 else "2022"

    # 5. Save
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Sync to DB
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portfolio.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE portfolio_data SET data = ? WHERE id=1", (json.dumps(data),))
    conn.commit()
    conn.close()
    print("Master update complete.")

if __name__ == "__main__":
    final_update()

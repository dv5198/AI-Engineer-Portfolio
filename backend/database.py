import json
import os
import shutil
import sqlite3
import time
from datetime import datetime
from filelock import FileLock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "portfolio.db")
LOCK_FILE = os.path.join(BASE_DIR, "portfolio.db.lock")

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS portfolio_data (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_name TEXT NOT NULL,
                locale TEXT NOT NULL,
                original_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                is_verified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(field_name, locale, original_text)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS pdf_cache (
                id TEXT PRIMARY KEY,
                pdf_blob BLOB NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.commit()

init_db()

DEFAULT_DATA = {
    "profile": {
        "name": "Divya Nirankari",
        "role": "Software Engineer & AI/ML Engineer",
        "email": "dvnirankari@gmail.com",
        "phone": "+91 9265768306",
        "location": "Surat, Gujarat, India",
        "summary": "Python and AI/ML Engineer with 3+ years of experience building production-ready machine learning systems, with a deep focus on Healthcare AI and biomedical signal processing. At Logixbuilt Infotech, I developed high-throughput REST APIs (10k+ daily requests, 99.9% uptime) and reduced database response times by 40% through PostgreSQL query optimisation. As a freelance engineer, I have designed ECG cardiac abnormality detection models achieving 94% F1-score using 1D CNN and ResNet architectures on the PhysioNet dataset, and built real-time AI-powered chatbots integrated across WhatsApp, Telegram, and Messenger. I am currently authoring a research paper on deep learning-based ECG analysis and am actively studying Japanese, with the goal of contributing to Japan's world-class AI research and healthcare technology ecosystem.",
        "bio": "Python and AI/ML Engineer specialising in Healthcare AI and biomedical signal processing. I build production-grade ML systems and scalable backends — from ECG cardiac detection models to real-time chatbot integrations.",
        "personal": {
            "dob": "1998-01-05",
            "gender": "female",
            "nationality": "India",
            "marital_status": "Single",
            "political_status": "",
            "wechat_id": "",
            "military_service": "No",
            "japanese_era_dates": False,
            "name_furigana": "ディヴィア・ニランカリ",
            "nationality_ja": "インド",
            "address_furigana": "インド グジャラート州 スーラト",
            "commute_time": "",
            "dependents_count": 0,
            "has_spouse": False,
            "spouse_dependency": False,
            "self_pr_ja": "Python・AI/MLエンジニアとして、医療AI分野に特化した実務経験を持ちます。ECG信号を用いた心臓異常検知モデル（1D CNN / ResNet、F1スコア94%）や、FastAPIを活用したスケーラブルなバックエンドシステムの開発に携わってまいりました。現在、日本語を積極的に学習中であり、日本の先進的なAI研究・開発環境において貢献したいと考えています。",
            "self_pr_ja_detailed": "Python・AI/MLエンジニアとして約3年の実務経験を有し、医療AIおよびバックエンド開発に注力してまいりました。Logixbuilt Infotech社ではFastAPIによるREST API開発・PostgreSQLクエリ最適化・自動テストパイプライン構築に従事し、フリーランスとして国際的なクライアント向けにPyTorchを用いた本番環境MLモデルの設計・ECG心臓異常検知システム（1D ResNet、PhysioNetデータセット使用）の開発を担当しました。現在は1D ResNetを用いた心臓異常検知に関する研究論文を執筆中です。在学中には「Data Structure Excellence Award」「Student of the Year」等の学業表彰を受けており、日本の医療AI・ヘルスケアテック分野でその専門性を活かし、社会に貢献することを目指しています。",
            "career_summary_ja": "Python・AI/MLエンジニアとして約3年の実務経験を有し、医療AIおよびバックエンド開発に注力してまいりました。Logixbuilt Infotech社ではFastAPIによるREST API開発・PostgreSQLクエリ最適化・自動テストパイプライン構築に従事し、フリーランスとして国際的なクライアント向けにPyTorchを用いた本番環境MLモデルの設計・ECG心臓異常検知システム（1D ResNet、PhysioNetデータセット使用）の開発を担当しました。現在は1D ResNetを用いた心臓異常検知に関する研究論文を執筆中であり、日本の医療AI・ヘルスケアテック分野でその専門性を活かし、社会に貢献することを目指しています。",
            "desired_conditions_ja": "貴社の規定に従います。"
        },
        "visa_info": {
            "visaType": "",
            "visaIssueDate": "",
            "visaExpiryDate": ""
        }
    },
    "connections": [
        {"id": "conn_1", "platform": "GitHub", "url": "https://github.com/dv5198", "handle": "dv5198", "visible": True, "order": 0},
        {"id": "conn_2", "platform": "LinkedIn", "url": "https://www.linkedin.com/in/divya-nirankari/", "handle": "Divya Nirankari", "visible": True, "order": 1},
        {"id": "conn_3", "platform": "Email", "url": "mailto:dvnirankari@gmail.com", "handle": "dvnirankari@gmail.com", "visible": True, "order": 2},
        {"id": "conn_4", "platform": "YouTube", "url": "", "handle": "", "visible": False, "order": 3},
        {"id": "conn_5", "platform": "Instagram", "url": "", "handle": "", "visible": False, "order": 4},
        {"id": "conn_6", "platform": "KakaoTalk", "url": "", "handle": "", "visible": False, "order": 5}
    ],
    "about": [
        "I am a Python and AI/ML Engineer with a deep focus on Healthcare AI, building systems that bridge cutting-edge research with real-world impact.",
        "My core expertise is in biomedical signal processing — I have designed ECG cardiac abnormality detection models using 1D CNN and ResNet architectures, achieving 94% F1-score on the PhysioNet dataset.",
        "On the backend, I architect scalable FastAPI systems, Redis-cached data pipelines, and production ML inference APIs deployed for international clients."
    ],
    "stats": {
        "projects_count": "12+",
        "years_experience": "3+",
        "ml_models": "6+",
        "fun_stat": "94% F1-Score on ECG Model"
    },
    "skills": ["Python", "JavaScript", "React", "FastAPI", "PyTorch", "TensorFlow", "SQL", "Docker", "AWS"],
    "skillCategories": [
        {
            "label": "AI & Machine Learning",
            "items": ["PyTorch", "TensorFlow", "Scikit-learn", "CNN", "1D ResNet", "LSTM", "Random Forest", "NLP", "Computer Vision", "Biomedical Signal Processing (ECG)", "Model Evaluation", "Hyperparameter Tuning"],
            "visible": True, "order": 1
        },
        {
            "label": "Backend & APIs",
            "items": ["Python", "FastAPI", "Django", "REST APIs", "GraphQL", "PostgreSQL", "Redis", "MongoDB", "SQL"],
            "visible": True, "order": 2
        },
        {
            "label": "Data & ML Ops",
            "items": ["Pandas", "NumPy", "SciPy", "Data Preprocessing", "Feature Engineering", "Git", "AWS", "K6 API Testing"],
            "visible": True, "order": 3
        }
    ],
    "sections_visibility": {
        "about": True,
        "skills": True,
        "projects": True,
        "contact": True,
        "experience": True,
        "achievements": False,
        "activity": False,
        "timeline": True,
        "research": False,
        "testimonials": False,
        "blog": False
    },
    "project_visibility": {},
    "researchInterests": [],
    "testimonials": [],
    "blogPosts": [],
    "languages": [
        {"id": "lang_1", "name": "English", "level": "Fluent / Professional", "percentage": 95, "visible": True, "order": 1},
        {"id": "lang_2", "name": "Hindi", "level": "Native", "percentage": 100, "visible": True, "order": 2},
        {"id": "lang_3", "name": "Korean", "level": "Basic", "percentage": 10, "visible": True, "order": 3},
        {"id": "lang_4", "name": "Japanese", "level": "Beginner (Currently Learning)", "percentage": 8, "visible": True, "order": 4}
    ],
    "experience": [
        {
            "id": "exp_1",
            "company": "Logixbuilt Infotech",
            "role": "Python Software Engineer",
            "startDate": "Mar 2022",
            "endDate": "Apr 2023",
            "resign_reason_ja": "一身上の都合により退社",
            "bullets": [
                "Developed REST APIs using FastAPI handling 10k+ daily requests with 99.9% uptime.",
                "Optimized PostgreSQL queries reducing average response time by 40%.",
                "Built automated testing pipelines using pytest cutting bug detection time by 50%."
            ],
            "visible": True
        },
        {
            "id": "exp_2",
            "company": "Freelance",
            "role": "Python & AI/ML Engineer",
            "startDate": "Jan 2023",
            "endDate": "Present",
            "bullets": [
                "Designed production-grade ML models for international clients using PyTorch and FastAPI.",
                "Built real-time chatbot system integrated with WhatsApp, Telegram, Facebook Messenger.",
                "Developed ECG cardiac abnormality detection model achieving 94% F1-score on PhysioNet dataset.",
                "Architected scalable backend systems with Redis caching and PostgreSQL data pipelines."
            ],
            "visible": True
        }
    ],
    "education": [
        {
            "id": "edu_1",
            "university": "Veer Narmad South Gujarat University",
            "degree": "Master of Computer Applications (MCA)",
            "major": "Computer Application",
            "year": "2020 – 2022",
            "awarded": "2023",
            "gpa": "A+",
            "notes": "Specialization in Artificial Intelligence",
            "visible": True,
            "order": 1
        },
        {
            "id": "edu_2",
            "university": "Vivekanand College of Computer Science",
            "degree": "Bachelor of Computer Applications (BCA)",
            "major": "Computer Application",
            "year": "2017 – 2020",
            "awarded": "2020",
            "gpa": "",
            "notes": "",
            "visible": True,
            "order": 2
        }
    ],
    "certifications": [],
    "achievements": [
        {"id": "ach_award_1", "title": "Data Structure Excellence Award", "year": "2018", "issuer": "Gujarat University", "description": "Academic excellence award in Data Structures", "visible": True},
        {"id": "ach_award_2", "title": "Database Management System Award", "year": "2018", "issuer": "Gujarat University", "description": "Academic excellence award in DBMS", "visible": True},
        {"id": "ach_award_3", "title": "Student of the Year", "year": "2019", "issuer": "Gujarat University", "description": "Awarded Student of the Year across the department", "visible": True},
        {"id": "ach_4", "title": "Most Diligent Employee", "year": "2022", "issuer": "Logixbuilt Infotech", "description": "Awarded Most Diligent Employee at Logixbuilt Infotech", "visible": True}
    ],
    "contactMessages": [],
    "analytics": [],
    "activityLog": [],
    "projects": [
        {
            "name": "Sample Manual Project",
            "description": "An example project added manually.",
            "image": "",
            "image_override": "",
            "visible": False
        }
    ],
    "hiddenProjects": [],
    "projectSummaries": {},
    "settings": {"hero3d": True}
}

def load_data():
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM portfolio_data WHERE id = 1")
            row = cursor.fetchone()
            
            if not row:
                # DB is empty, seed it with DEFAULT_DATA
                conn.execute(
                    "INSERT INTO portfolio_data (id, data, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)",
                    (json.dumps(DEFAULT_DATA, ensure_ascii=False),)
                )
                conn.commit()
                return DEFAULT_DATA
            
            data = json.loads(row[0])
            changed = False
    
            # Migration 1: Move legacy flat profile fields to nested structures
            if "profile" in data:
                profile = data["profile"]
                
                # Setup nested objects if missing
                if "personal" not in profile:
                    profile["personal"] = DEFAULT_DATA["profile"]["personal"].copy()
                    changed = True
                
                if "visa_info" not in profile:
                    profile["visa_info"] = DEFAULT_DATA["profile"]["visa_info"].copy()
                    changed = True
                
                # Move flat fields into personal/visa_info
                flat_to_personal = ["dob", "dateOfBirth", "gender", "nationality", "military_service", "marital_status"]
                for field in flat_to_personal:
                    if field in profile:
                        # 'dateOfBirth' maps to 'dob' for consistency in some generic contexts, but keep field name if preferred
                        target_field = "dob" if field == "dateOfBirth" else field
                        profile["personal"][target_field] = profile.pop(field)
                        changed = True
                
                flat_to_visa = ["visaType", "visaIssueDate", "visaExpiryDate"]
                for field in flat_to_visa:
                    if field in profile:
                        profile["visa_info"][field] = profile.pop(field)
                        changed = True
    
                # Migration 1.5: Ensure all personal fields exist safely
                japan_fields = {
                    "name_furigana": "",
                    "nationality_ja": "",
                    "address_furigana": "",
                    "commute_time": "",
                    "dependents_count": 0,
                    "has_spouse": False,
                    "spouse_dependency": False,
                    "self_pr_ja": "",
                    "self_pr_ja_detailed": "",
                    "career_summary_ja": "",
                    "desired_conditions_ja": "貴社の規定に従います。"
                }
                if "personal" in profile:
                    for k, v in japan_fields.items():
                        if k not in profile["personal"]:
                            profile["personal"][k] = v
                            changed = True
    
            # Migration 2: Ensure all DEFAULT_DATA keys exist
            for k, v in DEFAULT_DATA.items():
                if k not in data:
                    data[k] = v
                    changed = True
                    
            if changed:
                _save_data_internal(data)
            return data

def save_data(data):
    with FileLock(LOCK_FILE, timeout=10):
        _save_data_internal(data)

def _save_data_internal(data):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO portfolio_data (id, data, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)",
            (json.dumps(data, ensure_ascii=False),)
        )
        conn.commit()
    
    # Clear PDF cache
    try:
        from services.cache_service import clear_pdf_cache
        clear_pdf_cache()
    except ImportError:
        pass

def log_resume_download(ip: str, country: str, region: str, format_label: str):
    """
    Logs a resume download event into the analytics list.
    Keeps only the last 100 entries to prevent file bloat.
    """
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM portfolio_data WHERE id = 1")
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row[0])
            else:
                data = DEFAULT_DATA.copy()
                
            if "analytics" not in data:
                data["analytics"] = []
                
            event_entry = {
                "timestamp": datetime.now().isoformat(),
                "event": "resume_download",
                "ip": ip,
                "country": country,
                "region": region,
                "format": format_label
            }
            
            data["analytics"].insert(0, event_entry)
            
            if len(data["analytics"]) > 100:
                data["analytics"] = data["analytics"][:100]
                
            conn.execute(
                "INSERT OR REPLACE INTO portfolio_data (id, data, updated_at) VALUES (1, ?, CURRENT_TIMESTAMP)",
                (json.dumps(data, ensure_ascii=False),)
            )
            conn.commit()
            
    return event_entry

def get_cached_translation(field_name: str, locale: str, original_text: str):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT translated_text, is_verified FROM translations WHERE field_name = ? AND locale = ? AND original_text = ?",
                (field_name, locale, original_text)
            )
            return cursor.fetchone()

def save_translation(field_name: str, locale: str, original_text: str, translated_text: str, is_verified: bool = False):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO translations 
                   (field_name, locale, original_text, translated_text, is_verified, updated_at) 
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (field_name, locale, original_text, translated_text, 1 if is_verified else 0)
            )
            conn.commit()

def mark_translation_verified(field_name: str, locale: str, original_text: str):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "UPDATE translations SET is_verified = 1, updated_at = CURRENT_TIMESTAMP WHERE field_name = ? AND locale = ? AND original_text = ?",
                (field_name, locale, original_text)
            )
            conn.commit()

def get_cached_pdf_db(cache_key: str, ttl_seconds: int = 300):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pdf_blob, created_at FROM pdf_cache WHERE id = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            if row:
                pdf_blob, created_at = row
                # Check TTL
                created_dt = datetime.fromisoformat(created_at.replace(" ", "T")) if " " in created_at else datetime.fromisoformat(created_at)
                if (datetime.now() - created_dt).total_seconds() < ttl_seconds:
                    return pdf_blob
                else:
                    # Expired
                    conn.execute("DELETE FROM pdf_cache WHERE id = ?", (cache_key,))
                    conn.commit()
            return None

def save_cached_pdf_db(cache_key: str, pdf_blob: bytes):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO pdf_cache (id, pdf_blob, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (cache_key, sqlite3.Binary(pdf_blob))
            )
            conn.commit()

def clear_pdf_cache_db():
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM pdf_cache")
            conn.commit()

def get_all_translations():
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM translations ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

def delete_translation_db(t_id: int):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM translations WHERE id = ?", (t_id,))
            conn.commit()


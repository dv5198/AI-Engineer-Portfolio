import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")


DEFAULT_DATA = {
    "profile": {
        "name": "Divya Nirankari",
        "role": "Software Engineer & AI/ML Engineer",
        "email": "dvnirankari@gmail.com",
        "phone": "+91 9265768306",
        "location": "Surat, Gujarat, India",
        "summary": "AI Engineer specializing in building intelligent systems and scalable web applications. Passionate about Deep Learning and Backend Architecture.",
        "bio": "I am a passionate software engineer with a focus on AI and ML. I enjoy solving complex problems and building innovative solutions.",
        "personal": {
            "dob": "",
            "gender": "",
            "nationality": "",
            "marital_status": "",
            "political_status": "",
            "wechat_id": "",
            "military_service": "",
            "japanese_era_dates": False
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
        "I am a passionate engineer with experience in full-stack development and artificial intelligence.",
        "My work focuses on bridging the gap between cutting-edge ML research and practical, user-facing applications.",
        "When I'm not coding, I enjoy exploring new technologies and contributing to open-source projects."
    ],
    "stats": {
        "projects_count": "15+",
        "years_experience": "4",
        "ml_models": "8",
        "fun_stat": "10k+ Lines of Code"
    },
    "skills": ["Python", "JavaScript", "React", "FastAPI", "PyTorch", "TensorFlow", "SQL", "Docker", "AWS"],
    "skillCategories": [
        {
            "label": "AI & Machine Learning",
            "items": ["TensorFlow", "PyTorch", "Scikit-learn", "Hugging Face", "OpenCV", "NLP", "Computer Vision"],
            "visible": True, "order": 1
        },
        {
            "label": "Backend & Cloud",
            "items": ["Python (FastAPI, Django)", "Node.js", "SQL", "PostgreSQL", "AWS", "GCP", "Docker", "Redis"],
            "visible": True, "order": 2
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
        {"id": "lang_1", "name": "English", "level": "Business Level", "percentage": 90, "visible": True, "order": 1},
        {"id": "lang_2", "name": "Hindi", "level": "Native", "percentage": 100, "visible": True, "order": 2}
    ],
    "experience": [
        {
            "id": "exp_1",
            "company": "Freelance",
            "role": "Python & AI/ML Engineer",
            "location": "Surat, India",
            "startDate": "Jan 2023",
            "endDate": "Present",
            "bullets": [
                "Designed and implemented production-grade ML models for international clients using PyTorch and FastAPI.",
                "Architected scalable backend systems with optimized Redis caching and PostgreSQL data pipelines.",
                "Developed custom NLP solutions for text classification and sentiment analysis with Hugging Face transformers."
            ],
            "visible": True
        }
    ],
    "education": [
        {
            "id": "edu_1",
            "university": "Veer Narmad South Gujarat University",
            "degree": "Master of Computer Applications (MCA)",
            "year": "2020 – 2022",
            "awarded": "2023",
            "gpa": "A+",
            "notes": "Specialization in Artificial Intelligence",
            "visible": True,
            "order": 1
        }
    ],
    "certifications": [
        {"id": "cert_1", "name": "Machine Learning Specialization", "issuer": "DeepLearning.AI", "year": "2023", "visible": True}
    ],
    "contactMessages": [],
    "analytics": [],
    "activityLog": [],
    "hiddenProjects": [],
    "projectSummaries": {},
    "settings": {"hero3d": True}
}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, indent=4, ensure_ascii=False)
        return DEFAULT_DATA
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
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

        # Migration 2: Ensure all DEFAULT_DATA keys exist
        for k, v in DEFAULT_DATA.items():
            if k not in data:
                data[k] = v
                changed = True
                
        if changed:
            save_data(data)
        return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def log_resume_download(ip: str, country: str, region: str, format_label: str):
    """
    Logs a resume download event into the analytics list.
    Keeps only the last 100 entries to prevent file bloat.
    """
    data = load_data()
    
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
    
    # Prepend new event
    data["analytics"].insert(0, event_entry)
    
    # Prune to keep only top 100
    if len(data["analytics"]) > 100:
        data["analytics"] = data["analytics"][:100]
        
    save_data(data)
    return event_entry

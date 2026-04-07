import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")


DEFAULT_DATA = {
    "profile": {
        "name": "Divya Nirankari",
        "role": "Software Engineer & AI/ML Engineer",
        # "bio": "I build scalable web ait must not be pplications and intelligent machine learning models.",
        "github": "https://github.com/dv5198",
        "github_username": "dv5198",
        "linkedin": "https://www.linkedin.com/in/divya-nirankari/",
        "email": "dvnirankari@gmail.com",
        "phone": "+91 9265768306",
        "location": "Surat, Gujarat, India"
    },
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
        with open(DATA_FILE, "w") as f:
            json.dump(DEFAULT_DATA, f, indent=4)
        return DEFAULT_DATA
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        # Migration: Ensure all DEFAULT_DATA keys exist
        changed = False
        for k, v in DEFAULT_DATA.items():
            if k not in data:
                data[k] = v
                changed = True
        if changed:
            save_data(data)
        return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

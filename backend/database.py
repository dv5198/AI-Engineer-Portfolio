import json
import os

DATA_FILE = "data.json"

DEFAULT_DATA = {
    "profile": {
        "name": "Alex Sharma",
        "role": "Software Engineer & AI/ML Engineer",
        "bio": "I build scalable web applications and intelligent machine learning models.",
        "github": "https://github.com/alexsharma",
        "linkedin": "https://linkedin.com/in/alexsharma",
        "email": "alex@example.com"
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
    "sections_visibility": {
        "about": True,
        "skills": True,
        "projects": True,
        "contact": True
    },
    "project_visibility": {}
}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump(DEFAULT_DATA, f, indent=4)
        return DEFAULT_DATA
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

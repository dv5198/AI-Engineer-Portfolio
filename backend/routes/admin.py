import time
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from typing import List
from services.groq_service import (
    rewrite_text, 
    execute_admin_command,
    call_groq,
    summarize_about
)
from database import load_data, save_data
from services.github import fetch_github_projects
import shutil
import os

router = APIRouter()

class LoginRequest(BaseModel):
    password: str

class CommandRequest(BaseModel):
    command: str

class RewriteRequest(BaseModel):
    text: str
    instruction: str = "Make it sound more professional and engaging"

# Secure Token Loading
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SESSION_TOKEN = os.getenv("SESSION_TOKEN", "admin_secret_token_42")

login_attempts = {}

@router.post("/login/")
def login(req: LoginRequest, request: Request):
    ip = request.client.host
    now = time.time()
    
    # Keep only attempts within the last 15 minutes (900 seconds)
    attempts = [t for t in login_attempts.get(ip, []) if now - t < 900]
    
    if len(attempts) >= 5:
        login_attempts[ip] = attempts
        raise HTTPException(status_code=429, detail="Too many failed attempts. Please try again in 15 minutes.")
        
    if req.password == ADMIN_PASSWORD:
        if ip in login_attempts:
            del login_attempts[ip]
        return {"token": SESSION_TOKEN}
        
    attempts.append(now)
    login_attempts[ip] = attempts
    raise HTTPException(status_code=401, detail="Invalid password")

from fastapi import BackgroundTasks

@router.post("/command/")
async def process_command(req: CommandRequest, background_tasks: BackgroundTasks):
    current_data = load_data()
    # Execute command using Claude to get structural changes
    changes = await execute_admin_command(req.command, current_data)
    
    if "error" in changes:
        raise HTTPException(status_code=500, detail=changes["error"])
        
    # Apply changes natively here, simulating what portfolio update does
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
        
    updated = deep_update(current_data, changes)
    save_data(updated)
    
    from routes.dynamic_sections import log_activity
    log_activity(f"Applied AI command: {req.command}", "Admin AI", changes)
    
    from services.groq_service import auto_regenerate_summary_task
    background_tasks.add_task(auto_regenerate_summary_task)
    
    return {"message": "Command executed successfully", "changes_applied": changes, "new_data": updated}

@router.post("/rewrite-bio/")
async def rewrite_bio_route(req: RewriteRequest):
    new_text = await rewrite_text(req.text, req.instruction)
    return {"rewritten": new_text}
    
@router.post("/rewrite-about/")
async def rewrite_about_route(req: RewriteRequest):
    new_text = await rewrite_text(req.text, req.instruction)
    return {"rewritten": new_text}
    
class GroqTestRequest(BaseModel):
    message: str

@router.post("/test-groq/")
async def test_groq_route(req: GroqTestRequest):
    res = await call_groq(req.message)
    return {"response": res}

class SummarizeRequest(BaseModel):
    about_list: List[str]

@router.post("/rewrite-summary/")
async def rewrite_summary_route(req: SummarizeRequest):
    res = await summarize_about(req.about_list)
    return {"rewritten": res}

class CoverLetterGenerateRequest(BaseModel):
    about: List[str]
    experience: List[dict]
    region: str = "international"
    lang: str = "en"

@router.post("/generate-cover-letter/")
async def generate_cover_letter_route(req: CoverLetterGenerateRequest):
    from services.groq_service import call_groq_json
    
    about_text = "\n".join(req.about)
    exp_summary = "\n".join([f"- {e.get('role')} at {e.get('company')}: {e.get('description', '')}" for e in req.experience[:3]])
    
    system_prompt = "You are an expert Global Career Consultant. Return ONLY a JSON object."
    
    user_prompt = f"""
    Create a professional cover letter based on this candidate's data.
    Target Region: {req.region}
    Target Language: {req.lang} (Return the content in this language!)
    
    Candidate Background:
    {about_text}
    
    Recent Experience:
    {exp_summary}
    
    If the region is 'korea', return these EXACT 4 keys:
    "growth_background", "strengths_weaknesses", "motivation", "goals_after_joining"
    
    If the region is 'japan', return these EXACT keys:
    "content" (Full body of the 'Soe-jo' (添え状) following this 3-part Daijob.com structure:
        1. Background (Paragraph 1): Position interest and why (貴社の求人概要を拝見し、応募させていただきました).
        2. Experience Summary (Paragraph 2): Skills matching and what you bring (Why you are a fit).
        3. Interview Request (Paragraph 3): Mention availability and contact info.
        Use formal Japanese honorifics. Start with '採用ご担当者様' and '[Name]と申します。'.
        End with 'お忙しいなか恐縮ですが、どうぞ宜しくお願い致します。'),
    "self_pr_ja" (A separate Self-PR section for the Rirekisho)
    
    For all other regions, return:
    "content" (Full body in professional standard style)
    
    Tone: Sophisticated, impactful, and tailored to the {req.region} professional culture.
    Return ONLY JSON.
    """
    
    res = await call_groq_json(system_prompt, user_prompt)
    return res

class GenerateBulletsRequest(BaseModel):
    role: str
    company: str
    description: str

@router.post("/generate-bullets/")
async def generate_bullets_route(req: GenerateBulletsRequest):
    prompt = f"Generate 3 professional, action-oriented resume bullets for a {req.role} at {req.company} based on this description: {req.description}. Return ONLY the bullets starting with a dash (-). No introductory text."
    res = await call_groq(prompt)
    # Llama/Groq often uses '*' or '-' and might still include empty lines
    bullets = [b.strip().lstrip('-').lstrip('*').strip() for b in res.split('\n') if b.strip() and (b.strip().startswith('-') or b.strip().startswith('*'))]
    if not bullets:
        # Fallback if the model didn't use list markers
        bullets = [b.strip() for b in res.split('\n') if b.strip() and len(b.strip()) > 15]
    return {"bullets": bullets}
    
@router.get("/projects/all/")
async def get_all_projects_admin():
    data = load_data()
    github_handle = data.get("profile", {}).get("github", "")
    username = github_handle.split("/")[-1] if github_handle else "alexsharma"
    
    repos = await fetch_github_projects(username)
    if repos is None:
        raise HTTPException(status_code=503, detail="GitHub API Error")
    
    formatted = []
    for r in repos:
        formatted.append({
            "name": r["name"],
        })
    return formatted

@router.post("/achievement-image/")
async def upload_achievement_image(file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    file_path = os.path.join(UPLOAD_DIR, "award.jpg")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": "http://localhost:8001/uploads/award.jpg"}

@router.post("/profile-photo/")
async def upload_profile_photo(file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    file_path = os.path.join(UPLOAD_DIR, "profile_photo.jpg")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": "http://localhost:8001/uploads/profile_photo.jpg"}

@router.post("/project-image/")
async def upload_project_image(file: UploadFile = File(...)):
    import uuid
    UPLOAD_DIR = "uploads"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    filename = f"project_{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": f"uploads/{filename}"}

# --- Translation Management ---
from database import get_all_translations, delete_translation_db, DB_FILE, LOCK_FILE
from filelock import FileLock
import sqlite3

class TranslationUpdateRequest(BaseModel):
    id: int
    translated_text: str
    is_verified: bool

@router.get("/translations/")
def list_translations():
    return get_all_translations()

@router.post("/translations/update/")
def update_translation(req: TranslationUpdateRequest):
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "UPDATE translations SET translated_text = ?, is_verified = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (req.translated_text, 1 if req.is_verified else 0, req.id)
            )
            conn.commit()
    return {"message": "Translation updated"}

@router.delete("/translations/{t_id}")
def delete_translation(t_id: int):
    delete_translation_db(t_id)
    return {"message": "Translation deleted"}

@router.post("/translations/clear-cache/")
def clear_trans_cache():
    with FileLock(LOCK_FILE, timeout=10):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM translations WHERE is_verified = 0")
            conn.commit()
    return {"message": "Unverified translations cleared"}

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from services.groq_service import rewrite_text, execute_admin_command
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

# Simple token generation for proof of concept
ADMIN_PASSWORD = "admin123"
SESSION_TOKEN = "admin_secret_token_42"

@router.post("/login")
def login(req: LoginRequest):
    if req.password == ADMIN_PASSWORD:
        return {"token": SESSION_TOKEN}
    raise HTTPException(status_code=401, detail="Invalid password")

@router.post("/command")
async def process_command(req: CommandRequest):
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
    
    return {"message": "Command executed successfully", "changes_applied": changes, "new_data": updated}

@router.post("/rewrite-bio")
async def rewrite_bio_route(req: RewriteRequest):
    new_text = await rewrite_text(req.text, req.instruction)
    return {"rewritten": new_text}
    
@router.post("/rewrite-about")
async def rewrite_about_route(req: RewriteRequest):
    new_text = await rewrite_text(req.text, req.instruction)
    return {"rewritten": new_text}
    
@router.get("/projects/all")
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

@router.post("/achievement-image")
async def upload_achievement_image(file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    file_path = os.path.join(UPLOAD_DIR, "award.jpg")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": "http://localhost:8000/uploads/award.jpg"}

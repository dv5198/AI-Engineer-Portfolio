from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import load_data
from services.github import fetch_github_projects

router = APIRouter()

class SummaryRequest(BaseModel):
    repo_name: str
    description: str

@router.get("/")
async def get_projects():
    data = load_data()
    github_handle = data.get("profile", {}).get("github", "")
    username = github_handle.split("/")[-1] if github_handle else "alexsharma"
    
    repos = await fetch_github_projects(username)
    if repos is None:
        raise HTTPException(status_code=503, detail="GitHub API Error")
        
    # Apply visibility filter stored in data
    visibility = data.get("project_visibility", {})
    
    formatted = []
    repos_list = repos if repos is not None else []
    for r in repos_list:
        name = r["name"]
        if visibility.get(name) is False:
            continue
            
        formatted.append({
            "name": name,
            "description": r.get("description") or "",
            "html_url": r.get("html_url"),
            "homepage": r.get("homepage"),
            "language": r.get("language"),
            "topics": r.get("topics", []),
            "summary": "" # Will be populated natively or fetched client side if needed
        })
        
    return formatted

    return formatted

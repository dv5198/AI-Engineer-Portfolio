from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sys
import os
import shutil

# Adjust path to import main's load_data / save_data
# Alternatively, I can move data logic here, but let's keep it simple
router = APIRouter()

@router.get("/")
def get_portfolio():
    from database import load_data
    return load_data()

from fastapi import BackgroundTasks

@router.post("/")
def update_portfolio(data: Dict[str, Any], background_tasks: BackgroundTasks):
    from database import save_data, load_data
    
    current_data = load_data()
    
    # Deep update dict
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
        
    updated = deep_update(current_data, data)
    save_data(updated)
    
    from routes.dynamic_sections import log_activity
    sections_updated = list(data.keys())
    log_activity(f"Manually updated config/profile", "Settings", data)
    
    from services.groq_service import auto_regenerate_summary_task
    background_tasks.add_task(auto_regenerate_summary_task)
    
    return {"status": "success", "data": updated}

@router.post("/photo")
async def upload_photo(file: UploadFile = File(...)):
    import os
    from database import save_data, load_data

    # Generate filename and path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(base_dir, "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Safe file name
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WEBP are allowed.")

    filename = f"profile_photo.{file_extension}"
    file_path = os.path.join(upload_dir, filename)

    # Save physical file
    with open(file_path, "wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)

    # Note: Using absolute URL to backend static endpoint
    # E.g. http://localhost:8001/uploads/profile_photo.jpg
    photo_url = f"http://localhost:8001/uploads/{filename}"

    # Save to data.json instantly
    current_data = load_data()
    if "profile" in current_data:
        current_data["profile"]["photo"] = photo_url
        save_data(current_data)

    return {"status": "success", "photo_url": photo_url}

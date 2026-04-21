import json
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx
from datetime import datetime
import hashlib
from dotenv import load_dotenv
import asyncio
import sys

# Fix for Playwright NotImplementedError in Windows Async loops
if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from routes.portfolio import router as portfolio_router
from routes.projects import router as projects_router
from routes.admin import router as admin_router
from routes.dynamic_sections import router as dynamic_sections_router
from routes.platform import router as platform_router
from routes.resume import router as resume_router
from fastapi.staticfiles import StaticFiles
from database import load_data, save_data

app = FastAPI(title="Divya Nirankari Portfolio API")

# Mount static files
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from database import load_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


@app.on_event("startup")
def startup_event():
    load_data()
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

app.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(dynamic_sections_router, prefix="/api/dynamic", tags=["dynamic"])
app.include_router(platform_router, prefix="/api/platform", tags=["platform"])
app.include_router(resume_router, prefix="/api/resume", tags=["resume"])
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Dynamic resume download is handled in routes/resume.py via resume_router

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

import json
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
from dotenv import load_dotenv

from routes.portfolio import router as portfolio_router
from routes.projects import router as projects_router
from routes.resume import router as resume_router
from routes.admin import router as admin_router
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI(title="Alex Sharma Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from database import load_data

UPLOAD_DIR = "uploads"
RESUME_FILE = os.path.join(UPLOAD_DIR, "resume.pdf")

@app.on_event("startup")
def startup_event():
    load_data()
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

app.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
app.include_router(resume_router, prefix="/api/resume", tags=["resume"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def read_root():
    return {"message": "Portfolio API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

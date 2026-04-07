# backend/routes/resume.py

import os
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from services.geo import get_visitor_ip, get_country_from_ip, country_to_region
from services.pdf_generator import generate_resume_by_region
from database import load_data
import json

router = APIRouter()

@router.get("/detect")
async def detect_region(request: Request):
    """Detects region info for the current visitor."""
    ip = get_visitor_ip(request)
    geo_data = await get_country_from_ip(ip)
    country_code = geo_data['code']
    country_name = geo_data['name']
    region_info = country_to_region(country_code)
    
    return {
        "detectedCountry": country_code,
        "detectedCountryName": country_name,
        "detectedRegion": region_info['region'],
        "includesPhoto": region_info['photo'],
        "label": region_info['label'],
        "filename": region_info['filename'],
        "isLocalhost": country_code == 'DEV'
    }

@router.get("/download")
async def download_auto(request: Request, background_tasks: BackgroundTasks):
    """Auto-detects region and serves the PDF."""
    ip = get_visitor_ip(request)
    geo_data = await get_country_from_ip(ip)
    country_code = geo_data['code']
    region_info = country_to_region(country_code)
    
    return await serve_pdf(region_info, request, background_tasks)

@router.get("/download/{region}")
async def download_manual(region: str, request: Request, background_tasks: BackgroundTasks):
    """Manual override for regional resume download."""
    # Find the region info from REGION_MAP in geo.py
    from services.geo import REGION_MAP, DEFAULT_REGION
    
    # Matching by 'region' key or specific country code if provided as parameter
    target = None
    for code, info in REGION_MAP.items():
        if info['region'] == region or code.lower() == region.lower():
            target = info
            break
            
    if not target:
        target = DEFAULT_REGION
        
    return await serve_pdf(target, request, background_tasks)

async def serve_pdf(region_info: dict, request: Request, background_tasks: BackgroundTasks):
    """Helper to generate and serve the PDF response."""
    data = load_data()
    
    # Get live projects from projects service if needed, 
    # but here we can just pass the projects from data or fetched elsewhere.
    # Priority: Professional Summary > Bio > Generic About Us
    profile = data.get('profile', {})
    dynamic_summary = profile.get('summary') or profile.get('bio')
    
    if not dynamic_summary:
        about_list = data.get('about', [])
        dynamic_summary = "\n".join(about_list) if about_list else ""
    
    projects = data.get('projects', [])
    
    # Filter projects like in Projects.jsx if possible, 
    # but here we'll just include visible ones.
    visible_projects = [p for p in projects if p.get('visible') != False]
    
    try:
        region_name = region_info.get('region', 'international')
        include_photo = region_info.get('photo', False)
        
        buffer = generate_resume_by_region(data, live_projects=visible_projects, region=region_name, include_photo=include_photo)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{data.get("profile", {}).get("name", "resume").lower().replace(" ", "_")}_resume.pdf"'
            }
        )
    except Exception as e:
        print(f"Resume Generation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate resume")

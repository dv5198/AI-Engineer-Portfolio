# backend/routes/resume.py

import os
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from services.geo import get_visitor_ip, get_country_from_ip, country_to_region
from services.pdf_playwright import generate_resume_playwright
from services.email_service import send_email_notification
from database import load_data, log_resume_download
from services.github import fetch_github_projects
from services.ntfy import send_hiring_alert
import json
import asyncio

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
    
    # 1. Fetch GitHub projects concurrently if username is available
    github_username = profile.get('github_username')
    github_projects = []
    if github_username:
        github_projects = await fetch_github_projects(github_username)
    
    # 2. Get manual projects from data.json
    manual_projects = data.get('projects', [])
    visible_manual = [p for p in manual_projects if p.get('visible') != False]
    
    # 3. Apply Visibility Filter & Deduplication for GitHub items
    visibility_map = data.get('project_visibility', {})
    hidden_list = data.get('hiddenProjects', [])
    
    final_github_projects = []
    manual_names = {p.get('name').lower().strip() for p in visible_manual if p.get('name')}
    
    for gh_p in github_projects:
        name = gh_p.get('name')
        # Filter 1: Admin Toggle (visibility map or hidden list)
        if visibility_map.get(name) is False or name in hidden_list:
            continue
            
        # Filter 2: Deduplicate against manual items (Manual description is preferred)
        if name.lower().strip() in manual_names:
            continue
            
        final_github_projects.append(gh_p)
    
    # 4. Final Selection: All manual + Top 3 live GitHub pulses
    # Sort GitHub by stars then date
    final_github_projects.sort(key=lambda x: (x.get('stars', 0), x.get('updated_at', '')), reverse=True)
    
    merged_projects = visible_manual + final_github_projects[:3]
    
    try:
        region_name = region_info.get('region', 'international')
        include_photo = region_info.get('photo', False)
        
        # Hiring Radar: Process analytics and notifications in background
        client_ip = get_visitor_ip(request)
        
        async def background_radar_process():
            # Get full geo data for logging
            geo_data = await get_country_from_ip(client_ip)
            country_name = geo_data.get('name', 'Unknown')
            country_code = geo_data.get('code', '??')
            
            # 1. Log to Database
            log_resume_download(
                ip=client_ip,
                country=country_name,
                region=region_name,
                format_label=region_info.get('label', 'Standard')
            )
            
            # 2. Push Notification via NTFY
            await send_hiring_alert(
                location=country_name,
                country=country_code,
                region=region_name.capitalize()
            )
            
            # 3. Optional Legacy Email
            email_subject = f"🎯 Resume Hit: {country_name} ({region_name})"
            email_body = f"Resume downloaded in {country_name}.\nIP: {client_ip}\nRegion: {region_name}"
            await send_email_notification(email_subject, email_body)

        buffer = await generate_resume_playwright(data, live_projects=merged_projects, region=region_name, include_photo=include_photo)
        disp = "attachment" if request.query_params.get("download") == "true" else "inline"
        
        if disp == "attachment":
            background_tasks.add_task(background_radar_process)
            
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'{disp}; filename="{data.get("profile", {}).get("name", "resume").lower().replace(" ", "_")}_resume.pdf"'
            },
            background=background_tasks
        )
    except Exception as e:
        print(f"Resume Generation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate resume")

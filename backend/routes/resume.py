# backend/routes/resume.py

import os
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from services.geo import get_visitor_ip, get_country_from_ip, country_to_region
from services.pdf_playwright import generate_resume_playwright
from services.email_service import send_email_notification
from database import load_data, log_resume_download
from services.github import fetch_github_projects
from services.pregenerator import get_prebuilt_pdf
import json
import asyncio

from services.geo_rules import calculate_ats_score

router = APIRouter()

@router.get("/ats-score/{region}")
async def get_ats_score_route(region: str):
    data = load_data()
    result = calculate_ats_score(data, region)
    return result

# Country Detection
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
async def download_auto(request: Request, background_tasks: BackgroundTasks, lang: str = "en"):
    """Auto-detects region and serves the PDF.
    
    FAST PATH: Immediately serve the pre-built PDF using a synchronous IP check
    (private/local IPs resolve instantly). Geolocation API call is deferred to
    background for analytics only, so the user never waits for it.
    """
    from services.pregenerator import get_prebuilt_pdf
    import urllib.parse
    from io import BytesIO

    client_ip = get_visitor_ip(request)

    # ── Synchronous fast check: is this a local/private IP? ──────────────
    import ipaddress
    try:
        is_local = client_ip in ('localhost', '::1', '127.0.0.1') or \
                   ipaddress.ip_address(client_ip).is_private
    except ValueError:
        is_local = True

    # ── Determine region without waiting for geo API ───────────────────────
    from services.geo import IP_CACHE
    from datetime import datetime
    if is_local:
        region_info = country_to_region('IN')
    elif client_ip in IP_CACHE and IP_CACHE[client_ip]['expires'] > datetime.now():
        region_info = country_to_region(IP_CACHE[client_ip]['data']['code'])
    else:
        region_info = country_to_region('IN')  # fallback; bg task logs the real country

    # ── Try pre-built PDF immediately (no generation needed) ───────────
    region_name = region_info.get('region', 'international')
    pdf_bytes   = get_prebuilt_pdf(region_name, lang)

    if pdf_bytes:
        data = load_data()
        base_name       = data.get('profile', {}).get('name', 'resume').lower().replace(' ', '_')
        region_filename = region_info.get('filename', f'{base_name}_resume.pdf')
        if '{name}' in region_filename:
            region_filename = region_filename.replace('{name}', base_name)
        encoded_filename = urllib.parse.quote(region_filename)
        disp = "attachment" if request.query_params.get("download") == "true" else "inline"

        # Geo lookup + analytics deferred entirely to background
        async def bg_geo_and_log():
            geo_data     = await get_country_from_ip(client_ip)
            country_name = geo_data.get('name', 'Unknown')
            country_code = geo_data.get('code', '??')
            actual_region = country_to_region(country_code)
            log_resume_download(
                ip=client_ip, country=country_name,
                region=actual_region.get('region', region_name),
                format_label=actual_region.get('label', 'Standard')
            )
        background_tasks.add_task(bg_geo_and_log)

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"{disp}; filename*=UTF-8''{encoded_filename}",
                "Cache-Control": "public, max-age=3600",
            },
            background=background_tasks,
        )

    # ── Fallback: no pre-built PDF, full geo + live generation ─────────
    ip = get_visitor_ip(request)
    geo_data    = await get_country_from_ip(ip)
    country_code = geo_data['code']
    region_info  = country_to_region(country_code)
    return await serve_pdf(region_info, request, background_tasks, lang=lang)

@router.get("/download/{region}")
async def download_manual(region: str, request: Request, background_tasks: BackgroundTasks, lang: str = "en", cover: bool = None):
    """Manual override for regional resume download."""
    from services.geo import REGION_MAP, DEFAULT_REGION
    from services.geo_rules import GEO_RULES
    
    target = None
    region_lower = region.lower()
    
    # 1. Match directly with GEO_RULES keys first
    if region_lower in GEO_RULES:
        rule = GEO_RULES[region_lower]
        for code, info in REGION_MAP.items():
            if info['region'] == region_lower:
                target = info.copy()
                break
        if not target:
            label_map = {
                "usa": "USA (ATS)",
                "uk": "UK (ATS)",
                "uae": "UAE",
                "india": "India (ATS)",
                "germany": "Germany (Lebenslauf)",
                "china": "China (简历)",
                "korea": "South Korea (이력서)",
                "japan": "Japan (履歴書)",
                "middleeast": "Middle East",
                "international": "International (ATS)"
            }
            filename_map = {
                "usa": "divya_nirankari_resume_usa.pdf",
                "uk": "divya_nirankari_resume_uk.pdf",
                "uae": "divya_nirankari_resume_uae.pdf",
                "india": "divya_nirankari_resume_india.pdf",
                "germany": "divya_nirankari_lebenslauf.pdf",
                "china": "divya_nirankari_简历.pdf",
                "korea": "divya_nirankari_이력서.pdf",
                "japan": "divya_nirankari_履歴書.pdf",
                "middleeast": "divya_nirankari_resume_me.pdf",
                "international": "divya_nirankari_resume.pdf"
            }
            target = {
                "region": region_lower,
                "photo": rule.get("show_photo", False),
                "label": label_map.get(region_lower, region_lower.upper()),
                "filename": filename_map.get(region_lower, f"divya_nirankari_resume_{region_lower}.pdf")
            }
            
    # 2. Match by region key in REGION_MAP or country code
    if not target:
        for code, info in REGION_MAP.items():
            if info['region'] == region or code.lower() == region.lower():
                target = info
                break
            
    if not target:
        target = DEFAULT_REGION
        
    return await serve_pdf(target, request, background_tasks, lang=lang, include_cover=cover)

@router.get("/preview")
async def preview_auto(request: Request, background_tasks: BackgroundTasks, lang: str = "en"):
    """Auto-detects region and serves the HTML preview."""
    ip = get_visitor_ip(request)
    geo_data = await get_country_from_ip(ip)
    country_code = geo_data['code']
    region_info = country_to_region(country_code)
    
    return await serve_pdf(region_info, request, background_tasks, return_html=True, lang=lang)

@router.get("/preview/{region}")
async def preview_manual(region: str, request: Request, background_tasks: BackgroundTasks, lang: str = "en", cover: bool = False):
    """Manual override for regional HTML resume preview."""
    from services.geo import REGION_MAP, DEFAULT_REGION
    from services.geo_rules import GEO_RULES
    
    target = None
    region_lower = region.lower()
    
    # 1. Match directly with GEO_RULES keys first
    if region_lower in GEO_RULES:
        rule = GEO_RULES[region_lower]
        for code, info in REGION_MAP.items():
            if info['region'] == region_lower:
                target = info.copy()
                break
        if not target:
            label_map = {
                "usa": "USA (ATS)",
                "uk": "UK (ATS)",
                "uae": "UAE",
                "india": "India (ATS)",
                "germany": "Germany (Lebenslauf)",
                "china": "China (简历)",
                "korea": "South Korea (이력서)",
                "japan": "Japan (履歴書)",
                "middleeast": "Middle East",
                "international": "International (ATS)"
            }
            filename_map = {
                "usa": "divya_nirankari_resume_usa.pdf",
                "uk": "divya_nirankari_resume_uk.pdf",
                "uae": "divya_nirankari_resume_uae.pdf",
                "india": "divya_nirankari_resume_india.pdf",
                "germany": "divya_nirankari_lebenslauf.pdf",
                "china": "divya_nirankari_简历.pdf",
                "korea": "divya_nirankari_이력서.pdf",
                "japan": "divya_nirankari_履歴書.pdf",
                "middleeast": "divya_nirankari_resume_me.pdf",
                "international": "divya_nirankari_resume.pdf"
            }
            target = {
                "region": region_lower,
                "photo": rule.get("show_photo", False),
                "label": label_map.get(region_lower, region_lower.upper()),
                "filename": filename_map.get(region_lower, f"divya_nirankari_resume_{region_lower}.pdf")
            }
            
    # 2. Match by region key in REGION_MAP or country code
    if not target:
        for code, info in REGION_MAP.items():
            if info['region'] == region or code.lower() == region.lower():
                target = info
                break
            
    if not target:
        target = DEFAULT_REGION
        
    return await serve_pdf(target, request, background_tasks, return_html=True, lang=lang, include_cover=cover)

async def serve_pdf(region_info: dict, request: Request, background_tasks: BackgroundTasks, return_html: bool = False, lang: str = "en", include_cover: bool = None):
    """Helper to generate and serve the PDF response."""
    import urllib.parse
    from io import BytesIO
    from services.cache_service import get_cached_pdf, set_cached_pdf

    data    = load_data()
    profile = data.get("profile", {})

    # ── Filename ──────────────────────────────────────────────────────────────
    base_name       = profile.get("name", "resume").lower().replace(" ", "_")
    region_filename = region_info.get("filename", f"{base_name}_resume.pdf")
    if "{name}" in region_filename:
        region_filename = region_filename.replace("{name}", base_name)
    encoded_filename = urllib.parse.quote(region_filename)

    # ── Region ────────────────────────────────────────────────────────────────
    region_name   = region_info.get("region", "international")
    include_photo = region_info.get("photo", False)

    # ── Cover letter flag ─────────────────────────────────────────────────────
    if include_cover is None:
        from services.geo_rules import ATS_COUNTRIES
        q_cover = request.query_params.get("cover")
        if q_cover is not None:
            include_cover = q_cover.lower() == "true"
        else:
            include_cover = False if (region_name.lower() in ATS_COUNTRIES and region_name.lower() != 'germany') else True

    # ── Background analytics ──────────────────────────────────────────────────
    client_ip = get_visitor_ip(request)

    async def background_radar_process():
        geo_data     = await get_country_from_ip(client_ip)
        country_name = geo_data.get("name", "Unknown")
        country_code = geo_data.get("code", "??")
        log_resume_download(ip=client_ip, country=country_name, region=region_name, format_label=region_info.get("label", "Standard"))
        # Email notification removed per user request (slowing down process)
        # await send_email_notification(...)

    disp         = "attachment" if request.query_params.get("download") == "true" else "inline"
    use_prebuilt = request.query_params.get("v") is None  # ?v=... forces live generation

    try:
        # ── HTML preview: always live-generate ───────────────────────────────
        if return_html:
            merged_projects = await _build_merged_projects(data)
            html_content = await generate_resume_playwright(
                data, live_projects=merged_projects, region=region_name,
                include_photo=include_photo, return_html=True, lang=lang,
                include_cover=include_cover,
            )
            return HTMLResponse(content=html_content)

        # ── Fast path: serve pre-built PDF from disk ─────────────────────────
        if use_prebuilt:
            pdf_bytes = get_prebuilt_pdf(region_name, lang)
            if pdf_bytes:
                if disp == "attachment":
                    background_tasks.add_task(background_radar_process)
                return StreamingResponse(
                    BytesIO(pdf_bytes),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"{disp}; filename*=UTF-8''{encoded_filename}"},
                    background=background_tasks,
                )

        # ── Fallback: live generation (cold start or forced refresh) ─────────
        merged_projects = await _build_merged_projects(data)
        cache_key  = f"{region_name}_{lang}_{include_cover}"
        cached_pdf = get_cached_pdf(cache_key) if use_prebuilt else None
        if cached_pdf:
            buffer = BytesIO(cached_pdf)
        else:
            buffer = await generate_resume_playwright(
                data, live_projects=merged_projects, region=region_name,
                include_photo=include_photo, lang=lang, include_cover=include_cover,
            )
            set_cached_pdf(cache_key, buffer.getvalue())

        if disp == "attachment":
            background_tasks.add_task(background_radar_process)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"{disp}; filename*=UTF-8''{encoded_filename}"},
            background=background_tasks,
        )

    except Exception as e:
        print(f"Resume Generation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate resume")


async def _build_merged_projects(data: dict) -> list:
    """Fetches and merges GitHub + manual projects — shared by serve_pdf and pregenerator."""
    profile         = data.get("profile", {})
    github_username = profile.get("github_username")
    github_projects = []
    if github_username:
        github_projects = await fetch_github_projects(github_username)

    manual_projects = data.get("projects", [])
    visible_manual  = [p for p in manual_projects if p.get("visible") is not False]
    visibility_map  = data.get("project_visibility", {})
    hidden_list     = data.get("hiddenProjects", [])
    manual_names    = {p.get("name", "").lower().strip() for p in visible_manual}

    final_github = [
        p for p in github_projects
        if visibility_map.get(p.get("name")) is not False
        and p.get("name") not in hidden_list
        and p.get("name", "").lower().strip() not in manual_names
    ]
    final_github.sort(key=lambda x: (x.get("stars", 0), x.get("updated_at", "")), reverse=True)
    return visible_manual + final_github[:3]


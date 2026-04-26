import os
import asyncio
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
import nest_asyncio

# Apply nest_asyncio to allow asyncio to run inside FastAPI's event loop
nest_asyncio.apply()

# Global Playwright concurrency limit
pdf_semaphore = asyncio.Semaphore(3)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'resume_templates')

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), extensions=['jinja2.ext.do'])

# Helper to normalize file paths for CSS
def get_file_uri(rel_path):
    return "file:///" + os.path.join(TEMPLATES_DIR, rel_path).replace("\\", "/")

def get_categorized_projects(projects):
    ai_research = []
    software = []
    
    for p in projects:
        cat = p.get('category', '').lower()
        if 'ai' in cat or 'ml' in cat or 'research' in cat:
            ai_research.append(p)
        else:
            software.append(p)
            
    # Default to all in software if completely empty categorization
    if not ai_research and not software:
        software = projects
        
    return {
        'ai_research': ai_research,
        'software_other': software
    }

def _generate_pdf_sync(html_content: str, pdf_format: str, pdf_margin: dict) -> bytes:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        
        pdf_bytes = page.pdf(
            format=pdf_format,
            print_background=True,
            margin=pdf_margin
        )
        browser.close()
        return pdf_bytes

def ensure_bullets(text_or_list, min_bullets: int = 3) -> list:
    """
    Normalizes any text/list input into a clean list of bullet strings.
    """
    if not text_or_list:
        return []

    # Already a list
    if isinstance(text_or_list, list):
        cleaned = [b.strip().rstrip('.').strip() for b in text_or_list if b and len(b.strip()) > 14]
        return cleaned

    # It's a string — split into sentences
    text = str(text_or_list).strip()
    if not text:
        return []

    # Try newline split first
    if '\n' in text:
        parts = [p.strip().rstrip('.').strip() for p in text.split('\n')]
    else:
        # Split on '. ' to get sentences
        parts = [p.strip().rstrip('.').strip() for p in text.split('. ')]

    # Filter out fragments that are too short to be meaningful
    cleaned = [p for p in parts if p and len(p) > 14]
    return cleaned

async def generate_project_bullets(project: dict, context_hint: str = "") -> list:
    """
    Uses Grok to generate 3–4 resume bullet points for a project.
    Called ONLY when project has no bullets and description is a single sentence.
    """
    import os, httpx, json
    from services.cache_service import get_cached_project_bullets, set_cached_project_bullets

    name = project.get('name', '')
    
    # Check cache first — avoid redundant Grok calls
    cached = get_cached_project_bullets(name)
    if cached:
        return cached

    description = project.get('description', '')
    tech = project.get('techStack', project.get('tech', ''))

    # Only generate if description is a single short paragraph
    existing = ensure_bullets(description)
    if len(existing) >= 3:
        return existing  # Already enough — don't call API

    prompt = f"""You are writing resume bullet points for a software engineering portfolio.

Project: {name}
Description: {description}
Tech stack: {tech}
{f"Context: {context_hint}" if context_hint else ""}

Write exactly 3 concise resume bullet points for this project.
Rules:
- Each bullet starts with a strong action verb (Built, Developed, Implemented, Designed, Optimized, etc.)
- Each bullet is factual — based only on the information provided above
- Each bullet is max 120 characters
- No invented metrics or statistics unless they appear in the description above
- Return ONLY a JSON array of 3 strings, nothing else
- Example format: ["Built X using Y.", "Implemented Z to solve W.", "Achieved Q by doing R."]

Return only the JSON array:"""

    try:
        api_key = os.getenv("GROK_API_KEY", "")
        if not api_key:
            return existing or [description] if description else []

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-3",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()

            # Strip markdown fences if present
            content = content.replace("```json", "").replace("```", "").strip()

            bullets = json.loads(content)
            if isinstance(bullets, list) and len(bullets) >= 1:
                # Validate each bullet is a non-empty string
                valid = [b.strip() for b in bullets if isinstance(b, str) and len(b.strip()) > 10]
                if valid:
                    set_cached_project_bullets(name, valid)
                    return valid

    except Exception as e:
        print(f"[generate_project_bullets] Grok call failed for '{name}': {e}")

    # Fallback — return whatever we had
    return existing or ([description] if description else [])

async def enrich_projects(projects: list) -> list:
    """
    Enriches each project with a proper bullets list before passing to template.
    """
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent Grok calls

    async def enrich_one(project: dict) -> dict:
        p = project.copy()
        async with semaphore:
            existing_bullets = ensure_bullets(p.get('bullets', []))
            
            if len(existing_bullets) >= 3:
                p['bullets'] = existing_bullets
                return p

            # Try splitting description first (no API cost)
            desc_bullets = ensure_bullets(p.get('summary') or p.get('description', ''))
            
            if len(desc_bullets) >= 3:
                p['bullets'] = desc_bullets
                return p

            # Need Grok — description is too short to split meaningfully
            generated = await generate_project_bullets(p)
            p['bullets'] = generated
            return p

    enriched = await asyncio.gather(*[enrich_one(p) for p in projects], return_exceptions=False)
    return list(enriched)

def enrich_experience(experience: list) -> list:
    """
    Normalizes experience bullets to always be a clean list.
    """
    result = []
    for exp in experience:
        e = exp.copy()
        
        bullets = e.get('bullets', [])
        normalized = ensure_bullets(bullets)
        
        if not normalized:
            # Try description field as fallback
            normalized = ensure_bullets(e.get('description', ''))
        
        e['bullets'] = normalized
        result.append(e)
    return result

def parse_human_date(date_str: str):
    """Parses 'Jan 2023', '2023', 'Present' into year, month, day."""
    from datetime import datetime
    if not date_str or date_str.lower() in ["present", "current"]:
        now = datetime.today()
        return now.year, now.month, now.day
        
    parts = date_str.strip().split()
    year = 2000
    month = 1
    
    if len(parts) == 2:
        month_str, year_str = parts
        try:
            year = int(year_str)
            month = datetime.strptime(month_str[:3], "%b").month
        except ValueError:
            pass
    elif len(parts) == 1:
        try:
            year = int(parts[0])
        except ValueError:
            pass
            
    return year, month, 1

def build_japan_context(data: dict) -> dict:
    """Builds context for Japanese resume template"""
    import copy
    context = copy.deepcopy(data)
    
    if "profile" in context and "personal" in context["profile"]:
        p = context["profile"]
        p["name"] = p.get("name", "")
        p["name_furigana"] = p["personal"].get("name_furigana", "")
        p["email"] = p.get("email", "")
        p["phone"] = p.get("phone", "")
        p["address"] = p.get("location", "")
        p["address_furigana"] = p["personal"].get("address_furigana", "")
        
        gender = p["personal"].get("gender", "").lower()
        if gender.startswith("m"):
            p["gender_ja"] = "男"
        elif gender.startswith("f"):
            p["gender_ja"] = "女"
        else:
            p["gender_ja"] = ""
            
    for edu in context.get("education", []):
        year_str = edu.get("year", "")
        if "–" in year_str:
            parts = year_str.split("–")
        elif "-" in year_str:
            parts = year_str.split("-")
        else:
            parts = [year_str, ""]
            
        try:
            edu["start_year"] = int(parts[0].strip()) if parts[0].strip() else ""
            edu["start_month"] = 4
            edu["end_year"] = int(parts[1].strip()) if parts[1].strip() else ""
            edu["end_month"] = 3
        except ValueError:
            pass
            
    for exp in context.get("experience", []):
        sy, sm, _ = parse_human_date(exp.get("startDate", ""))
        ey, em, _ = parse_human_date(exp.get("endDate", ""))
        exp["start_year"] = sy
        exp["start_month"] = sm
        exp["end_year"] = ey
        exp["end_month"] = em
        
        if "bullets" not in exp or not exp["bullets"]:
            exp["bullets"] = [exp.get("description", "")]
            
    return context

def _generate_japan_pdfs_sync(rirekisho_html: str, shokumu_html: str, pdf_margin: dict) -> bytes:
    from pypdf import PdfWriter
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 1. Rirekisho
        page.set_content(rirekisho_html, wait_until="networkidle")
        rirekisho_bytes = page.pdf(format="A4", print_background=True, margin=pdf_margin)
        
        # 2. Shokumu-keirekisho
        page.set_content(shokumu_html, wait_until="networkidle")
        shokumu_bytes = page.pdf(format="A4", print_background=True, margin=pdf_margin)
        
        browser.close()
        
        # Merge with pypdf
        writer = PdfWriter()
        writer.append(BytesIO(rirekisho_bytes))
        writer.append(BytesIO(shokumu_bytes))
        
        out_buffer = BytesIO()
        writer.write(out_buffer)
        return out_buffer.getvalue()

async def generate_resume_playwright(data: dict, live_projects: list, region: str, include_photo: bool) -> BytesIO:
    """Generate Resume PDF using Jinja2 and Playwright."""
    
    # 1. Prepare View Data
    profile = data.get('profile', {}).copy()   # single copy, keep it
    personal = profile.get('personal', {})
    
    # Calculate age from personal.dob (not profile.dateOfBirth)
    from datetime import datetime
    today = datetime.today()
    dob_str = personal.get('dob') or profile.get('dateOfBirth', '')
    if dob_str:
        try:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    dob = datetime.strptime(dob_str, fmt)
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    profile['age'] = age
                    personal['age'] = age
                    break
                except ValueError:
                    continue
        except Exception:
            pass
            
    # Calculate Japanese Era (Reiwa started May 1, 2019)
    # Simple calculation for current year
    reiwa_year = today.year - 2018
    
    enriched_experience = enrich_experience(data.get('experience', []))
    enriched_projects = await enrich_projects(live_projects)

    view_data = {
        'profile': profile,
        'personal': personal,
        'region': region,
        'about': data.get('about', []),
        'education': data.get('education', []),
        'experience': enriched_experience,
        'research': data.get('research', []),
        'achievements': data.get('achievements', []),
        'certifications': data.get('certifications', []),
        'connections': data.get('connections', []),
        'skillCategories': data.get('skillCategories', []),
        'categorized_projects': get_categorized_projects(enriched_projects),
        'base_css': get_file_uri('css/base.css'),
        'generated_era_year': str(reiwa_year),
        'generated_month': str(today.month),
        'generated_day': str(today.day),
        'data': data
    }

    # 2. Select Template based on region using REGION_CONFIG
    import base64
    import mimetypes
    
    def get_photo_base64(photo_path):
        try:
            with open(photo_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            mime_type, _ = mimetypes.guess_type(photo_path)
            if not mime_type:
                mime_type = "image/jpeg"
            return f"data:{mime_type};base64,{data}"
        except:
            return photo_path

    REGION_CONFIG = {
        'japan': {
            'template': 'japan.html',
            'css': 'css/japan.css',
            'format': 'A4',
            'margin': {"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
            'allowed_personal': ['dob', 'gender', 'marital_status', 'name_furigana', 'nationality_ja', 'address_furigana', 'commute_time', 'dependents_count', 'has_spouse', 'spouse_dependency', 'self_pr_ja', 'self_pr_ja_detailed', 'career_summary_ja', 'desired_conditions_ja'],
            'process_func': 'process_japan'
        },
        'china': {
            'template': 'china.html',
            'css': 'css/china.css',
            'format': 'A4',
            'margin': {"top": "15mm", "right": "15mm", "bottom": "15mm", "left": "15mm"},
            'allowed_personal': ['dob', 'gender', 'political_status', 'wechat_id'],
            'process_func': 'process_photo'
        },
        'germany': {
            'template': 'europe.html',
            'css': 'css/europe.css',
            'format': 'A4',
            'margin': {"top": "18mm", "right": "15mm", "bottom": "18mm", "left": "15mm"},
            'allowed_personal': ['dob', 'nationality', 'visa_status'],
            'process_func': 'process_photo'
        },
        'middleeast': {
            'template': 'middleeast.html',
            'css': 'css/middleeast.css',
            'format': 'A4',
            'margin': {"top": "15mm", "right": "15mm", "bottom": "15mm", "left": "15mm"},
            'allowed_personal': ['dob', 'nationality', 'marital_status', 'gender'],
            'process_func': 'process_photo'
        },
        'academic': {
            'template': 'academic.html',
            'css': 'css/academic.css',
            'format': 'Letter',
            'margin': {"top": "25mm", "right": "25mm", "bottom": "25mm", "left": "25mm"},
            'allowed_personal': [],
            'process_func': None
        },
        'korea': {
            'template': 'korea.html',
            'css': 'css/korea.css',
            'format': 'A4',
            'margin': {"top": "18mm", "right": "15mm", "bottom": "18mm", "left": "15mm"},
            'allowed_personal': ['dob', 'gender', 'military_service'],
            'process_func': 'process_korea'
        },
        'detailed': {
            'template': 'template_b.html',
            'css': 'css/detailed.css',
            'format': 'A4',
            'margin': {"top": "18mm", "right": "15mm", "bottom": "18mm", "left": "15mm"},
            'allowed_personal': [],
            'process_func': 'process_photo'
        },
        'international': {
            'template': 'international.html',
            'css': 'css/ats.css',
            'format': 'Letter',
            'margin': {"top": "25mm", "right": "25mm", "bottom": "25mm", "left": "25mm"},
            'allowed_personal': [],
            'process_func': None
        }
    }

    target_region = region
    if target_region not in REGION_CONFIG:
        target_region = 'detailed' if include_photo else 'international'

    config = REGION_CONFIG[target_region]
    template_name = config['template']
    view_data['specific_css'] = get_file_uri(config['css'])
    pdf_format = config['format']
    pdf_margin = config['margin']

    # Strict Personal Data filtering
    raw_personal = profile.get('personal', {})
    filtered_personal = {k: raw_personal.get(k, '') for k in config['allowed_personal']}
    view_data['personal'] = filtered_personal

    def process_photo(vd):
        photo_rel = vd['profile'].get('photo', '')
        if photo_rel and not photo_rel.startswith('http'):
            photo_full = os.path.join(BASE_DIR, photo_rel.replace('/', os.sep))
            vd['profile']['photo'] = get_photo_base64(photo_full)

    def to_japanese_era(year, month, day):
        dt = datetime(year, month, day)
        if dt >= datetime(2019, 5, 1):
            era_year = dt.year - 2018
            return f"令和{era_year}年" if era_year > 1 else "令和元年"
        elif dt >= datetime(1989, 1, 8):
            era_year = dt.year - 1988
            return f"平成{era_year}年" if era_year > 1 else "平成元年"
        elif dt >= datetime(1926, 12, 25):
            era_year = dt.year - 1925
            return f"昭和{era_year}年" if era_year > 1 else "昭和元年"
        return f"{year}年"

    def process_japan(vd):
        process_photo(vd)
        dob_str = vd['profile'].get('dateOfBirth') or raw_personal.get('dob')
        if dob_str:
            try:
                if '-' in dob_str:
                    parts = dob_str.split('-')
                    if len(parts[0]) == 4:
                        dt = datetime.strptime(dob_str, "%Y-%m-%d")
                    else:
                        dt = datetime.strptime(dob_str, "%d-%m-%Y")
                else:
                    dt = datetime.strptime(dob_str, "%d/%m/%Y")
                
                vd['personal']['japanese_dob_era'] = to_japanese_era(dt.year, dt.month, dt.day) + f" {dt.month}月 {dt.day}日生"
            except Exception:
                pass

    def process_korea(vd):
        process_photo(vd)
        full_time = []
        part_time = []
        for exp in vd['experience']:
            etype = exp.get('employment_type', 'Full-time').lower()
            if 'part' in etype or '알바' in etype:
                part_time.append(exp)
            else:
                full_time.append(exp)
        vd['experience_full'] = full_time
        vd['experience_part'] = part_time

    if config['process_func'] == 'process_photo':
        process_photo(view_data)
    elif config['process_func'] == 'process_japan':
        process_japan(view_data)
    elif config['process_func'] == 'process_korea':
        process_korea(view_data)

    # 3. Render HTML
    if target_region == 'japan':
        japan_context = build_japan_context(view_data)
        
        template_rirekisho = env.get_template('template_japan_rirekisho.html')
        html_rirekisho = template_rirekisho.render(**japan_context)
        
        template_shokumu = env.get_template('template_japan_shokumu.html')
        html_shokumu = template_shokumu.render(**japan_context)
        
        try:
            async with pdf_semaphore:
                pdf_bytes = await asyncio.wait_for(
                    asyncio.to_thread(_generate_japan_pdfs_sync, html_rirekisho, html_shokumu, pdf_margin),
                    timeout=60.0
                )
        except asyncio.TimeoutError:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Resume generation timed out.")
            
        buffer = BytesIO(pdf_bytes)
        return buffer
        
    template = env.get_template(template_name)
    html_content = template.render(**view_data)

    # 4. Generate PDF asynchronously via a separate thread to bypass Windows event loop issues
    try:
        async with pdf_semaphore:
            pdf_bytes = await asyncio.wait_for(
                asyncio.to_thread(_generate_pdf_sync, html_content, pdf_format, pdf_margin),
                timeout=60.0
            )
    except asyncio.TimeoutError:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Resume generation timed out.")
    except Exception as e:
        raise
    
    buffer = BytesIO(pdf_bytes)
    return buffer


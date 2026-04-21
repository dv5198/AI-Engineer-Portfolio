import os
import asyncio
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
import nest_asyncio

# Apply nest_asyncio to allow asyncio to run inside FastAPI's event loop
nest_asyncio.apply()

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

async def generate_resume_playwright(data: dict, live_projects: list, region: str, include_photo: bool) -> BytesIO:
    """Generate Resume PDF using Jinja2 and Playwright."""
    
    # 1. Prepare View Data
    profile = data.get('profile', {}).copy()
    
    # Calculate Age if DOB is available
    from datetime import datetime
    dob_str = profile.get('dateOfBirth')
    if dob_str:
        try:
            dob = datetime.strptime(dob_str, "%d/%m/%Y")
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            profile['age'] = age
        except:
            pass

    view_data = {
        'profile': profile,
        'region': region,
        'about': data.get('about', []),
        'experience': data.get('experience', []),
        'research': data.get('research', []),
        'achievements': data.get('achievements', []),
        'certifications': data.get('certifications', []),
        'skillCategories': data.get('skillCategories', []),
        'categorized_projects': get_categorized_projects(live_projects),
        'base_css': get_file_uri('css/base.css')
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
            'allowed_personal': ['dob', 'gender', 'marital_status'],
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
        'europe': {
            'template': 'europe.html',
            'css': 'css/europe.css',
            'format': 'A4',
            'margin': {"top": "18mm", "right": "15mm", "bottom": "18mm", "left": "15mm"},
            'allowed_personal': ['dob', 'nationality', 'visa_status'],
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
    template = env.get_template(template_name)
    html_content = template.render(**view_data)

    # 4. Generate PDF asynchronously via a separate thread to bypass Windows event loop issues
    pdf_bytes = await asyncio.to_thread(_generate_pdf_sync, html_content, pdf_format, pdf_margin)
    
    buffer = BytesIO(pdf_bytes)
    return buffer


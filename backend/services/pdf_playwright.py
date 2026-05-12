import os
import asyncio
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

# Global Playwright concurrency limit
pdf_semaphore = asyncio.Semaphore(3)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'resume_templates')

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), extensions=['jinja2.ext.do'])

from services.geo_rules import get_geo_rule, ATS_COUNTRIES
from services.translations import get_labels, translate_text, translate_batch


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
    Uses Groq (Llama-3) to generate 3–4 resume bullet points for a project.
    Called ONLY when project has no bullets and description is a single sentence.
    """
    import os, json
    from services.geo_rules import get_geo_rule
    from services.translations import get_labels, translate_text
    from services.cache_service import get_cached_project_bullets, set_cached_project_bullets

    name = project.get('name', '')
    
    # Check cache first — avoid redundant AI calls
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
        from services.groq_service import call_groq_json
        
        system_prompt = "You are a professional resume writer. Return ONLY a JSON object with a key 'bullets' containing an array of 3 concise, action-oriented resume bullet points."
        user_prompt = prompt
        
        res = await call_groq_json(system_prompt, user_prompt)
        bullets = res.get("bullets", [])
        
        if isinstance(bullets, list) and len(bullets) >= 1:
            # Validate each bullet is a non-empty string
            valid = [b.strip() for b in bullets if isinstance(b, str) and len(b.strip()) > 10]
            if valid:
                set_cached_project_bullets(name, valid)
                return valid

    except Exception as e:
        print(f"[generate_project_bullets] Groq call failed for '{name}': {e}")

    # Fallback — return whatever we had
    return existing or ([description] if description else [])

async def enrich_projects(projects: list) -> list:
    """
    Enriches each project with a proper bullets list before passing to template.
    """
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent Grok calls

    async def enrich_one(project: dict) -> dict:
        p = project.copy()
        
        # Priority for image:
        if p.get('image_override'):  # Admin overrode GitHub image
            p['image'] = p['image_override']
            p['has_image'] = True
        elif p.get('image'):
            p['has_image'] = True
            
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
        
        phone = p.get("phone", "")
        if "/" in phone:
            phone = phone.split("/")[0].strip()
        p["phone"] = phone
        
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
            start_y = int(parts[0].strip()) if parts[0].strip() else 2000
            edu["start_year"] = start_y
            edu["start_month"] = 4
            edu["end_year"] = int(parts[1].strip()) if parts[1].strip() else start_y + 4
            edu["end_month"] = 3
            edu["start"] = (start_y, 4)  # Add start attribute for sorting
        except ValueError:
            edu["start"] = (2000, 4)
            pass
            
        if "university" in edu and "institution" not in edu:
            edu["institution"] = edu["university"]
            
    for exp in context.get("experience", []):
        start_str = exp.get("startDate", "")
        end_str = exp.get("endDate", "")
        
        if not start_str and "duration" in exp:
            dur = exp["duration"]
            if " - " in dur:
                start_str, end_str = dur.split(" - ", 1)
            elif "-" in dur:
                start_str, end_str = dur.split("-", 1)
            else:
                start_str = dur
                end_str = ""
                
        sy, sm, _ = parse_human_date(start_str)
        ey, em, _ = parse_human_date(end_str)
        exp["start_year"] = sy
        exp["start_month"] = sm
        exp["end_year"] = ey
        exp["end_month"] = em
        exp["start"] = (sy, sm)  # Add start attribute for sorting
        
        # Determine if the job is current
        is_current_str = end_str.strip().lower()
        exp["is_current"] = is_current_str in ["present", "current", "now", ""]
        
        if "bullets" not in exp or not exp["bullets"]:
            exp["bullets"] = [exp.get("description", "")]
            
    # Map skillCategories to skills for Shokumu-keirekisho
    if "skillCategories" in context:
        new_skills = []
        for cat in context["skillCategories"]:
            if cat.get("visible", True):
                new_skills.append({
                    "name": cat.get("label", ""),
                    "items": cat.get("items", []),
                    "years": cat.get("years", "—"),
                    "level": cat.get("level", "実務経験")
                })
        context["skills"] = new_skills
        
    # Map project attributes
    for proj in context.get("projects", []):
        if "tech" not in proj and "techStack" in proj:
            proj["tech"] = proj["techStack"]
        if "description" not in proj and "summary" in proj:
            proj["description"] = proj["summary"]
            
    # Map certifications
    for cert in context.get("certifications", []):
        year_str = cert.get("year", "")
        # Extract the start year if it's a range
        if "–" in year_str:
            year_str = year_str.split("–")[0].strip()
        elif "-" in year_str:
            year_str = year_str.split("-")[0].strip()
            
        y, m, _ = parse_human_date(year_str)
        cert["year"] = y
        cert["month"] = m
            
    # Include cover letter (already in context from view_data)
    if 'cover_letter' not in context:
        context['cover_letter'] = {}
            
    return context


def _calc_korea_duration(start_year: int, start_month: int, end_year: int, end_month: int, is_current: bool = False) -> str:
    """Returns Korean duration string. Adds 1 month for inclusive counting. Adds '약' for current roles."""
    total_months = (end_year - start_year) * 12 + (end_month - start_month) + 1
    if total_months < 0:
        total_months = 0
    years = total_months // 12
    months = total_months % 12
    
    prefix = "약 " if is_current else ""
    
    # 년: &#45380; | 개월: &#44060;&#50900;
    if years > 0 and months > 0:
        return f"({prefix}{years}&#45380; {months}&#44060;&#50900;)"
    elif years > 0:
        return f"({prefix}{years}&#45380;)"
    elif months > 0:
        return f"({prefix}{months}&#44060;&#50900;)"
    return "(1&#44060;&#50900;)"


def build_korea_context(data: dict) -> dict:
    """Builds enriched context for Korean 이력서 template (Korean_resume_template.html)."""
    import copy
    from datetime import datetime
    context = copy.deepcopy(data)
    today = datetime.today()

    profile = context.get('profile', {})
    summary = profile.get('summary', '')
    if summary:
        profile['summary'] = summary.replace("Japanese", "Korean").replace("Japan's", "Korea's").replace("Japan", "Korea")

    # ── generated_date in Korean format ──────────────────────────────────────
    context['generated_date'] = f"{today.year}년 {today.month}월 {today.day}일"

    # ── profile.address alias ─────────────────────────────────────────────────
    if not profile.get('address'):
        profile['address'] = profile.get('location', '')

    # ── alternate_phone — secondary phone from data ───────────────────────────
    phone_raw = profile.get('phone', '')
    if '/' in phone_raw:
        parts = phone_raw.split('/', 1)
        profile['phone'] = parts[0].strip()
        profile['alternate_phone'] = parts[1].strip()
    else:
        profile['alternate_phone'] = ''

    # ── personal sub-context for template ────────────────────────────────────
    raw_personal = profile.get('personal', {})
    dob_raw = raw_personal.get('dob') or profile.get('dateOfBirth', '')
    dob_formatted = ''
    if dob_raw:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                dob = datetime.strptime(dob_raw, fmt)
                dob_formatted = dob.strftime('%Y/%m/%d')
                break
            except ValueError:
                continue

    # Extract Korean level from languages list
    korean_level = 'Basic'
    for lang in context.get('languages', []):
        if lang.get('name', '').lower() in ('korean', '한국어'):
            korean_level = lang.get('level', 'Basic')
            break

    # Nationality
    nat_raw = raw_personal.get('nationality', profile.get('nationality', 'India'))
    nationality_en = nat_raw.strip().title() if nat_raw else 'India'
    
    # Translate nationality if in Korean
    if context.get('lang') == 'ko' and nationality_en == 'India':
        nationality_display = '인도'
    else:
        nationality_display = nationality_en

    context['personal'] = {
        'gender':        raw_personal.get('gender', ''),
        'dob':           dob_formatted,
        'nationality':   nationality_display,
        'korean_level':  korean_level,
        'visa_type':     raw_personal.get('visa_status', '') or profile.get('visa_info', {}).get('visaType', ''),
        'summary':       profile.get('summary', ''),
        'military_service': raw_personal.get('military_service', 'No'),
    }
    context['korea_dob'] = dob_formatted

    # ── connections — only professional platforms with real URLs ──────────────
    connections = context.get('connections', [])
    resume_platforms = {'github', 'linkedin', 'portfolio', 'website'}
    # Filter to only platforms relevant to a professional resume with non-empty URLs
    filtered = [
        c for c in connections
        if c.get('platform', '').lower() in resume_platforms
        and c.get('url', '').strip()
        and c.get('visible', True)
    ]
    # Ensure GitHub and LinkedIn always appear from profile if missing
    platform_names = {c['platform'].lower() for c in filtered}
    if 'github' not in platform_names and profile.get('github'):
        filtered.append({'platform': 'GitHub', 'url': profile['github'], 'visible': True})
    if 'linkedin' not in platform_names and profile.get('linkedin'):
        filtered.append({'platform': 'LinkedIn', 'url': profile['linkedin'], 'visible': True})
    context['connections'] = filtered

    # ── education ─────────────────────────────────────────────────────────────
    degree_ko_map = {
        'master': 'Master', 'mca': 'Master', 'm.c.a': 'Master', 'm.sc': 'Master', 'msc': 'Master', 'mba': 'Master',
        'bachelor': 'Bachelor', 'bca': 'Bachelor', 'b.c.a': 'Bachelor', 'b.sc': 'Bachelor', 'bsc': 'Bachelor', 'be': 'Bachelor', 'btech': 'Bachelor',
        'phd': 'PhD', 'doctorate': 'PhD',
        'diploma': 'Diploma',
    }
    major_map = {
        'master of computer applications': 'Computer Applications (MCA)',
        'bachelor of computer applications': 'Computer Applications (BCA)',
    }

    for edu in context.get('education', []):
        year_str = edu.get('year', '')
        sep = '–' if '–' in year_str else '-'
        parts = year_str.split(sep)
        try:
            sy = int(parts[0].strip()) if parts[0].strip() else 2000
            ey_raw = parts[1].strip() if len(parts) > 1 else ''
            is_current = ey_raw.lower() in ('', 'present', 'current')
            ey = today.year if is_current else (int(ey_raw) if ey_raw else sy + 4)
        except (ValueError, IndexError):
            sy, ey, is_current = 2000, 2004, False

        # Education months: April start (04), March end (03) — Indian university calendar
        edu['start_year']  = sy
        edu['start_month'] = 4
        edu['end_year']    = ey
        edu['end_month']   = 3
        edu['is_current']  = is_current
        edu['start']       = (sy, 4)
        edu['duration']    = _calc_korea_duration(sy, 4, ey, 3, is_current)

        if 'university' in edu and 'institution' not in edu:
            edu['institution'] = edu['university']

        # degree_en: English label from degree string
        deg_raw = edu.get('degree', '').lower()
        edu['degree_ko'] = 'Bachelor'  # default English label in degree column
        for key, val in degree_ko_map.items():
            if key in deg_raw:
                edu['degree_ko'] = val
                break

        # major: short clean form in English — avoid duplication if same as degree
        full_deg = edu.get('degree', '')
        clean_major = major_map.get(full_deg.lower(), full_deg)
        if clean_major.lower() == edu['degree_ko'].lower():
            edu['major'] = clean_major
        else:
            edu['major'] = f"{edu['degree_ko']} of {clean_major}" if "of" not in clean_major.lower() else clean_major

        edu['gpa'] = edu.get('gpa', '')

    # ── experience ────────────────────────────────────────────────────────────
    emp_type_map = {
        '正社員': '정규직', 'フリーランス': '프리랜서', '契約社員': '계약직',
        'full-time': '정규직', 'fulltime': '정규직', 'permanent': '정규직',
        'freelance': '프리랜서', 'contract': '계약직', 'part-time': '파트타임',
    }

    for exp in context.get('experience', []):
        sy, sm, _ = parse_human_date(exp.get('startDate', ''))
        ey, em, _ = parse_human_date(exp.get('endDate', ''))
        exp['start_year']  = sy
        exp['start_month'] = sm
        exp['end_year']    = ey
        exp['end_month']   = em
        exp['start']       = (sy, sm)
        is_current = exp.get('endDate', '').strip().lower() in ('present', 'current', 'now', '')
        exp['is_current']  = is_current
        exp['duration']    = _calc_korea_duration(sy, sm, ey, em, is_current)

        # employment_type_ko
        etype_raw = (exp.get('employment_type_ja') or exp.get('employment_type') or '').strip().lower()
        if 'freelance' in exp.get('company', '').lower() or 'freelance' in exp.get('role', '').lower() or 'freelance' in etype_raw:
            exp['employment_type_ko'] = '프리랜서'
        elif etype_raw in ('正社員', 'full-time', 'fulltime', 'permanent'):
            exp['employment_type_ko'] = '정규직'
        elif etype_raw in ('契約社員', 'contract'):
            exp['employment_type_ko'] = '계약직'
        else:
            exp['employment_type_ko'] = '정규직'

        if not exp.get('bullets'):
            exp['bullets'] = [exp['description']] if exp.get('description') else []

    # ── languages — add level_dots and level_label ────────────────────────────
    pct_to_dots = [(90, 5), (70, 4), (50, 3), (30, 2), (0, 1)]
    # Level label map — English values
    level_label_map = {
        'native': 'Native', 'mother tongue': 'Native',
        'business level': 'Business Level', 'business': 'Business Level', 'advanced': 'Business Level',
        'intermediate': 'Intermediate', 'conversational': 'Intermediate',
        'beginner': 'Basic', 'basic': 'Basic', 'beginner (currently learning)': 'Basic (Learning)',
        'elementary': 'Basic',
    }
    note_map = {
        'korean': 'Currently Learning',
        'japanese': 'Currently Learning',
        'english': 'Business Advanced',
        'hindi': 'Mother Tongue',
        'gujarati': 'Mother Tongue',
    }
    # Keep language names in English, force Korean visible
    korea_langs = []
    for lang in context.get('languages', []):
        name_lower = lang.get('name', '').lower()
        if not lang.get('visible', True) and name_lower not in ('korean', '한국어'):
            continue
        pct = lang.get('percentage', 50)
        dots = 1
        for threshold, d in pct_to_dots:
            if pct >= threshold:
                dots = d
                break
        raw_level = lang.get('level', '').lower()
        label = level_label_map.get(raw_level, lang.get('level', ''))
        # Keep English names (no Korean translation)
        korea_langs.append({
            'name':        lang['name'],   # Keep original English name
            'level_dots':  dots,
            'level_label': label,
            'cert':        lang.get('cert', ''),
            'note':        note_map.get(name_lower, ''),
        })
    context['languages'] = korea_langs

    # ── skills — remap skillCategories → skills ───────────────────────────────
    skills = []
    for cat in context.get('skillCategories', []):
        if not cat.get('visible', True):
            continue
        # Map level string to dots (Experienced=5, Skilled=4, Proficient=3, etc.)
        level_str = cat.get('level', 'Experienced').lower()
        dots = 5
        if 'expert' in level_str or 'senior' in level_str: dots = 5
        elif 'experienced' in level_str or 'skilled' in level_str: dots = 4
        elif 'proficient' in level_str or 'intermediate' in level_str: dots = 3
        elif 'familiar' in level_str or 'basic' in level_str: dots = 2
        else: dots = 4 # default

        skills.append({
            'name':  cat.get('label', cat.get('name', '')),
            'items': cat.get('items', []),
            'level': cat.get('level', 'Experienced'),
            'level_dots': dots
        })
    context['skills'] = skills

    # ── awards — filter achievements that have year + issuer ─────────────────
    awards = []
    for ach in context.get('achievements', []):
        year_raw = str(ach.get('year', ''))
        # Only items with a proper year (not empty) AND an issuer go into 수상
        if year_raw and year_raw.isdigit() and ach.get('issuer'):
            y, m, _ = parse_human_date(year_raw)
            awards.append({
                'year':   y,
                'month':  m if m else 1,
                'name':   ach.get('title', ''),
                'issuer': ach.get('issuer', ''),
            })
    context['awards'] = awards

    # ── projects — map for template — Limit to top 5 for Korea ────────────────
    projects_out = []
    # Sort projects by priority or just take first 5
    raw_projects = context.get('projects', [])
    for p in raw_projects[:5]:
        if p.get('hidden'):
            continue
        tech = p.get('techStack') or p.get('tech') or p.get('technologies', '')
        if isinstance(tech, list):
            tech = ', '.join(tech)
        
        # Localization
        team_size = str(p.get('team_size', 'Individual'))
        role = str(p.get('role', 'Developer'))
        
        projects_out.append({
            'name':      p.get('name', ''),
            'period':    p.get('period', ''),
            'team_size': '개인' if 'individual' in team_size.lower() else team_size,
            'tech':      tech,
            'role':      '개발자' if 'developer' in role.lower() else role,
            'summary':   p.get('summary') or p.get('description', ''),
        })
    context['projects'] = projects_out

    # ── research ──────────────────────────────────────────────────────────────
    research_out = []
    for r in context.get('research', []) + context.get('researchInterests', []):
        if not r.get('visible', True):
            continue
        research_out.append({
            'title':       r.get('title', r.get('topic', '')),
            'status':      r.get('status', 'Writing'),
            'year':        r.get('year', today.year),
            'description': r.get('description', r.get('summary', '')),
        })
    context['research'] = research_out

    # ── cover_letter — defaults ───────────────────────────────────────────────
    cl = context.get('cover_letter', {})
    context['cover_letter'] = {
        'growth_background':   cl.get('growth_background',   '[Please write your background and growth]'),
        'strengths_weaknesses': cl.get('strengths_weaknesses', '[Please write your strengths and weaknesses]'),
        'motivation':          cl.get('motivation',           '[Please write your reason for applying]'),
        'goals_after_joining': cl.get('goals_after_joining',  '[Please write your goals after joining]'),
    }

    return context


def build_china_context(data: dict) -> dict:
    """Builds enriched context for Chinese 简历 template."""
    import copy
    from datetime import datetime
    context = copy.deepcopy(data)
    today = datetime.today()

    # ── generated_date in Chinese format ─────────────────────────────────────
    context['generated_date'] = f"{today.year}年{today.month}月{today.day}日"
    
    # Simple mapping for labels if not already done by translation service
    context['L_CN'] = {
        'education': '教育背景',
        'experience': '工作经历',
        'projects': '项目经验',
        'skills': '专业技能',
        'summary': '自我评价'
    }

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

async def generate_resume_playwright(data, live_projects=None, region="international", include_photo=False, return_html=False, lang="en", include_cover=False):
    """Generate Resume PDF using Jinja2 and Playwright."""
    
    # 1. Prepare View Data
    profile = data.get('profile', {}).copy()   # single copy, keep it
    personal = profile.get('personal', {})
    
    from datetime import datetime
    today = datetime.today()

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

    # Calculate age from personal.dob (not profile.dateOfBirth)
    dob_str = personal.get('dob') or profile.get('dateOfBirth', '')
    if dob_str:
        try:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    dob = datetime.strptime(dob_str, fmt)
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    profile['age'] = age
                    personal['age'] = age
                    personal['japanese_dob_era'] = to_japanese_era(dob.year, dob.month, dob.day) + f" {dob.month}月 {dob.day}日"
                    break
                except ValueError:
                    continue
        except Exception:
            pass
            
    # Map furigana to profile so template can access them easily
    profile['name_furigana'] = personal.get('name_furigana', '')
    profile['address_furigana'] = personal.get('address_furigana', '')
    if not profile.get('address') and profile.get('location'):
        profile['address'] = profile.get('location')

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
        'projects': data.get('projects', []),
        'research': data.get('research', []),
        'researchInterests': data.get('researchInterests', []),
        'achievements': data.get('achievements', []),
        'certifications': data.get('certifications', []),
        'connections': data.get('connections', []),
        'languages': data.get('languages', []),
        'skillCategories': data.get('skillCategories', []),
        'skills': data.get('skills', []),
        'live_projects': enriched_projects,
        'categorized_projects': get_categorized_projects(enriched_projects),
        'base_css': get_file_uri('css/base.css'),
        'generated_era_year': str(reiwa_year),
        'generated_month': str(today.month),
        'generated_day': str(today.day),
        'generated_date': (to_japanese_era(today.year, today.month, today.day) + f" {today.month}月 {today.day}日") if region == 'japan' else today.strftime("%B %d, %Y"),
        'data': data,
        'cover_letter': (lambda cl: {**cl, 'content': cl.get('content') or "\n\n".join(filter(None, [cl.get('growth_background'), cl.get('strengths_weaknesses'), cl.get('motivation'), cl.get('goals_after_joining')]))})(data.get('cover_letter', {})),
        'include_cover': include_cover,
        'show_project_images': region not in {'international', 'academic'}
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

    # 2. Select Template & Apply Rules
    geo_rule = get_geo_rule(region)
    template_name = geo_rule['template']
    view_data['specific_css'] = get_file_uri(geo_rule['css'])
    pdf_format = geo_rule['format']
    pdf_margin = geo_rule['margin']
    view_data['L'] = get_labels(lang)
    view_data['lang'] = lang
    view_data['geo_rule'] = geo_rule

    # Data Pruning Layer (Compliance)
    raw_personal = profile.get('personal', {}).copy()
    for field in geo_rule.get('prune_fields', []):
        if field in raw_personal:
            raw_personal[field] = ""
        # Also prune from top-level profile if they exist there
        if field in profile:
            profile[field] = ""
    
    # Apply allowed personal fields if specialty
    if geo_rule.get('specialty'):
        # In specialty templates, we might still want to filter personal data strictly
        # or we might just use raw_personal.
        view_data['personal'] = raw_personal
    else:
        # Standard ATS: Minimal personal data usually
        view_data['personal'] = raw_personal

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

    def process_china(vd):
        process_photo(vd)
        # Any specific field normalization for China
        pass

    def process_international(vd):
        # Merge research and researchInterests for ATS
        res = vd.get('research', [])
        interests = vd.get('researchInterests', [])
        merged_res = []
        seen_titles = set()
        
        for r in res:
            title = r.get('title', '').strip()
            if title:
                merged_res.append(r)
                seen_titles.add(title.lower())
        
        for i in interests:
            topic = i.get('topic', '').strip()
            if topic and topic.lower() not in seen_titles:
                merged_res.append({
                    'title': topic,
                    'year': i.get('year', ''),
                    'description': i.get('description', '')
                })
        vd['research'] = merged_res

    # 3. JIT Translation for all sections (Batched to avoid rate limits)
    if lang != 'en':
        queue = [] # List of {"text": str, "field_name": str, "callback": function}
        
        # Summary
        if view_data.get('about'):
            for i, text in enumerate(view_data['about']):
                def make_cb(idx): return lambda t: view_data['about'].__setitem__(idx, t)
                queue.append({"text": text, "field_name": "about", "cb": make_cb(i)})

        # Experience
        if view_data.get('experience'):
            for exp in view_data['experience']:
                def set_field(obj, key): return lambda t: obj.__setitem__(key, t)
                queue.append({"text": exp.get('role', ''), "field_name": "exp_role", "cb": set_field(exp, 'role')})
                queue.append({"text": exp.get('company', ''), "field_name": "exp_company", "cb": set_field(exp, 'company')})
                if exp.get('bullets'):
                    for i, b in enumerate(exp['bullets']):
                        queue.append({"text": b, "field_name": "exp_bullet", "cb": make_cb(i) if False else (lambda t, e=exp, idx=i: e['bullets'].__setitem__(idx, t))})
                if exp.get('description'):
                    queue.append({"text": exp['description'], "field_name": "exp_desc", "cb": set_field(exp, 'description')})
                if exp.get('resign_reason_ja'):
                    queue.append({"text": exp['resign_reason_ja'], "field_name": "exp_resign", "cb": set_field(exp, 'resign_reason_ja')})

        # Projects
        if view_data.get('live_projects'):
            for proj in view_data['live_projects']:
                def set_p(p, k): return lambda t: p.__setitem__(k, t)
                queue.append({"text": proj.get('name', ''), "field_name": "proj_name", "cb": set_p(proj, 'name')})
                queue.append({"text": proj.get('summary', ''), "field_name": "proj_summary", "cb": set_p(proj, 'summary')})
                queue.append({"text": proj.get('description', ''), "field_name": "proj_desc", "cb": set_p(proj, 'description')})
                queue.append({"text": proj.get('role', ''), "field_name": "proj_role", "cb": set_p(proj, 'role')})
                queue.append({"text": proj.get('tech', ''), "field_name": "proj_tech", "cb": set_p(proj, 'tech')})
                queue.append({"text": proj.get('techStack', ''), "field_name": "proj_tech_stack", "cb": set_p(proj, 'techStack')})

        # Education
        if view_data.get('education'):
            for edu in view_data['education']:
                def set_e(e, k): return lambda t: e.__setitem__(k, t)
                queue.append({"text": edu.get('degree', ''), "field_name": "edu_degree", "cb": set_e(edu, 'degree')})
                queue.append({"text": edu.get('major', ''), "field_name": "edu_major", "cb": set_e(edu, 'major')})
                if edu.get('notes'):
                    queue.append({"text": edu['notes'], "field_name": "edu_notes", "cb": set_e(edu, 'notes')})
                if edu.get('university'):
                    queue.append({"text": edu['university'], "field_name": "edu_uni", "cb": set_e(edu, 'university')})

        # Achievements
        if view_data.get('achievements'):
            for ach in view_data['achievements']:
                def set_a(a, k): return lambda t: a.__setitem__(k, t)
                queue.append({"text": ach.get('title', ''), "field_name": "ach_title", "cb": set_a(ach, 'title')})
                queue.append({"text": ach.get('description', ''), "field_name": "ach_desc", "cb": set_a(ach, 'description')})

        # Research
        if view_data.get('research'):
            for res in view_data['research']:
                def set_r(r, k): return lambda t: r.__setitem__(k, t)
                queue.append({"text": res.get('title', ''), "field_name": "res_title", "cb": set_r(res, 'title')})
                queue.append({"text": res.get('description', ''), "field_name": "res_desc", "cb": set_r(res, 'description')})
                queue.append({"text": res.get('status', ''), "field_name": "res_status", "cb": set_r(res, 'status')})

        # Skill Categories
        if view_data.get('skillCategories'):
            for cat in view_data['skillCategories']:
                def set_c(c, k): return lambda t: c.__setitem__(k, t)
                queue.append({"text": cat.get('label', ''), "field_name": "skill_cat", "cb": set_c(cat, 'label')})

        # Cover Letter
        if view_data.get('cover_letter'):
            cl = view_data['cover_letter']
            for field in ['content', 'intro', 'body', 'closing', 'professional_summary', 'growth_willingness', 'motivation', 'vision']:
                if cl.get(field):
                    def set_cl(c, k): return lambda t: c.__setitem__(k, t)
                    queue.append({"text": cl[field], "field_name": f"cl_{field}", "cb": set_cl(cl, field)})

        # Projects (Manual ones)
        if view_data.get('projects'):
            for proj in view_data['projects']:
                def set_p_m(p, k): return lambda t: p.__setitem__(k, t)
                queue.append({"text": proj.get('name', ''), "field_name": "proj_name", "cb": set_p_m(proj, 'name')})
                queue.append({"text": proj.get('summary', ''), "field_name": "proj_summary", "cb": set_p_m(proj, 'summary')})
                queue.append({"text": proj.get('description', ''), "field_name": "proj_desc", "cb": set_p_m(proj, 'description')})
                queue.append({"text": proj.get('role', ''), "field_name": "proj_role", "cb": set_p_m(proj, 'role')})
                queue.append({"text": proj.get('tech', ''), "field_name": "proj_tech", "cb": set_p_m(proj, 'tech')})
                queue.append({"text": proj.get('techStack', ''), "field_name": "proj_tech_stack", "cb": set_p_m(proj, 'techStack')})

        # Certifications
        if view_data.get('certifications'):
            for cert in view_data['certifications']:
                def set_cert(c, k): return lambda t: c.__setitem__(k, t)
                queue.append({"text": cert.get('name', ''), "field_name": "cert_name", "cb": set_cert(cert, 'name')})

        # Languages
        if view_data.get('languages'):
            for l in view_data['languages']:
                def set_l(obj, k): return lambda t: obj.__setitem__(k, t)
                queue.append({"text": l.get('name', ''), "field_name": "lang_name", "cb": set_l(l, 'name')})
                queue.append({"text": l.get('level', ''), "field_name": "lang_level", "cb": set_l(l, 'level')})

        # Profile / Personal
        if view_data.get('profile'):
            prof = view_data['profile']
            def set_prof(p, k): return lambda t: p.__setitem__(k, t)
            if prof.get('summary'):
                queue.append({"text": prof['summary'], "field_name": "profile_summary", "cb": set_prof(prof, 'summary')})
            
            pers = prof.get('personal', {})
            if pers:
                def set_pers(p, k): return lambda t: p.__setitem__(k, t)
                if pers.get('self_pr_ja'):
                    queue.append({"text": pers['self_pr_ja'], "field_name": "self_pr", "cb": set_pers(pers, 'self_pr_ja')})
                if pers.get('career_summary_ja'):
                    queue.append({"text": pers['career_summary_ja'], "field_name": "career_summary", "cb": set_pers(pers, 'career_summary_ja')})
                if pers.get('desired_conditions_ja'):
                    queue.append({"text": pers['desired_conditions_ja'], "field_name": "desired_cond", "cb": set_pers(pers, 'desired_conditions_ja')})
                if pers.get('nationality'):
                    queue.append({"text": pers['nationality'], "field_name": "nationality", "cb": set_pers(pers, 'nationality')})
                if pers.get('summary'):
                    queue.append({"text": pers['summary'], "field_name": "pers_summary", "cb": set_pers(pers, 'summary')})
                if pers.get('visa_status'):
                    queue.append({"text": pers['visa_status'], "field_name": "visa_status", "cb": set_pers(pers, 'visa_status')})
                if pers.get('political_status'):
                    queue.append({"text": pers['political_status'], "field_name": "political_status", "cb": set_pers(pers, 'political_status')})
            
            if prof.get('address'):
                queue.append({"text": prof['address'], "field_name": "address", "cb": set_prof(prof, 'address')})

        # Execute Batch Translation
        if queue:
            batch_items = [{"text": q["text"], "field_name": q["field_name"]} for q in queue]
            translated_results = await translate_batch(batch_items, lang)
            
            # Apply results back
            for i, translated_text in enumerate(translated_results):
                queue[i]["cb"](translated_text)

    # 4. Process Region-Specific Logic
    if region == 'japan':
        process_japan(view_data)
    elif region == 'korea':
        process_korea(view_data)
    elif region == 'china':
        process_china(view_data)
    elif region == 'international' or region in ATS_COUNTRIES:
        process_international(view_data)
    else:
        # Default photo processing
        process_photo(view_data)

    # 5. Render HTML
    if region == 'japan':
        japan_context = build_japan_context(view_data)
        template_rirekisho = env.get_template('template_japan_rirekisho.html')
        html_rirekisho = template_rirekisho.render(**japan_context)
        template_shokumu = env.get_template('template_japan_shokumu.html')
        html_shokumu = template_shokumu.render(**japan_context)
        
        if return_html:
            html = html_rirekisho + "\n<div style='page-break-after: always; height: 20px; background: #eee;'></div>\n" + html_shokumu
            return html.replace("file:///" + TEMPLATES_DIR.replace("\\", "/"), "/static/templates")
            
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

    elif region == 'korea':
        korea_context = build_korea_context(view_data)
        template = env.get_template(template_name)
        html_content = template.render(**korea_context)
    elif region == 'china':
        china_context = build_china_context(view_data)
        template = env.get_template(template_name)
        html_content = template.render(**china_context)
    else:
        template = env.get_template(template_name)
        html_content = template.render(**view_data)

    if return_html:
        # Inject Neural Scroll Sync Script
        sync_script = """
        <script>
            (function() {
                window.onscroll = function() {
                    var percentage = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);
                    window.parent.postMessage({ type: 'scroll', percentage: percentage, sourceId: window.name || location.href }, '*');
                };
                window.addEventListener('message', function(event) {
                    if (event.data && event.data.type === 'scroll' && event.data.sourceId !== (window.name || location.href)) {
                        var targetScroll = event.data.percentage * (document.documentElement.scrollHeight - window.innerHeight);
                        window.scrollTo(0, targetScroll);
                    }
                });
            })();
        </script>
        """
        html_with_sync = html_content + sync_script
        return html_with_sync.replace("file:///" + TEMPLATES_DIR.replace("\\", "/"), "/static/templates")

    # 6. Generate PDF
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


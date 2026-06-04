import os
import asyncio
import re
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
from markupsafe import Markup
import html

# Global Playwright concurrency limit
pdf_semaphore = asyncio.Semaphore(3)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'resume_templates')

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), extensions=['jinja2.ext.do'])

from services.geo_rules import get_geo_rule, ATS_COUNTRIES
from services.translations import (
    get_labels,
    translate_text,
    translate_batch,
    translate_text_sync,
    translate_batch_sync,
    resolve_region_visa_status,
    is_sufficiently_translated,
)


# Helper to normalize file paths for CSS
def get_file_uri(rel_path):
    return "file:///" + os.path.join(TEMPLATES_DIR, rel_path).replace("\\", "/")

def apply_phone_display(profile: dict) -> None:
    """Format profile.phone as 'primary / alternate' when alternate_phone is set."""
    phone = (profile.get('phone') or '').strip()
    alt = (profile.get('alternate_phone') or '').strip()
    if ' / ' in phone:
        return
    if '/' in phone and not alt:
        parts = phone.split('/', 1)
        phone, alt = parts[0].strip(), parts[1].strip()
    if alt and alt != phone:
        profile['phone'] = f"{phone} / {alt}"
        profile['alternate_phone'] = alt
    else:
        profile['phone'] = phone

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

def calculate_experience_years(start_year: int, start_month: int) -> str:
    """Dynamically calculates years of experience from a start date."""
    from datetime import date
    today = date.today()
    months = (today.year - start_year) * 12 + (today.month - start_month)
    years = months // 12
    return f"{years}+"


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
    if not projects:
        return []
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

def calculate_proficiency(years_str: str, lang: str = "en") -> str:
    """Dynamically calculates proficiency label based on years and target language."""
    from services.translations import PROFICIENCY_LEVELS
    import re
    
    # Normalize lang code
    if lang == "cn": lang = "zh"
    if lang not in ["en", "ja", "ko", "zh"]: lang = "en"
    
    levels = PROFICIENCY_LEVELS.get(lang, PROFICIENCY_LEVELS["en"])
    
    # Fallback if no years provided
    if not years_str or str(years_str).strip() in ("", "—"):
        return levels["experienced"] # Default to Experienced for this candidate
    
    # Try to find a decimal or integer number (e.g. "5", "3.5", "5+")
    match = re.search(r"(\d+(\.\d+)?)", str(years_str))
    if not match:
        return levels["experienced"]
    
    try:
        years = float(match.group(1))
    except ValueError:
        return levels["experienced"]
    
    # Unified Years-to-Level Logic
    if years <= 1.0:
        return levels["beginner"]
    elif years <= 3.0:
        return levels["intermediate"]
    elif years <= 5.0:
        return levels["experienced"]
    elif years <= 10.0:
        return levels["advanced"]
    else:
        return levels["expert"]

def build_japan_context(data: dict) -> dict:
    """Builds context for Japanese resume template"""
    import copy
    context = copy.deepcopy(data)
    context['L'] = get_labels(context.get('lang', 'ja'))
    
    if "profile" in context and "personal" in context["profile"]:
        p = context["profile"]
        personal_data = p["personal"]
        p["name"] = p.get("name", "")
        p["name_furigana"] = personal_data.get("name_furigana", "")
        p["email"] = p.get("email", "")
        
        apply_phone_display(p)
        
        p["address"] = p.get("location", "")
        p["address_furigana"] = personal_data.get("address_furigana", "")
        # JP6: Use nationality_ja (印度) for ja, nationality (India) for en
        if context.get('lang') == 'ja':
            p["nationality_display"] = personal_data.get("nationality_ja", "印度")
        else:
            p["nationality_display"] = personal_data.get("nationality", "India")
        # JP9: Hide postal code for overseas applicants (no Japanese postal code)
        p["postal_code"] = ""  # Always blank for overseas — hides 〒000-0000 placeholder

        # Visa status translation mapping
        personal_data["visa_status"] = (
            (context.get('personal') or {}).get('visa_status', '').strip()
            or resolve_region_visa_status(
                p.get('visa', {}),
                'JP',
                context.get('lang', 'ja'),
            )
        )
        if 'personal' not in context:
            context['personal'] = {}
        context['personal']['visa_status'] = personal_data["visa_status"]

        if context.get('lang') == 'ja':
            if p.get('summary_ja'):
                p['summary'] = p['summary_ja']
            if personal_data.get('career_summary_ja'):
                personal_data['self_pr_ja'] = personal_data.get('career_summary_ja')

        gender = personal_data.get("gender", "").lower()
        L = get_labels(context.get('lang', 'ja'))
        if gender.startswith("m"):
            p["gender_ja"] = L.get("male", "Male")
        elif gender.startswith("f"):
            p["gender_ja"] = L.get("female", "Female")
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
        # JE4: Fix date formatter — use zero-padded month to avoid '20223' concatenation
        exp["start_ym"] = f"{sy}/{sm:02d}"
        exp["end_ym"] = f"{ey}/{em:02d}" if not end_str.strip().lower() in ('present', 'current', 'now', '') else ""
        exp["start"] = (sy, sm)
        
        # Determine if the job is current
        is_current_str = end_str.strip().lower()
        exp["is_current"] = is_current_str in ["present", "current", "now", ""]
        
        if "bullets" not in exp or not exp["bullets"]:
            exp["bullets"] = [exp.get("description", "")]

        # JP13: Correct employment type labels for Japan
        etype_raw = (exp.get('employment_type_ja') or exp.get('employment_type') or '').strip().lower()
        company_lower = exp.get('company', '').lower()
        role_lower = exp.get('role', '').lower()
        is_freelance = (
            'freelance' in company_lower or 'freelancer' in company_lower or 'フリーランス' in company_lower or
            'freelance' in role_lower or 'freelancer' in role_lower or 'フリーランス' in role_lower or
            'freelance' in etype_raw or 'freelancer' in etype_raw or 'フリーランス' in etype_raw
        )
        L_exp = context.get('L', {})
        if is_freelance:
            exp['employment_type_ja'] = L_exp.get('freelance', 'フリーランス')
        elif not exp.get('employment_type_ja'):
            exp['employment_type_ja'] = L_exp.get('fulltime', '正社員')

        # JP8: Use standard resignation phrase (rirekisho template reads resign_reason)
        if exp.get("is_current") is False:
            if context.get('lang') == 'ja':
                reason = exp.get("resign_reason_ja") or context.get('profile', {}).get('personal', {}).get(
                    'resign_reason_standard_ja', '一身上の都合により退社'
                )
            else:
                reason = exp.get("resign_reason") or context.get('profile', {}).get('personal', {}).get(
                    'resign_reason_standard_en', L.get('resignation_reason', 'Resigned for personal reasons')
                )
            exp["resign_reason_ja"] = reason if context.get('lang') == 'ja' else exp.get('resign_reason_ja')
            exp["resign_reason"] = reason

        # Shokumu table fields — defaults when missing from source data
        lang_code = context.get('lang', 'ja')
        L_exp = get_labels(lang_code)
        if not (exp.get('role') or '').strip():
            exp['role'] = 'Developer' if lang_code == 'en' else L_exp.get('developer', '開発者')
        if not (exp.get('team_size') or '').strip():
            exp['team_size'] = L_exp.get('individual', '個人') if lang_code == 'ja' else 'Individual'
            
    # Map skillCategories to skills for Shokumu-keirekisho
    if "skillCategories" in context:
        new_skills = []
        L = get_labels(context.get('lang', 'ja'))
        lang_code = context.get('lang', 'ja')
        for cat in context["skillCategories"]:
            if cat.get("visible", True):
                # Automatically calculate proficiency based on years of experience
                calc_level = calculate_proficiency(cat.get("years", ""), lang_code)
                new_skills.append({
                    "name": cat.get("label", ""),
                    "items": cat.get("items", []),
                    "years": cat.get("years", "—"),
                    "level": calc_level or cat.get("level") or L.get("proficiency_label", "Proficient")
                })
        context["skills"] = new_skills

    # JP-NEW5: Localize research status ("Writing" → "執筆中" etc.)
    L_res = get_labels(context.get('lang', 'ja'))
    for r in context.get('research', []):
        raw_status = r.get('status', 'Writing')
        if raw_status.lower() in ('writing', 'in progress'):
            r['status'] = L_res.get('writing_status', raw_status)
        
    # Map project attributes
    for proj in context.get("projects", []):
        if "tech" not in proj and "techStack" in proj:
            proj["tech"] = proj["techStack"]
        if "description" not in proj and "summary" in proj:
            proj["description"] = proj["summary"]
            
    # 履歴書 免許・資格 — official licenses only (awards go on 職務経歴書)
    license_rows = []
    for cert in context.get("certifications", []):
        year_str = cert.get("year", "")
        if "–" in year_str:
            year_str = year_str.split("–")[0].strip()
        elif "-" in year_str:
            year_str = year_str.split("-")[0].strip()
        y, m, _ = parse_human_date(year_str)
        license_rows.append({"year": y, "month": m, "name": cert.get("name", "")})
    license_rows.sort(key=lambda x: (x["year"], x["month"]))
    context["certifications"] = license_rows

    awards_rows = []
    for ach in context.get("achievements", []):
        if not ach.get("visible", True):
            continue
        year_str = ach.get("year", "")
        y, m, _ = parse_human_date(year_str)
        if ach.get("month"):
            try:
                m = int(ach["month"])
            except ValueError:
                m = None
        else:
            m = None
        awards_rows.append({
            "year": y,
            "month": m,
            "name": ach.get("title", ""),
            "issuer": ach.get("issuer", ""),
        })
    awards_rows.sort(key=lambda x: (x["year"], x["month"]))
    context["awards"] = awards_rows

    # Expose GitHub/LinkedIn on profile for 履歴書 contact block
    prof = context.get("profile", {})
    if not prof.get("github") and context.get("connections"):
        for conn in context["connections"]:
            if conn.get("platform", "").lower() == "github" and conn.get("url"):
                prof["github"] = conn["url"]
            if conn.get("platform", "").lower() == "linkedin" and conn.get("url"):
                prof["linkedin"] = conn["url"]
            
    # Include cover letter (already in context from view_data)
    if 'cover_letter' not in context:
        context['cover_letter'] = {}
            
    return context


def _calc_korea_duration(start_year: int, start_month: int, end_year: int, end_month: int, is_current: bool = False, lang: str = 'ko') -> str:
    """Returns localized duration string. Adds 1 month for inclusive counting."""
    total_months = (end_year - start_year) * 12 + (end_month - start_month) + 1
    if total_months < 0:
        total_months = 0
    years = total_months // 12
    months = total_months % 12
    
    is_en = lang == 'en'
    prefix = ("Approx. " if is_en else "약 ") if is_current else ""
    year_label = " yr" if is_en else "&#45380;"
    month_label = " mo" if is_en else "&#44060;&#50900;"
    
    if years > 0 and months > 0:
        return f"({prefix}{years}{year_label} {months}{month_label})"
    elif years > 0:
        return f"({prefix}{years}{year_label})"
    elif months > 0:
        return f"({prefix}{months}{month_label})"
    return f"(1{month_label})"


def build_korea_context(data: dict) -> dict:
    """Builds enriched context for Korean 이력서 template (Korean_resume_template.html)."""
    import copy
    from datetime import datetime
    context = copy.deepcopy(data)
    context['L'] = get_labels(context.get('lang', 'ko'))
    today = datetime.today()

    profile = context.get('profile', {})
    # KR1: Keep summary in English — do not machine-translate to Korean
    # Only replace Japan-specific references with Korea equivalents if present
    summary = profile.get('summary', '')
    if summary:
        profile['summary'] = summary.replace("Japanese", "Korean").replace("Japan's", "Korea's").replace("Japan", "Korea")

    # ── generated_date in localized format ──────────────────────────────────────
    is_ko = context.get('lang') == 'ko'
    if is_ko:
        context['generated_date'] = f"{today.year}년 {today.month}월 {today.day}일"
    else:
        context['generated_date'] = today.strftime('%Y/%m/%d')

    # ── profile.address alias ─────────────────────────────────────────────────
    if not profile.get('address'):
        profile['address'] = profile.get('location', '')

    apply_phone_display(profile)

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

    # Nationality - Region Aware
    if context.get('lang') == 'ko':
        nationality_display = '인도'
    else:
        nationality_display = 'India'

    is_en = context.get('lang') == 'en'
    gender_raw = raw_personal.get('gender', '').lower()
    if gender_raw.startswith('f'):
        gender_display = 'Female' if is_en else '여성'
    elif gender_raw.startswith('m'):
        gender_display = 'Male' if is_en else '남성'
    else:
        gender_display = ''

    context['personal'] = {
        'gender':        gender_display,
        'dob':           dob_formatted,
        'nationality':   nationality_display,
        'korean_level':  korean_level,
        'visa_type':     (
            (context.get('personal') or {}).get('visa_status', '').strip()
            or resolve_region_visa_status(
                profile.get('visa', {}),
                'KR',
                context.get('lang', 'ko'),
            )
        ),
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
        # Improved Date Parsing for Education
        import re
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        def parse_edu_year(s):
            s = s.lower().strip()
            # Try to find a 4-digit year
            year_match = re.search(r'(\d{4})', s)
            year = int(year_match.group(1)) if year_match else 2000
            # Try to find a month name
            month = 4 # Default to April
            for name, val in month_map.items():
                if name in s:
                    month = val
                    break
            return year, month

        parts = re.split(r'[–\-\—]', year_str)
        try:
            sy, sm = parse_edu_year(parts[0])
            if len(parts) > 1:
                ey_str = parts[1].strip()
                is_current = ey_str.lower() in ('', 'present', 'current', 'now')
                if is_current:
                    ey, em = today.year, today.month
                else:
                    ey, em = parse_edu_year(ey_str)
            else:
                ey, em, is_current = sy + 4, 3, False
        except Exception:
            sy, sm, ey, em, is_current = 2000, 4, 2004, 3, False

        edu['start_year']  = sy
        edu['start_month'] = sm
        edu['end_year']    = ey
        edu['end_month']   = em
        edu['is_current']  = is_current
        edu['start']       = (sy, sm)
        edu['duration']    = _calc_korea_duration(sy, sm, ey, em, is_current, context.get('lang'))

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
        exp['duration']    = _calc_korea_duration(sy, sm, ey, em, is_current, context.get('lang'))

        # KR3: Correct employment type labels for Korea
        is_en = context.get('lang') == 'en'
        etype_raw = (exp.get('employment_type_ja') or exp.get('employment_type') or '').strip().lower()
        company_lower = exp.get('company', '').lower()
        role_lower = exp.get('role', '').lower()
        if 'freelance' in company_lower or 'freelance' in role_lower or 'freelance' in etype_raw:
            exp['employment_type_ko'] = 'Freelance' if is_en else '프리랜서'
        elif etype_raw in ('정규직', 'full-time', 'fulltime', 'permanent', '正社員'):
            exp['employment_type_ko'] = 'Full-time' if is_en else '정규직'
        elif etype_raw in ('계약직', 'contract', '契約社員'):
            exp['employment_type_ko'] = 'Contract' if is_en else '계약직'
        else:
            exp['employment_type_ko'] = 'Full-time' if is_en else '정규직'

        # status labels
        L = get_labels(context.get('lang', 'ko'))
        exp['status_label'] = (L.get('current', 'Current') if exp['is_current'] else L.get('left', 'Resigned')) if context.get('lang') != 'ko' else ('재직중' if exp['is_current'] else '퇴사')

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
        'hindi': 'Mother Tongue',
        'gujarati': 'Mother Tongue',
    }
    lang_display_ko = {
        'english': '영어',
        'hindi': '힌디어',
        'gujarati': '구자라트어',
        'korean': '한국어',
        'japanese': '일본어',
        'chinese': '중국어',
        'mandarin': '중국어',
    }
    lang_display_en = {
        'english': 'English',
        'hindi': 'Hindi',
        'gujarati': 'Gujarati',
        'korean': 'Korean',
        'japanese': 'Japanese',
        'chinese': 'Chinese',
        'mandarin': 'Chinese',
    }
    # Language Relevance Filter: Only show languages relevant to the region
    relevant_langs = []
    region_lower = (context.get('region') or data.get('region', 'korea')).lower()
    for lang in context.get('languages', []):
        name_lower = lang.get('name', '').lower()
        
        # Core languages always visible
        if name_lower in ('english', 'hindi'):
            is_relevant = True
        # Regional languages only show for their region
        elif name_lower in ('japanese', '日本語'):
            is_relevant = region_lower == 'japan'
        elif name_lower in ('korean', '한국어'):
            is_relevant = region_lower == 'korea'
        elif name_lower in ('chinese', 'mandarin', '中文'):
            is_relevant = region_lower == 'china'
        else:
            is_relevant = lang.get('visible', True)
            
        if not is_relevant:
            continue
            
        pct = lang.get('percentage', 50)
        dots = 1
        for threshold, d in pct_to_dots:
            if pct >= threshold:
                dots = d
                break
        raw_level = lang.get('level', '').lower()
        label = level_label_map.get(raw_level, lang.get('level', ''))
        display_names = lang_display_en if is_en else lang_display_ko
        display_name = display_names.get(name_lower, lang.get('name', ''))
        if not is_en and name_lower == 'hindi' and raw_level in ('native', 'mother tongue'):
            label = '원어민'
        note = note_map.get(name_lower, '')
        if is_en and name_lower == 'english' and 'business' in raw_level:
            note = ''  # avoid "Business Fluent Business Advanced" duplicate
        relevant_langs.append({
            'name':        display_name,
            'level_dots':  dots,
            'level_label': label,
            'cert':        lang.get('cert', ''),
            'note':        note,
        })
    context['languages'] = relevant_langs

    # ── skills — remap skillCategories → skills ───────────────────────────────
    skills = []
    for cat in context.get('skillCategories', []):
        if not cat.get('visible', True):
            continue
        # Automatically calculate proficiency based on years of experience
        calc_level = calculate_proficiency(cat.get("years", ""), context.get('lang', 'ko'))
        
        # Map word-based level back to dots for the visual template
        level_dots = 4
        if "expert" in calc_level.lower() or "전문가" in calc_level: level_dots = 5
        elif "advanced" in calc_level.lower() or "고급" in calc_level: level_dots = 5
        elif "experienced" in calc_level.lower() or "경험" in calc_level: level_dots = 4
        elif "intermediate" in calc_level.lower() or "중급" in calc_level: level_dots = 3
        else: level_dots = 2

        skills.append({
            'name':  cat.get('label', cat.get('name', '')),
            'items': cat.get('items', []),
            'level': calc_level,
            'level_dots': level_dots
        })
    context['skills'] = skills

    # ── certifications — add year and month ──────────────────────────────────
    korea_certs = []
    for cert in context.get('certifications', []):
        if not cert.get('visible', True):
            continue
        year_str = cert.get('year', '')
        y, m, _ = parse_human_date(year_str)
        korea_certs.append({
            'year':   y,
            'month':  m if m else 1,
            'name':   cert.get('name', ''),
            'issuer': cert.get('issuer', ''),
        })
    korea_certs.sort(key=lambda x: (x['year'], x['month']))
    context['certifications'] = korea_certs

    # ── awards — filter achievements that have year + issuer ─────────────────
    awards = []
    for ach in context.get('achievements', []):
        year_raw = str(ach.get('year', ''))
        # Only items with a proper year (not empty) AND an issuer go into 수상
        if year_raw and year_raw.isdigit() and ach.get('issuer'):
            y, m, _ = parse_human_date(year_raw)
            # KR5: If year_raw is a 4-digit year-only string, month is unknown → None
            # The template uses {% if award.month %} so None suppresses the /01 display
            month_val = None if len(year_raw) == 4 else (m if m else None)
            awards.append({
                'year':   y,
                'month':  month_val,
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
        is_en = context.get('lang') == 'en'
        
        projects_out.append({
            'name':      p.get('name', ''),
            'period':    p.get('period', ''),
            'team_size': ('Individual' if is_en else '개인') if 'individual' in team_size.lower() else team_size,
            'tech':      tech,
            'role':      (('Developer' if is_en else '개발자') if not role.strip() or 'developer' in role.lower() else role),
            'summary':   p.get('summary') or p.get('description', ''),
        })
    context['projects'] = projects_out

    # ── research ──────────────────────────────────────────────────────────────
    research_out = []
    # FIX: Ensure we don't accidentally pull cover letter content here
    raw_research = context.get('research', [])
    if isinstance(raw_research, dict): raw_research = [raw_research] # safety
    
    # Get labels for localization
    L = get_labels(context.get('lang', 'en'))
    
    for r in raw_research:
        if not isinstance(r, dict) or not r.get('visible', True):
            continue
        # Localize research status
        raw_status = r.get('status', 'Writing')
        status_localized = L.get('writing_status', raw_status) if raw_status.lower() in ('writing', 'in progress', '執筆中', '작성 중', '进行中') else raw_status
        
        research_out.append({
            'title':       r.get('title', ''),
            'status':      status_localized,
            'year':        r.get('year', '2026'),
            'description': r.get('description', ''),
        })
    context['research'] = research_out

    # ── cover_letter — defaults ───────────────────────────────────────────────
    cl = context.get('cover_letter', {})
    is_ko = context.get('lang') == 'ko'
    
    def _formalize_korean_cl(text: str) -> str:
        if not text:
            return text
        text = text.replace('영어를 계속 배우면서', '한국어를 계속 공부하면서')
        text = text.replace('영어를 배우면서', '한국어를 공부하면서')
        for informal, formal in (
            ('나는', '저는'), ('내가', '제가'), ('나의', '제'), ('나를', '저를'),
            ('나에게', '저에게'), ('내 ', '제 '),
        ):
            text = text.replace(informal, formal)
        return text

    context['cover_letter'] = cl
    if is_ko:
        cl_out = context['cover_letter']
        for key in ('growth_background', 'strengths_weaknesses', 'motivation', 'goals_after_joining'):
            if cl_out.get(key):
                cl_out[key] = _formalize_korean_cl(cl_out[key])

    return context


def _calc_china_duration(start_year: int, start_month: int, end_year: int, end_month: int, is_current: bool = False, lang: str = 'zh', inclusive: bool = False) -> str:
    """Returns localized duration string (e.g., '1年3个月' or '1 yr 3 mo')."""
    total_months = (end_year - start_year) * 12 + (end_month - start_month)
    if inclusive:
        total_months += 1
    if total_months < 0:
        total_months = 0
    years = total_months // 12
    months = total_months % 12
    
    is_en = lang == 'en'
    y_label = " yr" if is_en else "年"
    m_label = " mo" if is_en else "个月"
    
    parts = []
    if years > 0:
        parts.append(f"{years}{y_label}")
    if months > 0:
        parts.append(f"{months}{m_label}")
    
    if not parts:
        return f"1{m_label}"
    return (" " if is_en else "").join(parts)


def build_china_context(data: dict) -> dict:
    """Builds enriched context for Chinese 简历 template."""
    import copy
    from datetime import datetime
    context = copy.deepcopy(data)
    context['L'] = get_labels(context.get('lang', 'zh'))
    today = datetime.today()

    profile = context.get('profile', {})
    apply_phone_display(profile)
    email = (profile.get('email') or '').strip()
    if email.lower().startswith('mailto:'):
        profile['email'] = email[7:].strip()
    
    # ── generated_date in localized format ─────────────────────────────────────
    is_zh = context.get('lang') == 'zh'
    if is_zh:
        context['generated_date'] = f"{today.year}年{today.month}月{today.day}日"
    else:
        context['generated_date'] = today.strftime('%Y/%m/%d')

    # ── profile.address alias ─────────────────────────────────────────────────
    if not profile.get('address'):
        profile['address'] = profile.get('location', '')

    # ── personal sub-context for template ────────────────────────────────────
    raw_personal = profile.get('personal', {})
    
    # DOB Formatting
    dob_raw = raw_personal.get('dob') or profile.get('dateOfBirth', '')
    dob_zh = ''
    if dob_raw:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                dob = datetime.strptime(dob_raw, fmt)
                if context.get('lang') == 'zh':
                    dob_zh = f"{dob.year}年{dob.month}月{dob.day}日"
                else:
                    dob_zh = f"{dob.year}/{dob.month:02d}/{dob.day:02d}"
                break
            except ValueError:
                continue

    is_en = context.get('lang') == 'en'
    gender_raw = raw_personal.get('gender', '').lower()
    if gender_raw.startswith('f'):
        gender_display = 'Female' if is_en else '女'
    elif gender_raw.startswith('m'):
        gender_display = 'Male' if is_en else '男'
    else:
        gender_display = ''

    raw_status = raw_personal.get('marital_status', '').lower()
    L = get_labels(context.get('lang', 'en'))
    if 'married' in raw_status:
        marital_display = L.get('married', 'Married')
    elif 'single' in raw_status or 'unmarried' in raw_status:
        marital_display = L.get('single', 'Single')
    else:
        marital_display = raw_personal.get('marital_status', '')

    # Check if candidate is overseas (address does not contain China/中国)
    location_lower = (profile.get('location') or profile.get('address') or '').lower()
    is_overseas = not ('china' in location_lower or '中国' in location_lower)

    context['personal'] = {
        'gender':        gender_display,
        'dob':           dob_zh,
        'nationality':   '印度' if context.get('lang') == 'zh' else 'India',
        'visa_status':   (
            (context.get('personal') or {}).get('visa_status', '').strip()
            or resolve_region_visa_status(
                profile.get('visa', {}),
                'CN',
                context.get('lang', 'zh'),
            )
        ),
        'marital_status': marital_display,
        'summary':       profile.get('summary', ''),
        'hobbies':       raw_personal.get('hobbies', ''),
        'is_overseas':   is_overseas,
    }

    # Use pre-translated Chinese summary when available
    if context.get('lang') == 'zh' and profile.get('summary_zh'):
        profile['summary'] = profile['summary_zh']
    summary = profile.get('summary', '')
    if summary:
        summary = summary.replace("专注于医疗AI及生物医学 signal 处理", "专注于医疗AI及生物医学信号处理")
        summary = summary.replace("专注于医疗AI及生物医学signal处理", "专注于医疗AI及生物医学信号处理")
        summary = summary.replace("全能力栈", "完整技术能力").replace("全栈能力", "完整技术能力")
        profile['summary'] = summary.replace("Japan's", "China's").replace("Japanese", "Chinese").replace("Japan", "China")
    if context.get('lang') == 'zh':
        context['personal']['summary'] = profile.get('summary', '')

    connections = context.get('connections', [])
    filtered = [
        c for c in connections
        if c.get('visible', True) and c.get('url', '').strip()
    ]
    context['connections'] = filtered

    # ── education ─────────────────────────────────────────────────────────────
    for edu in context.get('education', []):
        year_str = edu.get('year', '')
        import re
        month_map = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}
        def parse_edu_year(s):
            s = s.lower().strip()
            year_match = re.search(r'(\d{4})', s)
            year = int(year_match.group(1)) if year_match else 2000
            month = 4
            for name, val in month_map.items():
                if name in s: month = val; break
            return year, month

        parts = re.split(r'[–\-\—]', year_str)
        try:
            sy, sm = parse_edu_year(parts[0])
            if len(parts) > 1:
                ey_str = parts[1].strip()
                is_current = ey_str.lower() in ('', 'present', 'current')
                if is_current: ey, em = today.year, today.month
                else: ey, em = parse_edu_year(ey_str)
            else: ey, em, is_current = sy + 4, 3, False
        except Exception:
            sy, sm, ey, em, is_current = 2000, 4, 2004, 3, False

        edu['start_year']  = sy
        edu['start_month'] = sm
        edu['end_year']    = ey
        edu['end_month']   = em
        edu['duration']    = _calc_china_duration(sy, sm, ey, em, is_current, context.get('lang'), inclusive=True)
        edu['start']       = (sy, sm)

        if 'university' in edu and 'institution' not in edu:
            edu['institution'] = edu['university']

        # Clean GPA double label (Issue 1)
        gpa = edu.get('gpa', '')
        if gpa:
            cleaned = re.sub(r'(?i)\bCGPA\b', '', gpa).strip()
            cleaned = re.sub(r'\s+', ' ', cleaned)
            edu['gpa'] = cleaned

    # ── experience ────────────────────────────────────────────────────────────
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
        exp['duration']    = _calc_china_duration(sy, sm, ey, em, is_current, context.get('lang'))
        
        # Employment Type
        is_en = context.get('lang') == 'en'
        etype_raw = (exp.get('employment_type') or '').lower()
        company_raw = (exp.get('company') or '').lower()
        role_raw = (exp.get('role') or '').lower()
        if ('freelance' in etype_raw or 'freelance' in company_raw
                or 'freelance' in role_raw or '自由职业' in company_raw):
            exp['employment_type_zh'] = 'Freelance' if is_en else '自由职业'
        elif 'contract' in etype_raw:
            exp['employment_type_zh'] = 'Contract' if is_en else '合同工'
        else:
            exp['employment_type_zh'] = 'Full-time' if is_en else '全职'

        # status labels
        L = get_labels(context.get('lang', 'zh'))
        exp['status_label'] = (L.get('current', 'Current') if exp['is_current'] else L.get('left', 'Resigned'))

    # ── languages ────────────────────────────────────────────────────────────
    pct_to_dots = [(90, 5), (70, 4), (50, 3), (30, 2), (0, 1)]
    is_zh = context.get('lang') == 'zh'
    level_label_map = {
        'native': '母语' if is_zh else 'Native',
        'fluent / professional': '流利 / 专业' if is_zh else 'Fluent / Professional',
        'business level': '商务水平' if is_zh else 'Business Level',
        'advanced': '精通' if is_zh else 'Advanced',
        'intermediate': '中级' if is_zh else 'Intermediate',
        'basic': '基础' if is_zh else 'Basic',
        'beginner': '初级' if is_zh else 'Beginner',
        'beginner (currently learning)': '初级 (学习中)' if is_zh else 'Beginner (Currently Learning)'
    }
    
    raw_langs = list(context.get('languages', []))
    has_chinese = any(l.get('name', '').lower() in ('chinese', 'mandarin', '中文') for l in raw_langs)
    if not has_chinese:
        raw_langs.append({
            "id": "lang_cn",
            "name": "中文" if is_zh else "Mandarin Chinese",
            "level": "beginner (currently learning)",
            "percentage": 10,
            "visible": True,
            "order": 5
        })

    china_langs = []
    region_lower = (context.get('region') or data.get('region', 'china')).lower()
    for lang in raw_langs:
        if not lang.get('visible', True): continue
        name_lower = lang.get('name', '').lower()
        
        # Core languages always visible
        if name_lower in ('english', 'hindi', 'mandarin chinese', 'chinese', 'mandarin', '中文'):
            is_relevant = True
        # Regional languages only show for their region
        elif name_lower in ('japanese', '日本語'):
            is_relevant = region_lower == 'japan'
        elif name_lower in ('korean', '한국어'):
            is_relevant = region_lower == 'korea'
        else:
            is_relevant = lang.get('visible', True)
            
        if not is_relevant:
            continue
            
        pct = lang.get('percentage', 50)
        dots = 1
        for threshold, d in pct_to_dots:
            if pct >= threshold:
                dots = d
                break
        raw_level = lang.get('level', '').lower()
        label = level_label_map.get(raw_level, lang.get('level', ''))
        china_langs.append({
            'name':        lang['name'],
            'level_dots':  dots,
            'level_label': label,
            'cert':        lang.get('cert', ''),
            'note':        lang.get('note', '')
        })
    context['languages'] = china_langs

    # ── skills ───────────────────────────────────────────────────────────────
    skills_out = []
    for cat in context.get('skillCategories', []):
        if not cat.get('visible', True): continue
        # Check if custom level is set on category
        raw_level = cat.get('level', '')
        if raw_level:
            from services.translations import PROFICIENCY_LEVELS
            lang_key = context.get('lang', 'zh')
            if lang_key == 'cn': lang_key = 'zh'
            if lang_key not in ["en", "ja", "ko", "zh"]: lang_key = "en"
            
            raw_lower = str(raw_level).lower()
            if raw_lower in PROFICIENCY_LEVELS.get("en", {}):
                calc_level = PROFICIENCY_LEVELS.get(lang_key, {}).get(raw_lower, raw_level)
            else:
                calc_level = raw_level
        else:
            # Automatically calculate proficiency based on years of experience
            calc_level = calculate_proficiency(cat.get("years", ""), context.get('lang', 'zh'))

        # Map word-based level back to dots for the visual template
        level_dots = 4
        if "expert" in calc_level.lower() or "专家" in calc_level: level_dots = 5
        elif "advanced" in calc_level.lower() or "精通" in calc_level or "高级" in calc_level: level_dots = 5
        elif "experienced" in calc_level.lower() or "经验" in calc_level or "熟练" in calc_level: level_dots = 4
        elif "intermediate" in calc_level.lower() or "中级" in calc_level: level_dots = 3
        else: level_dots = 2

        is_en = context.get('lang') == 'en'
        skills_out.append({
            'name':  cat.get('label', cat.get('name', '')),
            'items': cat.get('items', []),
            'level': calc_level,
            'level_dots': level_dots
        })
    context['skills'] = skills_out

    # ── awards & certifications ──────────────────────────────────────────────
    awards = []
    for ach in context.get('achievements', []):
        awards.append({
            'name': ach.get('title', ''),
            'issuer': ach.get('issuer', ''),
            'year': ach.get('year', '')
        })
    context['awards'] = awards
    
    certs = []
    for c in context.get('certifications', []):
        certs.append({
            'name': c.get('name', ''),
            'issuer': c.get('issuer', ''),
            'year': c.get('year', '')
        })
    context['certifications'] = certs

    # ── projects ─────────────────────────────────────────────────────────────
    projects_out = []
    is_en = context.get('lang') == 'en'
    for p in context.get('projects', []):
        if p.get('hidden'): continue
        tech = p.get('techStack') or p.get('tech') or ''
        if isinstance(tech, list): tech = '、'.join(tech)
        # CN2: Use the English name and description — don't rely on translated/truncated values
        proj_name = p.get('name', '')
        proj_summary = p.get('summary') or p.get('description', '')
        # Fallback: if name looks truncated (len < 3), use full english name from data
        if not proj_name or len(proj_name.strip()) < 3:
            proj_name = p.get('full_name', p.get('name', ''))
        projects_out.append({
            'name':      proj_name,
            'period':    p.get('period', ''),
            'team_size': p.get('team_size', L.get('individual', 'Individual') if is_en else '个人'),
            'tech':      tech,
            'role':      p.get('role') or (L.get('developer', 'Developer') if is_en else '开发者'),
            'summary':   proj_summary
        })
    context['projects'] = projects_out

    # ── research ─────────────────────────────────────────────────────────────
    research_out = []
    for r in context.get('research', []):
        # Issue 10 / CN: Localize status "Writing" → "进行中" (or EN equivalent)
        raw_status = r.get('status', 'Writing')
        if raw_status.lower() in ('writing', 'in progress'):
            status_loc = L.get('writing_status', raw_status)
        else:
            status_loc = raw_status
        research_out.append({
            'title': r.get('title', ''),
            'status': status_loc,
            'year': r.get('year', '2026'),
            'description': r.get('description', '')
        })
    context['research'] = research_out

    # ── cover_letter — defaults ───────────────────────────────────────────────
    cl = context.get('cover_letter', {})
    is_zh = context.get('lang') == 'zh'
    
    context['cover_letter'] = {
        **cl,
        'growth_background':   cl.get('growth_background',   '我一直对软件技术如何积极地改变世界深感着迷，并一直致力于通过建立稳健的实际工程技能来促进自己的成长。' if is_zh else 'I have always been deeply fascinated by how software technology positively impacts the world, focusing my growth on building robust, real-world engineering skills.'),
        'strengths_weaknesses': cl.get('strengths_weaknesses', '我的主要优势在于能够追踪并解决复杂问题的毅力，以及构建稳定的后端和实时人工智能模型的能力。' if is_zh else 'My primary strength lies in my persistence to trace and solve complex problems, coupled with a strong capacity to architect stable backends and real-time AI models.'),
        'motivation':          cl.get('motivation',           '我非常希望能在贵公司领先的技术业务生态系统中，充分利用我的高性能 API 设计和 AI/ML 解决方案工程能力，为贵公司的发展做出贡献。' if is_zh else 'I am highly motivated to leverage my high-performance API design and AI/ML solution engineering capabilities within your pioneering technical business ecosystem.'),
        'goals_after_joining': cl.get('goals_after_joining',  '入职后，我旨在通过带头进行后端优化和微调稳健的机器学习模型，成功管理大规模流量并加速创新。' if is_zh else 'Upon joining, I aim to accelerate innovation and successfully manage large-scale traffic by spearheading backend optimizations and fine-tuning robust machine learning models.'),
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

async def translate_cover_letter_paragraphs(content: str, target_lang: str) -> str:
    """Helper to translate cover letter paragraphs concurrently to avoid length limits/timeouts."""
    if not content:
        return content
    from services.translations import translate_text
    from services.cover_letter_service import _to_prose_paragraphs, _polish_cover_letter_body
    prose = _to_prose_paragraphs(content)
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', prose) if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    translated_parts = await asyncio.gather(*[
        translate_text(p, target_lang, field_name="cover_letter_para") for p in paragraphs
    ])
    body = '\n\n'.join(translated_parts)
    return _polish_cover_letter_body(body, f"_{target_lang.upper()}")

async def generate_resume_playwright(data, live_projects=None, region="international", include_photo=False, return_html=False, lang="en", include_cover=False):
    """Generate Resume PDF using Jinja2 and Playwright."""
    import copy
    data = copy.deepcopy(data)
    if live_projects is not None:
        live_projects = copy.deepcopy(live_projects)

    # Defensive placeholder filter
    placeholder_patterns = ['test', 'testa', '测试', '테스트', 'temp', 'placeholder']
    if 'certifications' in data:
        data['certifications'] = [
            c for c in data['certifications']
            if not any(p in (c.get('name') or '').lower() or p in (c.get('issuer') or '').lower() for p in placeholder_patterns)
        ]
    if 'achievements' in data:
        data['achievements'] = [
            a for a in data['achievements']
            if not any(p in (a.get('title') or '').lower() or p in (a.get('issuer') or '').lower() for p in placeholder_patterns)
        ]
    
    # 1. Prepare View Data
    profile = data.get('profile', {}).copy()   # single copy, keep it

    # Strip "Aspiring" from Japanese resume personal fields
    personal_data = profile.get('personal', {})
    for key in ('self_pr_ja', 'self_pr_ja_detailed', 'career_summary_ja'):
        val = personal_data.get(key, '')
        if isinstance(val, str) and 'aspiring' in val.lower():
            personal_data[key] = re.sub(r'\bAspiring\s*', '', val, flags=re.IGNORECASE).strip()

    # Remove underselling "Aspiring" title wording
    for key in ('role', 'summary', 'bio'):
        val = profile.get(key, '')
        if isinstance(val, str) and 'aspiring' in val.lower():
            profile[key] = re.sub(r'\bAspiring\s*', '', val, flags=re.IGNORECASE).strip()
    if not profile.get('role'):
        profile['role'] = 'AI/ML Engineer'
    
    # Strip years of experience mentions from summary (highly requested)
    summary_raw = profile.get('summary', '')
    if summary_raw:
        patterns = [
            r'\b(?:with|having)?\s*(?:over|more than)?\s*\d+\+?\s*years?\s*of\s*(?:professional\s*)?experience\s*\b',
            r'\b(?:with|having)?\s*(?:over|more than)?\s*\d+\+?\s*years?\s*\b',
            r'\b\d+\+?\s*개년\b',
            r'\b\d+\+?\s*년\b',
            r'\b\d+\+?\s*年\b',
        ]
        for pattern in patterns:
            summary_raw = re.sub(pattern, ' ', summary_raw, flags=re.IGNORECASE)
        summary_raw = re.sub(r'\s{2,}', ' ', summary_raw).strip()
        profile['summary'] = summary_raw

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

    apply_phone_display(profile)
            
    # 1.5 G1: Dynamic summary sentence — inject language_study + target_ecosystem per region
    region_key_map = {
        'japan': 'JP', 'japan_english': 'JP_EN',
        'korea': 'KR', 'korea_english': 'KR_EN',
        'china': 'CN', 'china_english': 'CN_EN',
        'germany': 'DE', 'uk': 'UK', 'usa': 'US',
        'india': 'IN', 'uae': 'AE', 'middleeast': 'AE', 'international': 'GLOBAL'
    }
    region_key = region_key_map.get(region, 'GLOBAL')
    lang_study_map  = personal.get('language_study_en', {})
    ecosystem_map   = personal.get('target_ecosystem', {})
    view_data_language_study  = lang_study_map.get(region_key)
    view_data_target_ecosystem = ecosystem_map.get(region_key, 'the global AI research and healthcare technology ecosystem')

    # G2: Dynamic experience years (Logixbuilt start: March 2022)
    experience_years = calculate_experience_years(2022, 3)

    # G10: Visa statement injection
    visa_map = profile.get('visa', {})
    visa_statement = resolve_region_visa_status(
        visa_map,
        region_key,
        lang,
        existing=personal.get('visa_status') or personal.get('visa_type') or profile.get('visa_info', {}).get('visaType', '') or '',
    )

    summary = profile.get('summary', '')

    # Map furigana to profile so template can access them easily
    profile['name_furigana'] = personal.get('name_furigana', '')
    profile['address_furigana'] = personal.get('address_furigana', '')
    
    # FIX: Prioritize 'location' over 'address' to prevent Tokyo address leak from data.json
    if profile.get('location'):
        profile['address'] = profile.get('location')
    elif not profile.get('address'):
        profile['address'] = ""

    # Consolidate Visa Status for Global Integration
    personal['visa_status'] = visa_statement

    # Calculate Japanese Era (Reiwa started May 1, 2019)
    # Simple calculation for current year
    reiwa_year = today.year - 2018
    
    enriched_experience = enrich_experience(data.get('experience', []))
    # ── Parallel execution of AI-heavy tasks ────────────────────────────
    cl_task = None
    manual_cover_content = ""
    is_manual_cover = False
    
    if include_cover:
        reg_cl = data.get('regional_cover_letters', {})
        cl = data.get('cover_letter', {})
        
        # Resolve any manual cover letter text
        if region == 'middleeast':
            lookup_region = 'uae'
        elif region == 'international':
            lookup_region = 'global'
        else:
            lookup_region = region
        specific_native = reg_cl.get(f"{lookup_region}_{lang}", "").strip()
        regional_base = reg_cl.get(lookup_region, "").strip()
        global_content = cl.get('content', "").strip()
        
        growth = cl.get('growth_background', "") or ""
        strengths = cl.get('strengths_weaknesses', "") or ""
        motivation = cl.get('motivation', "") or ""
        goals = cl.get('goals_after_joining', "") or ""
        merged_sections = "\n\n".join(filter(None, [growth, strengths, motivation, goals])).strip()
        
        # Decide if we have a manual cover letter
        # We only treat it as a manual cover letter if the text is long (>= 500 chars),
        # meaning the user has written/customized it, rather than it being a short default stub.
        if specific_native and len(specific_native) >= 500:
            manual_cover_content = specific_native
            is_manual_cover = True
        elif (regional_base or global_content or merged_sections) and len(regional_base or global_content or merged_sections) >= 500:
            manual_cover_content = regional_base or global_content or merged_sections
            is_manual_cover = True
            # If target language is not English and we fall back to an English manual letter, JIT-translate it!
            if lang != 'en':
                cl_task = asyncio.create_task(translate_cover_letter_paragraphs(manual_cover_content, lang))
        
        # If no manual cover letter exists, only then generate dynamically using Groq LLM
        if not is_manual_cover:
            from services.cover_letter_service import generate_dynamic_cover_letter
            cl_task = asyncio.create_task(generate_dynamic_cover_letter(region, lang, data))
    
    # Summary Translation Task
    summary_task = None
    pre_translated_summary = profile.get(f'summary_{lang}')
    if pre_translated_summary:
        profile['summary'] = pre_translated_summary
        summary_task = 'pre_translated'
    elif lang != 'en' and summary:
        from services.translations import translate_text
        # JP-NEW6: For specialty regions (JP/KR/CN), do NOT require verified_only —
        # fall back to Google Translate so the summary always appears in the target language
        is_specialty = region in ('japan', 'korea', 'china')
        summary_task = asyncio.create_task(
            translate_text(summary, lang, field_name="profile_summary", verified_only=not is_specialty)
        )

    # Gather all results
    tasks = [enrich_projects(live_projects)]
    if cl_task: tasks.append(cl_task)
    if summary_task and summary_task != 'pre_translated': tasks.append(summary_task)

    # Gather all results with exception handling
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as gather_err:
        print(f"Gather Error: {gather_err}")
        results = [[]] + [None] * (len(tasks)-1)

    # ── Robust Mapping of Results ──────────────────────────────────────────
    # Task 0 is always enrich_projects
    enriched_projects = results[0] if not isinstance(results[0], Exception) else []
    ai_letter = None
    
    res_ptr = 1
    if cl_task:
        res_val = results[res_ptr]
        ai_letter = res_val if not isinstance(res_val, Exception) else None
        res_ptr += 1
    if summary_task and summary_task != 'pre_translated':
        res_val = results[res_ptr]
        if not isinstance(res_val, Exception) and res_val:
            profile['summary'] = res_val
        res_ptr += 1

    # Clean experience years from final summary (G6, CN1, KR1)
    # Clean experience years from final summary and PR fields (G6, CN1, KR1, JP-NEW7)
    def clean_years(text):
        if not text or not isinstance(text, str):
            return text
        s_patterns = [
            # English
            r'(?<!\d)\d{1,2}\+?\s*years?\s*of\s*(?:professional\s*)?experience',
            r'(?<!\d)\d{1,2}\+?\s*years?',
            # Korean
            r'(?<!\d)\d{1,2}년\s*(?:이상|반|간)?\s*(?:의)?\s*(?:실무\s*)?경험을\s*(?:보유한|가진|지닌|보유)?',
            r'(?<!\d)\d{1,2}년\s*(?:이상|반|간)?\s*(?:의)?\s*(?:실무\s*)?경험',
            r'(?<!\d)\d{1,2}년\s*(?:이상|반|간)?\s*(?:의)?\s*(?:경력|경험)',
            r'(?<!\d)\d{1,2}\+?\s*개년',
            r'(?<!\d)\d{1,2}\+?\s*년',
            # Chinese
            r'拥有\s*(?<!\d)\d{1,2}\s*年\s*(?:的)?\s*(?:机器学习系统)?开发经验',
            r'拥有\s*(?<!\d)\d{1,2}\s*年\s*(?:的)?\s*(?:工作)?经验',
            r'拥有\s*(?<!\d)\d{1,2}\s*年\s*(?:的)?\s*经验',
            r'(?<!\d)\d{1,2}\+?\s*年',
            # Japanese
            r'(?<![令和平成昭和\d])\d{1,2}\+?\s*年\s*(?:以上)?\s*(?:の)?\s*(?:実務)?経験',
            r'(?<![令和平成昭和\d])\d{1,2}\+?\s*年\s*(?:以上)?\s*(?:の)?\s*実務経験',
            r'(?<![令和平成昭和\d])\d{1,2}\+?\s*年\s*(?:以上)?\s*(?:の)?\s*経験',
            r'(?<![令和平成昭和\d])\d{1,2}\+?\s*年',
        ]
        s_text = text
        for pattern in s_patterns:
            s_text = re.sub(pattern, ' ', s_text, flags=re.IGNORECASE)
        s_text = re.sub(r'\s{2,}', ' ', s_text)
        s_text = s_text.replace("，，", "，").replace(",,", ",").replace(", ,", ",")
        s_text = re.sub(r'，\s*，', '，', s_text)
        s_text = re.sub(r',\s*,', ',', s_text)
        return s_text.strip()

    if profile.get('summary'):
        profile['summary'] = clean_years(profile['summary'])
    if personal.get('summary'):
        personal['summary'] = clean_years(personal['summary'])

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
        'include_cover': include_cover,
    }

    # Handle Cover Letter Result
    if include_cover:
        if ai_letter:
            html_letter = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ai_letter)
            html_letter = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_letter)
            view_data['cover_letter'] = {
                'title': data.get('cover_letter', {}).get('title', 'Cover Letter'),
                'content': html_letter
            }
        else:
            # Fallback to static
            reg_cl = data.get('regional_cover_letters', {})
            cl = data.get('cover_letter', {})
            if region == 'middleeast':
                lookup_region = 'uae'
            elif region == 'international':
                lookup_region = 'global'
            else:
                lookup_region = region
            static_content = (reg_cl.get(f"{lookup_region}_{lang}") or reg_cl.get(lookup_region) or cl.get('content') or 
                             "\n\n".join(filter(None, [cl.get('growth_background'), cl.get('strengths_weaknesses'), cl.get('motivation'), cl.get('goals_after_joining')])))
            html_static = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', static_content)
            html_static = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_static)
            view_data['cover_letter'] = {**cl, 'content': html_static}
    else:
        view_data['cover_letter'] = {}

    view_data.update({
        'show_project_images': region not in {'international', 'academic', 'ats_usa', 'ats_uk', 'india', 'germany', 'middleeast', 'usa', 'uk', 'uae'},
        # G1: Dynamic summary sentence variables (only if applicable)
        'language_study': view_data_language_study if region in {'japan', 'korea', 'china'} else None,
        'target_ecosystem': view_data_target_ecosystem,
        # G2: Dynamic experience years
        'experience_years': experience_years,
        # G10: Visa statement
        'visa_statement': visa_statement,
        'show_extended_personal': False, # Default
    })

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
                
                # Format: 令和X年X月X日生
                vd['personal']['japanese_dob_era'] = to_japanese_era(dt.year, dt.month, dt.day) + f" {dt.month}月 {dt.day}日生"
                
                # Age calculation
                today = datetime.now()
                age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
                vd['personal']['age'] = age
            except Exception:
                vd['personal']['age'] = 28 # Fallback
        
        # JIT Labels for Japan
        if lang == 'ja':
            vd['profile']['nationality_ja'] = 'インド'
            vd['profile']['marital_status_ja'] = '未婚' if raw_personal.get('marital_status', '').lower() in ['single', 'unmarried'] else '既婚'
        
        # Employment Nature
        for exp in vd['experience']:
            etype = (exp.get('employment_type') or exp.get('employment_type_ja') or '').strip().lower()
            company = exp.get('company', '').lower()
            role = exp.get('role', '').lower()
            is_freelance = (
                'freelance' in company or 'freelancer' in company or 'フリーランス' in company or
                'freelance' in role or 'freelancer' in role or 'フリーランス' in role or
                'freelance' in etype or 'freelancer' in etype or 'フリーランス' in etype
            )
            if is_freelance:
                exp['employment_type_ja'] = vd['L'].get('freelance', 'フリーランス')
                exp['employment_type_ko'] = vd['L'].get('freelance', 'フリーランス')
            else:
                exp['employment_type_ja'] = vd['L'].get('fulltime', '正社員')
                exp['employment_type_ko'] = vd['L'].get('fulltime', '正社員')

    def process_korea(vd):
        full_time = []
        part_time = []
        for exp in vd['experience']:
            etype = exp.get('employment_type', 'Full-time').lower()
            if 'part' in etype or '알바' in etype:
                part_time.append(exp)
            else:
                full_time.append(exp)
            
            # Map JIT labels for Team Size and Role
            if lang == 'en':
                if not exp.get('role'): exp['role'] = 'Developer'
                if not exp.get('team_size'): exp['team_size'] = 'Individual'
        
        vd['experience_full'] = full_time
        vd['experience_part'] = part_time
        
        # Map Languages for English Resume
        if lang == 'en':
            for l in vd.get('languages', []):
                if '商务' in l.get('level', '') or 'Business' in l.get('level', ''):
                    l['level'] = 'Business Fluent'
                elif '母语' in l.get('level', '') or 'Native' in l.get('level', ''):
                    l['level'] = 'Native Speaker'
                elif '初级' in l.get('level', '') or 'Beginner' in l.get('level', ''):
                    l['level'] = 'Beginner (Currently Learning)'

    def process_china(vd):
        # Always set both English and Chinese versions
        # Template decides which to render based on lang
        vd['profile']['nationality_zh'] = '印度'
        vd['profile']['nationality_en'] = 'India'
        vd['profile']['marital_status_zh'] = '未婚' if raw_personal.get('marital_status', '').lower() in ['single', 'unmarried'] else '已婚'
        vd['profile']['marital_status_en'] = 'Single' if raw_personal.get('marital_status', '').lower() in ['single', 'unmarried'] else 'Married'
        
        # Date of Birth with day
        dob_str = vd['profile'].get('dateOfBirth') or raw_personal.get('dob')
        if dob_str:
            try:
                dt = datetime.strptime(dob_str, "%Y-%m-%d") if '-' in dob_str else datetime.strptime(dob_str, "%d/%m/%Y")
                vd['personal']['china_dob'] = f"{dt.year}年{dt.month}月{dt.day}日"
            except: pass
        
        # Language Mapping for China English
        if lang == 'en':
            for l in vd.get('languages', []):
                if '商务' in l.get('level', '') or 'Business' in l.get('level', ''):
                    l['level'] = 'Business Fluent'
                elif '母语' in l.get('level', '') or 'Native' in l.get('level', ''):
                    l['level'] = 'Native Speaker'



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

        # India specific labels
        if region == 'india':
            vd['L']['notice_period_label'] = 'Notice Period'
            vd['L']['cgpa_label'] = 'CGPA'
        
        # UAE/Germany personal blocks - show extended personal details only for UAE/Middle East
        if region in {'middleeast', 'uae'}:
            vd['show_extended_personal'] = True
        else:
            vd['show_extended_personal'] = False

        # Filter skillCategories by visible flag
        if 'skillCategories' in vd:
            vd['skillCategories'] = [
                cat for cat in vd['skillCategories']
                if cat.get('visible', True)
            ]
            
        # Neutralize Japan-specific references in summary for non-Asian resumes
        prof = vd.get('profile', {})
        summary = prof.get('summary', '')
        if summary:
            summary = summary.replace("actively studying Japanese, with the goal of contributing to Japan's world-class AI research and healthcare technology ecosystem", "committed to contributing to world-class AI research and healthcare technology ecosystems")
            summary = summary.replace("actively studying Japanese", "committed to professional growth")
            summary = summary.replace("studying Japanese", "committed to professional growth")
            summary = summary.replace("Japan's", "global").replace("Japan", "global")
            summary = summary.replace("Japanese", "global")
            prof['summary'] = summary
            
        # Language relevance filter for international/ATS resumes
        region_lower = region.lower()
        filtered_langs = []
        for lang_item in vd.get('languages', []):
            if not isinstance(lang_item, dict):
                continue
            name_lower = lang_item.get('name', '').lower()
            # Always show English, Hindi, and Gujarati
            if name_lower in ('english', 'hindi', 'gujarati'):
                filtered_langs.append(lang_item)
            # Only show regional languages for their specific region
            elif name_lower in ('japanese', '日本語') and region_lower == 'japan':
                filtered_langs.append(lang_item)
            elif name_lower in ('korean', '한국어') and region_lower == 'korea':
                filtered_langs.append(lang_item)
            elif name_lower in ('chinese', 'mandarin', '中文') and region_lower == 'china':
                filtered_langs.append(lang_item)
            # For non-regional languages, show if visible
            elif name_lower not in ('japanese', 'korean', 'chinese', 'mandarin', '日本語', '한국어', '中文'):
                if lang_item.get('visible', True):
                    filtered_langs.append(lang_item)
        vd['languages'] = filtered_langs

    # 2. Apply processing logic
    if geo_rule.get('show_photo'):
        process_photo(view_data)

    if region == 'japan':
        process_japan(view_data)
    elif region == 'korea':
        process_korea(view_data)
    elif region == 'china':
        process_china(view_data)
    else:
        process_international(view_data)

        # UK/India/UAE Spelling Localization (JIT)
        if region in {'uk', 'india', 'uae'} and lang == 'en':
            spelling_map = {
                'specializing': 'specialising',
                'specialized': 'specialised',
                'optimization': 'optimisation',
                'optimized': 'optimised',
                'standardize': 'standardise',
                'standardized': 'standardised',
                'initialize': 'initialise',
                'initialized': 'initialised',
                'analyze': 'analyse',
                'analyzed': 'analysed',
                'center': 'centre',
                'modeling': 'modelling'
            }
            # Apply to summary
            for i, text in enumerate(view_data['about']):
                for us, uk in spelling_map.items():
                    view_data['about'][i] = view_data['about'][i].replace(us, uk)
            
            # Apply to experience bullets
            for exp in view_data['experience']:
                if exp.get('bullets'):
                    for i, b in enumerate(exp['bullets']):
                        for us, uk in spelling_map.items():
                            exp['bullets'][i] = exp['bullets'][i].replace(us, uk)
                if exp.get('description'):
                    for us, uk in spelling_map.items():
                        exp['description'] = exp['description'].replace(us, uk)
        
        # 3. JIT Translation for all sections (Batched to avoid rate limits)
    if lang != 'en':
        queue = [] # List of {"text": str, "field_name": str, "callback": function}

        def _enqueue_translation(text, field_name, callback):
            """Skip empty strings — translating '' corrupts fields (e.g. project role)."""
            if text is None:
                return
            s = str(text).strip()
            if not s:
                return
            queue.append({"text": text, "field_name": field_name, "cb": callback})
        
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
                if exp.get('resign_reason_ja'):
                    queue.append({"text": exp['resign_reason_ja'], "field_name": "exp_resign", "cb": set_field(exp, 'resign_reason_ja')})

        # Projects
        if view_data.get('live_projects'):
            for proj in view_data['live_projects']:
                def set_p(p, k): return lambda t: p.__setitem__(k, t)
                queue.append({"text": proj.get('name', ''), "field_name": "proj_name", "cb": set_p(proj, 'name')})
                queue.append({"text": proj.get('role', ''), "field_name": "proj_role", "cb": set_p(proj, 'role')})

        # Education
        if view_data.get('education'):
            for edu in view_data['education']:
                def set_e(e, k): return lambda t: e.__setitem__(k, t)
                queue.append({"text": edu.get('university', ''), "field_name": "edu_university", "cb": set_e(edu, 'university')})
                # Degree left untranslated as requested by the user
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
                queue.append({"text": ach.get('issuer', ''), "field_name": "ach_issuer", "cb": set_a(ach, 'issuer')})

        # Research
        if view_data.get('research'):
            for res in view_data['research']:
                def set_r(r, k): return lambda t: r.__setitem__(k, t)
                queue.append({"text": res.get('title', ''), "field_name": "res_title", "cb": set_r(res, 'title')})
                queue.append({"text": res.get('status', ''), "field_name": "res_status", "cb": set_r(res, 'status')})

        # Skill Categories
        if view_data.get('skillCategories'):
            for cat in view_data['skillCategories']:
                def set_c(c, k): return lambda t: c.__setitem__(k, t)
                queue.append({"text": cat.get('label', ''), "field_name": "skill_cat", "cb": set_c(cat, 'label')})

        # Cover Letter - Enqueue individual sections for translation
        cl = view_data.get('cover_letter', {})
        if cl:
            for field_key in ['growth_background', 'strengths_weaknesses', 'motivation', 'goals_after_joining']:
                if cl.get(field_key):
                    def make_cl_cb(fk): return lambda t: cl.__setitem__(fk, t)
                    queue.append({"text": cl[field_key], "field_name": f"cl_{field_key}", "cb": make_cl_cb(field_key)})

        # Projects (Manual ones)
        if view_data.get('projects'):
            for proj in view_data['projects']:
                def set_p_m(p, k): return lambda t: p.__setitem__(k, t)
                queue.append({"text": proj.get('name', ''), "field_name": "proj_name", "cb": set_p_m(proj, 'name')})
                queue.append({"text": proj.get('role', ''), "field_name": "proj_role", "cb": set_p_m(proj, 'role')})

        # Certifications
        if view_data.get('certifications'):
            for cert in view_data['certifications']:
                def set_cert(c, k): return lambda t: c.__setitem__(k, t)
                queue.append({"text": cert.get('name', ''), "field_name": "cert_name", "cb": set_cert(cert, 'name')})
                queue.append({"text": cert.get('issuer', ''), "field_name": "cert_issuer", "cb": set_cert(cert, 'issuer')})

        # Language names/levels are set in build_*_context — do not JIT-translate (corrupts Hindi etc.)

        # Profile / Personal
        if view_data.get('profile'):
            prof = view_data['profile']
            def set_prof(p, k): return lambda t: p.__setitem__(k, t)
            if prof.get('role'):
                queue.append({"text": prof['role'], "field_name": "profile_role", "cb": set_prof(prof, 'role')})
            if prof.get('summary') and not summary_task:
                queue.append({"text": prof['summary'], "field_name": "profile_summary", "cb": set_prof(prof, 'summary')})
            
            pers = view_data.get('personal') or prof.get('personal', {})
            if pers:
                def set_pers(p, k): return lambda t: p.__setitem__(k, t)
                if pers.get('self_pr_ja') and lang == 'ja':
                    queue.append({"text": pers['self_pr_ja'], "field_name": "self_pr", "cb": set_pers(pers, 'self_pr_ja')})
                if pers.get('self_pr_ja_detailed') and lang == 'ja':
                    queue.append({"text": pers['self_pr_ja_detailed'], "field_name": "self_pr_detailed", "cb": set_pers(pers, 'self_pr_ja_detailed')})
                if pers.get('career_summary_ja') and lang == 'ja':
                    queue.append({"text": pers['career_summary_ja'], "field_name": "career_summary", "cb": set_pers(pers, 'career_summary_ja')})
                if pers.get('desired_conditions_ja') and lang == 'ja':
                    queue.append({"text": pers['desired_conditions_ja'], "field_name": "desired_cond", "cb": set_pers(pers, 'desired_conditions_ja')})
                if pers.get('nationality'):
                    queue.append({"text": pers['nationality'], "field_name": "nationality", "cb": set_pers(pers, 'nationality')})
                if pers.get('summary'):
                    queue.append({"text": pers['summary'], "field_name": "pers_summary", "cb": set_pers(pers, 'summary')})
                visa_val = pers.get('visa_status', '')
                if visa_val and lang != 'en' and not is_sufficiently_translated(visa_val, lang):
                    queue.append({"text": visa_val, "field_name": "visa_status", "cb": set_pers(pers, 'visa_status')})
                if pers.get('political_status'):
                    queue.append({"text": pers['political_status'], "field_name": "political_status", "cb": set_pers(pers, 'political_status')})
                if pers.get('commute_time'):
                    queue.append({"text": pers['commute_time'], "field_name": "commute_time", "cb": set_pers(pers, 'commute_time')})
            
            if prof.get('address'):
                queue.append({"text": prof['address'], "field_name": "address", "cb": set_prof(prof, 'address')})

        # Execute Batch Translation
        if queue:
            queue = [q for q in queue if q.get("text") and str(q["text"]).strip()]
        if queue:
            batch_items = [{"text": q["text"], "field_name": q["field_name"]} for q in queue]
            translated_results = await translate_batch(batch_items, lang, verified_only=True)
            
            # Apply results back
            for i, translated_text in enumerate(translated_results):
                if return_html:
                    # Direct-Edit wrapper
                    orig = queue[i]["text"]
                    fname = queue[i]["field_name"]
                    # Use Markup to tell Jinja this is safe HTML
                    # We escape the text content and the attribute to be safe
                    safe_translated = html.escape(translated_text)
                    safe_orig = html.escape(orig)
                    wrapped = Markup(f'<span class="de-editable" data-field="{fname}" data-orig="{safe_orig}" data-lang="{lang}" contenteditable="false" title="Click to edit translation">{safe_translated}</span>')
                    queue[i]["cb"](wrapped)
                else:
                    queue[i]["cb"](translated_text)

    # 4. Process Region-Specific Logic
    if region == 'japan':
        print(f"[JAPAN RESUME] Region: {region}, Language: {lang}")
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
        
        # Apply Parkinson apostrophe replacement
        html_rirekisho = html_rirekisho.replace("Parkinson' s", "Parkinson’s").replace("Parkinson's", "Parkinson’s")
        html_shokumu = html_shokumu.replace("Parkinson' s", "Parkinson’s").replace("Parkinson's", "Parkinson’s")
        
        if return_html:
            html_content = html_rirekisho + "\n<div style='page-break-after: always; height: 20px; background: #eee;'></div>\n" + html_shokumu
        else:
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

    # Apply Parkinson apostrophe replacement
    html_content = html_content.replace("Parkinson' s", "Parkinson’s").replace("Parkinson's", "Parkinson’s")

    if return_html:
        # Inject Neural Scroll Sync Script
        sync_script = """
        <script>
            (function() {
                // --- DIRECT EDIT HANDLER ---
                document.querySelectorAll('.de-editable').forEach(el => {
                    el.addEventListener('blur', function() {
                        const newText = this.innerText.trim();
                        const origText = this.getAttribute('data-orig');
                        const fieldName = this.getAttribute('data-field');
                        const locale = this.getAttribute('data-lang');
                        
                        if (!newText || newText === this.getAttribute('data-last-saved')) return;

                        this.style.backgroundColor = 'rgba(255, 255, 0, 0.2)'; // Saving indicator
                        
                        fetch('/api/admin/translations/direct-edit/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                field_name: fieldName,
                                locale: locale,
                                original_text: origText,
                                translated_text: newText
                            })
                        })
                        .then(res => res.json())
                        .then(data => {
                            this.style.backgroundColor = 'rgba(0, 255, 0, 0.1)'; // Success
                            this.setAttribute('data-last-saved', newText);
                            setTimeout(() => { this.style.backgroundColor = ''; }, 1000);
                        })
                        .catch(err => {
                            console.error('Save failed:', err);
                            this.style.backgroundColor = 'rgba(255, 0, 0, 0.1)'; // Error
                        });
                    });
                    
                    // Simple styling to indicate it's editable
                    el.style.borderBottom = '1px dashed #ccc';
                    el.style.cursor = 'text';
                    el.style.display = 'inline-block';
                    el.style.minWidth = '20px';
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


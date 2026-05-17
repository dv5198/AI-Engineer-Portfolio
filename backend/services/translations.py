import sqlite3
import json
import os
import re
import asyncio
from typing import List, Dict, Optional, Tuple

# ─── TRANSLATION CACHE (SQLite) ────────────────────────────────────────────────
from database import get_cached_translation, save_translation

# ─── LABELS ───────────────────────────────────────────────────────────────────
LABELS = {
    "en": {
        "rirekisho_title": "Resume",
        "shokumu_title": "Job History",
        "jagi_title": "Self-Introduction / Cover Letter",
        "phonetic": "Phonetic",
        "name_label": "Full Name",
        "as_of": "as of",
        "photo": "Photo",
        "nationality": "Nationality",
        "dob": "Date of Birth",
        "age": "Age",
        "gender": "Gender",
        "male": "Male",
        "female": "Female",
        "visa": "Visa Status",
        "address": "Current Address",
        "phone": "Phone",
        "email": "Email",
        "education": "Education",
        "work_experience": "Work Experience",
        "projects": "Technical Projects",
        "research": "Research & Publications",
        "skills": "Technical Skills",
        "certifications": "Certifications",
        "awards": "Awards",
        "languages": "Languages",
        "portfolio": "Portfolio",
        "github": "GitHub",
        "linkedin": "LinkedIn",
        "role_label": "Role",
        "tech_stack_label": "Tech Stack",
        "outcomes_label": "Outcomes",
        "date_label": "Generated on:",
        "cl_growth": "Growth & Background",
        "cl_strengths": "Strengths & Weaknesses",
        "cl_motivation": "Motivation",
        "cl_goals": "Goals after Joining",
        "freelance": "Freelance",
        "fulltime": "Full-time",
        "intern": "Intern",
        "individual": "Individual",
        "developer": "Developer",
        "lead": "Lead",
        "manager": "Manager",
        "year": "Year",
        "month": "Month",
        "notice_period_label": "Notice Period",
        "notice_period_val": "Immediately available / No notice period",
        "cgpa_label": "CGPA",
        "marks_label": "Marks",
        "experience_suffix": "Years",
        "category_label": "Category",
        "proficiency_label": "Proficiency",
        "skills_tools_label": "Skills & Tools",
        "experience_years_label": "Years",
        "proj_name_label": "Project Name",
        "period_label": "Period",
        "type_label": "Employment Type",
        "team_size_label": "Team Size",
        "marital_status": "Marital Status",
        "wishes": "Desired Conditions / Requests",
        "single": "Single",
        "married": "Married",
        "rirekisho_end": "End of Document",
        "certificates": "Certifications & Licenses",
        "hobbies": "Hobbies & Special Skills",
        "summary": "Professional Summary",
        "contact": "Contact Info",
        "age_suffix": " years old",
        "in": "in",
        "cover_letter_title": "Cover Letter",
        "salutation": "Dear Hiring Manager,",
        "valediction": "Best regards,",
        "remarks_label": "Remarks",
        "cert_exam_label": "Certification/Exam",
        "generated_at": "Created on",
        "page_x_of_y": "Page {x} of {y}",
        "resignation_reason": "Resigned for personal reasons",
        "experience_label": "Experience",
        "experience": "Work Experience",
        "approx_prefix": "Approx. ",
        "contact_alt_label": "Alternate Contact",
        "contact_alt": "Alternate Contact",
        "same_as_above": "Same as above",
        "entry": "Entered",
        "grad": "Graduated",
        "left": "Resigned",
        "joining": "Joined",
        "resignation": "Resigned",
        "current": "Current",
        "cl_header": "Submission of Application Documents",
        "self_pr_label": "Self-PR / Summary",
        "commute_time_label": "Commute Time",
        "dependents_label": "Dependents (excluding spouse)",
        "people_count": " person(s)",
        "spouse_label": "Spouse",
        "spouse_dependency_label": "Spousal Support Obligation",
        "desired_conditions_label": "Desired Conditions / Requests",
        "instructions_label": "All information above is true and correct.",
        "end_of_doc": "End of Document",
        "applicant_label": "Applicant:",
        "stamp_label": "(Seal/Signature)",
        "confirmation_text": "I hereby certify that the above statements are true and correct."
    },
    "ja": {
        "rirekisho_title": "履 歴 書",
        "shokumu_title": "職務経歴書",
        "as_of": "現在",
        "phonetic": "ふりがな",
        "name_label": "氏 名",
        "photo": "写真を貼る位置",
        "male": "男",
        "female": "女",
        "education": "学 歴",
        "work_experience": "職 歴",
        "rirekisho_end": "以 上",
        "certificates": "免許・資格",
        "awards": "受賞歴",
        "research": "研究・発表",
        "skills": "スキル・知識",
        "hobbies": "趣味・特技",
        "jagi_title": "自己紹介書",
        "motivation": "志望動機・特技・好きな学科など",
        "wishes": "本人希望記入欄（特に給料・職種・勤務時間・勤務地・入社時期等に関する希望があれば記入）",
        "date_label": "作成日:",
        "freelance": "フリーランス",
        "individual": "個人",
        "developer": "開発者",
        "summary": "職務要約",
        "contact": "連絡先",
        "visa": "ビザ状況",
        "gender": "性別",
        "nationality": "国籍",
        "phone": "電話番号",
        "email": "メールアドレス",
        "address": "住所",
        "dob": "生年月日",
        "age": "年齢",
        "age_suffix": "歳",
        "marital_status": "配偶者",
        "in": "にて",
        "cover_letter_title": "添え状",
        "salutation": "採用担当者様",
        "valediction": "敬具",
        "role_label": "役割",
        "type_label": "雇用形態",
        "team_size_label": "チーム規模",
        "proj_name_label": "プロジェクト名",
        "period_label": "期間",
        "tech_stack_label": "使用技術",
        "outcomes_label": "職務内容・成果",
        "remarks_label": "備考",
        "cert_exam_label": "資格・試験",
        "generated_at": "作成日",
        "page_x_of_y": "{x} / {y} ページ",
        "year": "年",
        "month": "月",
        "notice_period_label": "入社可能時期",
        "notice_period_val": "即時入社可能（離職中のため）",
        "cgpa_label": "成績(CGPA)",
        "marks_label": "点数",
        "resignation_reason": "一身上の都合により退社",
        "experience_label": "実務経験あり",
        "category_label": "カテゴリ",
        "proficiency_label": "熟練度",
        "skills_tools_label": "スキル・ツール",
        "experience_years_label": "経験年数",
        "single": "未婚",
        "married": "既婚"
    },
    "ko": {
        "rirekisho_title": "이 력 서",
        "shokumu_title": "경력기술서",
        "jagi_title": "자 기 소 개 서",
        "name_label": "성 명",
        "phonetic": "성 명(영문)",
        "dob": "생년월일",
        "age": "연령",
        "gender": "성별",
        "address": "주 소",
        "contact": "연락처",
        "phone": "전화번호",
        "email": "이메일",
        "photo": "사 진",
        "education": "학 력 사 항",
        "work_experience": "경 력 사 항",
        "certificates": "자격 및 면허",
        "awards": "수상 경력",
        "skills": "보유 기술",
        "languages": "어학 능력",
        "research": "연구 및 프로젝트",
        "date_label": "작성일:",
        "cl_growth": "성장과정",
        "cl_strengths": "성격의 장단점",
        "cl_motivation": "지원동기",
        "cl_goals": "입사 후 포부",
        "visa": "비자 상태",
        "nationality": "국적",
        "role_label": "담당 역할",
        "tech_stack_label": "사용 기술",
        "outcomes_label": "주요 성과",
        "freelance": "프리랜서",
        "fulltime": "정규직",
        "individual": "개인",
        "developer": "개발자",
        "cgpa_label": "학점(CGPA)",
        "marks_label": "점수",
        "notice_period_label": "입사 가능일",
        "notice_period_val": "즉시 입사 가능",
        "approx_prefix": "약 ",
        "category_label": "분류",
        "proficiency_label": "숙련도",
        "skills_tools_label": "기술 및 도구",
        "experience_years_label": "경력 연수",
        "proj_name_label": "프로젝트명",
        "period_label": "기간",
        "type_label": "고용 형태",
        "team_size_label": "팀 규모",
        "marital_status": "혼인 여부",
        "wishes": "희망 조건 및 요구 사항",
        "single": "미혼",
        "married": "기혼"
    },
    "zh": {
        "rirekisho_title": "个 人 简 历",
        "shokumu_title": "工作经历",
        "jagi_title": "自 荐 信",
        "name_label": "姓名",
        "phonetic": "英文姓名",
        "dob": "出生日期",
        "age": "年龄",
        "gender": "性别",
        "address": "居住地址",
        "contact": "联系方式",
        "phone": "手机号码",
        "email": "电子邮箱",
        "photo": "照片",
        "education": "教育背景",
        "work_experience": "工作经历",
        "certificates": "专业证书",
        "awards": "获奖荣誉",
        "skills": "专业技能",
        "languages": "语言能力",
        "research": "研究与项目",
        "generated_at": "创建日期",
        "date_label": "创建日期:",
        "visa": "签证状态",
        "nationality": "国籍",
        "role_label": "担任角色",
        "tech_stack_label": "技术栈",
        "outcomes_label": "工作成果",
        "freelance": "自由职业",
        "fulltime": "全职",
        "individual": "个人",
        "developer": "开发人员",
        "cgpa_label": "平均分(CGPA)",
        "marks_label": "分数",
        "notice_period_label": "到岗时间",
        "notice_period_val": "即刻到岗",
        "summary": "专业总结",
        "category_label": "类别",
        "proficiency_label": "熟练度",
        "skills_tools_label": "技能与工具",
        "experience_years_label": "经验年限",
        "proj_name_label": "项目名称",
        "period_label": "期间",
        "type_label": "工作类型",
        "team_size_label": "团队规模",
        "marital_status": "婚姻状况",
        "wishes": "期望工作条件",
        "single": "未婚",
        "married": "已婚"
    }
}

# ─── PROMPTS ──────────────────────────────────────────────────────────────────
TRANSLATION_PROMPT = """
You are a professional resume translator.

Rules:
1. Translate ONLY what is given.
2. Do NOT add or remove any information.
3. Do NOT truncate or shorten the content. Never end with an ellipsis (...). Ensure the full original content is translated in its entirety.
4. Keep all numbers, percentages, and metrics EXACTLY as they are (94%, 10k+, 99.9%, 40%, 50%).
5. PROTECTED — copy these exactly, do not translate:
   "AI-Engineer-Portfolio", "Parkinson's Disease Detection System",
   "Logixbuilt Infotech", "PhysioNet", "PhysioNet/CinC Challenge",
   "FastAPI", "PyTorch", "PostgreSQL", "Redis", "MongoDB",
   "REST APIs", "CNN", "LSTM", "1D ResNet", "MCA", "BCA",
   "WhatsApp", "Telegram", "Facebook Messenger",
   "React", "Tailwind CSS", "Playwright", "SQLite", "AWS",
   "Git", "GitHub", "K6", "Pandas", "NumPy"
6. Translate ONLY natural language sentences and descriptions.
7. Maintain a professional, sophisticated business tone.
8. Target language: {target_lang}
9. Return ONLY the translation, nothing else.

Text to translate:
{text}
"""

BATCH_TRANSLATION_PROMPT = """
You are a professional resume translator specializing in technical roles.

Rules:
1. Translate the following list of items to {target_lang}.
2. Do NOT truncate or shorten the content. Never end with an ellipsis (...). Ensure all translations are complete.
3. PROTECTION RULE — these strings must appear EXACTLY as written, untranslated:
   PROTECTED_TERMS = [
     "AI-Engineer-Portfolio",
     "Parkinson's Disease Detection System", 
     "Logixbuilt Infotech",
     "PhysioNet",
     "PhysioNet/CinC Challenge",
     "CinC Challenge",
     "FastAPI", "PyTorch", "PostgreSQL", "Redis",
     "REST APIs", "CNN", "LSTM", "1D ResNet",
     "MCA", "BCA",
     "WhatsApp", "Telegram", "Facebook Messenger",
     "React", "Tailwind CSS", "Playwright", "SQLite",
     "AWS", "Git", "GitHub", "K6"
   ]
   If any of these appear in the text, copy them character-for-character including hyphens.
4. Keep all numbers, metrics, percentages, dates exactly as they are.
5. For Japan: Use business Keigo. For China/Korea: Use formal, high-impact language.
6. Return ONLY a valid JSON array. Each object: {{"index": N, "translation": "..."}}.
7. Return ONLY the JSON. No other text, no markdown, no explanation.

Items to translate:
{items_json}
"""

SYNTHESIS_PROMPT = """
You are a professional resume consultant specializing in cultural adaptation for {target_lang_name}.

Task:
Rewrite the following resume snippet (in English) to be more appealing to recruiters in {target_lang_name}.

Rules:
1. DO NOT just translate. REWRITE the content to fit the cultural professional standards of that region.
2. Do NOT truncate or shorten the content. Never end with an ellipsis (...). Ensure the full meaning, all achievements, and details are perfectly represented and preserved in full.
3. REGION AWARENESS: If the text mentions "Japan" or "Japanese" but the target region is China or Korea, 
   SWAP it for the correct country/language. If the target is International, use neutral global language.
4. Tone: Highly professional, formal, and achievement-oriented.
5. For Japan: Use business-appropriate Keigo. Emphasize team collaboration and stability.
6. For China: Emphasize high-impact metrics and certifications.
7. For South Korea: Use formal tone and specify project roles.
8. STRICT RULE: Keep technical terms (FastAPI, Python, CNN, etc.) in English.
9. DO NOT include phrases like "X years of experience", "X+ years", "X年の経験" or any 
   duration-based experience claims. Describe expertise by what was built, not how long.
10. DO NOT use filler phrases like: "passionate about", "driven to", "eager to", 
    "meaningful contribution", "forward-thinking", "seamless transition".
11. Return ONLY the rewritten text in {target_lang_name}, nothing else.

Section context: {field_name}
Original English text:
{text}
"""

# ─── CORE FUNCTIONS ───────────────────────────────────────────────────────────
from services.groq_service import call_groq

def contains_japanese(text: str) -> bool:
    """Returns True if string contains any Japanese characters."""
    return bool(re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]', text))

async def synthesize_resume_text(text: str, target_lang: str, field_name: str = "summary") -> str:
    """Uses LLM to culturally adapt resume snippets rather than just literal translation."""
    if not text:
        return text
    
    # Check Cache first
    cached = get_cached_translation(field_name, target_lang, text)
    if cached and cached[1] == 1: # is_verified
        return cached[0]

    lang_name = {
        "ko": "Korean",
        "ja": "Japanese",
        "zh": "Chinese",
    }.get(target_lang, "English")

    prompt = SYNTHESIS_PROMPT.format(
        target_lang_name=lang_name,
        field_name=field_name,
        text=text
    )
    
    try:
        synthesized = await call_groq(prompt)
        synthesized = synthesized.strip()
        
        # Save to Cache as verified because this was a deliberate synthesis request
        save_translation(field_name, target_lang, text, synthesized, is_verified=True)
        
        return synthesized
    except Exception as e:
        print(f"Synthesis error: {e}")
        return text # Fallback to original English

async def translate_text(text: str, target_lang: str, field_name: str = "generic") -> str:
    """Translates text using Groq with SQLite caching."""
    if not text:
        return text
    
    # Normally skip English, unless the source is Japanese and we want English
    if target_lang == "en" and not contains_japanese(text):
        return text

    # 1. Check Cache
    cached = get_cached_translation(field_name, target_lang, text)
    if cached:
        return cached[0] # translated_text

    # 2. Call AI
    lang_name = {
        "ko": "Korean",
        "ja": "Japanese",
        "zh": "Chinese",
        "de": "German",
        "fr": "French",
        "en": "English"
    }.get(target_lang, "English")

    prompt = TRANSLATION_PROMPT.format(target_lang=lang_name, text=text)
    
    try:
        translated = await call_groq(prompt)
        translated = translated.strip()
        
        # 3. Save to Cache (Mark as unverified initially)
        save_translation(field_name, target_lang, text, translated, is_verified=False)
        
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text # Fallback to original English

async def translate_batch(items: List[Dict[str, str]], target_lang: str) -> List[str]:
    """
    Translates multiple strings in a single API call to avoid rate limits.
    items: List of {"text": "...", "field_name": "..."}
    """
    if not items:
        return []
    
    # Normally skip English
    if target_lang == "en":
        needs_translation = any(contains_japanese(item["text"]) for item in items)
        if not needs_translation:
            return [item["text"] for item in items]

    results = [None] * len(items)
    to_translate = [] # list of (original_index, item)

    # 1. Check Cache for each
    for i, item in enumerate(items):
        text = item["text"]
        field = item["field_name"]
        if not text:
            results[i] = ""
            continue
            
        cached = get_cached_translation(field, target_lang, text)
        if cached:
            results[i] = cached[0]
        else:
            to_translate.append((i, item))

    if not to_translate:
        return results

    # 2. Call AI in batches of 15
    lang_name = {"ko": "Korean", "ja": "Japanese", "zh": "Chinese", "en": "English"}.get(target_lang, "English")
    
    for start_idx in range(0, len(to_translate), 15):
        chunk = to_translate[start_idx : start_idx + 15]
        
        chunk_data = [{"index": idx, "text": item["text"]} for idx, item in chunk]
        prompt = BATCH_TRANSLATION_PROMPT.format(
            target_lang=lang_name, 
            items_json=json.dumps(chunk_data, ensure_ascii=False)
        )
        
        for attempt in range(2):
            try:
                response = await call_groq(prompt)
                clean_res = response.strip()
                if "```json" in clean_res:
                    clean_res = clean_res.split("```json")[1].split("```")[0]
                elif "```" in clean_res:
                    clean_res = clean_res.split("```")[1].split("```")[0]
                
                clean_res = re.sub(r'[\x00-\x1F\x7F]', '', clean_res)
                # FIX (Bug 1): Replace double-escape with negative lookbehind/lookahead
                clean_res = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', clean_res)
                
                try:
                    translations = json.loads(clean_res, strict=False)
                except Exception as json_err:
                    print("DEBUG RAW RESPONSE:")
                    print(response)
                    print("DEBUG CLEAN RES:")
                    print(clean_res)
                    arr_match = re.search(r'\[\s*{.*}\s*\]', clean_res, re.DOTALL)
                    if arr_match:
                        translations = json.loads(arr_match.group(0), strict=False)
                    else:
                        raise json_err
                
                for t in translations:
                    orig_idx = t["index"]
                    translated_text = t["translation"]
                    
                    # FIX (Bug 3): skip empty translations, fall back to original
                    if not translated_text or not translated_text.strip():
                        orig_text = next(item["text"] for idx, item in chunk if idx == orig_idx)
                        results[orig_idx] = orig_text
                        continue
                        
                    field_name = next(item["field_name"] for idx, item in chunk if idx == orig_idx)
                    orig_text = next(item["text"] for idx, item in chunk if idx == orig_idx)
                    results[orig_idx] = translated_text
                    save_translation(field_name, target_lang, orig_text, translated_text, is_verified=False)
                break
            except Exception as e:
                if "429" in str(e) and attempt == 0:
                    print(f"Rate limited during batch translation. Retrying in 5s...")
                    await asyncio.sleep(5) # asyncio imported now
                    continue
                print(f"Batch translation error for chunk {start_idx}: {e}")
                for idx, item in chunk:
                    if results[idx] is None:
                        results[idx] = item["text"]
                break

    return [r if r is not None else items[i]["text"] for i, r in enumerate(results)]

def get_labels(lang: str):
    """Returns the labels dictionary for the target language."""
    if lang not in LABELS:
        print(f"Warning: No labels found for language '{lang}', falling back to English.")
    return LABELS.get(lang, LABELS["en"])

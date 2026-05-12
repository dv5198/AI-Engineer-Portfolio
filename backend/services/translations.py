# backend/services/translations.py

import os
from services.groq_service import call_groq
from database import get_cached_translation, save_translation

LABELS = {
    "ko": {
        "education": "학력",
        "experience": "경력",
        "skills": "스킬",
        "projects": "주요 프로젝트",
        "awards": "수상",
        "research": "연구/논문",
        "certificates": "자격증",
        "languages": "언어 능력",
        "current": "재직중",
        "left": "퇴직",
        "fulltime": "정규직",
        "freelance": "프리랜서",
        "individual": "개인",
        "developer": "개발자",
        "summary": "전문 분야 요약",
        "contact": "연락처",
    },
    "ja": {
        "education": "学歴",
        "experience": "職歴",
        "skills": "スキル・技術",
        "projects": "プロジェクト詳細",
        "awards": "受賞",
        "research": "研究・論文",
        "certificates": "免許・資格",
        "languages": "語学",
        "current": "在職中",
        "left": "退職",
        "fulltime": "正社員",
        "freelance": "フリーランス",
        "individual": "個人",
        "developer": "開発者",
        "summary": "自己PR",
        "contact": "連絡先",
    },
    "en": {
        "education": "Education",
        "experience": "Professional Experience",
        "skills": "Skills & Expertise",
        "projects": "Key Projects",
        "awards": "Awards & Achievements",
        "research": "Research & Academic Work",
        "certificates": "Certifications",
        "languages": "Languages",
        "current": "Current",
        "left": "Resigned",
        "fulltime": "Full-time",
        "freelance": "Freelance",
        "individual": "Individual",
        "developer": "Developer",
        "summary": "Professional Summary",
        "contact": "Contact Information",
    },
    "zh": {
        "education": "教育经历",
        "experience": "工作经历",
        "skills": "技能专长",
        "projects": "项目经验",
        "awards": "荣誉奖项",
        "research": "研究成果",
        "certificates": "资质证书",
        "languages": "语言能力",
        "current": "在职",
        "left": "离职",
        "fulltime": "全职",
        "freelance": "自由职业",
        "individual": "个人",
        "developer": "开发者",
        "summary": "专业总结",
        "contact": "联系方式",
    }
}

TRANSLATION_PROMPT = """
You are a professional resume translator.

Rules:
1. Translate ONLY what is given.
2. Do NOT add or remove any information.
3. Keep all numbers, percentages, and metrics EXACTLY as they are (e.g., 94% stays 94%, 10k+ stays 10k+).
4. Keep company names in English (e.g., 'Logixbuilt Infotech' stays as is).
5. Keep technical terms in English (e.g., 'FastAPI', 'PostgreSQL', 'CNN' stays as is).
6. Translate ONLY natural language sentences.
7. Maintain a professional, sophisticated business tone.
8. Target language: {target_lang}
9. Return ONLY the translation, nothing else. No introductions or explanations.

Text to translate:
{text}
"""

import json
from typing import List, Dict

BATCH_TRANSLATION_PROMPT = """
You are a professional resume translator.

Rules:
1. Translate the following list of items to {target_lang}.
2. Return ONLY a valid JSON array of objects, each containing "index" and "translation".
3. Maintain original meaning, professional tone, and keep technical terms/numbers in English.
4. Return ONLY the JSON, no other text.

Items:
{items_json}
"""

async def translate_text(text: str, target_lang: str, field_name: str = "generic") -> str:
    """Translates text using Groq with SQLite caching."""
    if not text or target_lang == "en":
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
        "fr": "French"
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
    if not items or target_lang == "en":
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

    # 2. Call AI in batches of 15 (to be safe with context and RPM)
    lang_name = {"ko": "Korean", "ja": "Japanese", "zh": "Chinese"}.get(target_lang, "English")
    
    # Process in chunks of 15
    for start_idx in range(0, len(to_translate), 15):
        chunk = to_translate[start_idx : start_idx + 15]
        
        chunk_data = [{"index": idx, "text": item["text"]} for idx, item in chunk]
        prompt = BATCH_TRANSLATION_PROMPT.format(
            target_lang=lang_name, 
            items_json=json.dumps(chunk_data, ensure_ascii=False)
        )
        
        try:
            response = await call_groq(prompt)
            # Clean response if AI adds markdown blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            translations = json.loads(response.strip())
            
            for t in translations:
                orig_idx = t["index"]
                translated_text = t["translation"]
                
                # Find the field name for this index
                field_name = next(item["field_name"] for idx, item in chunk if idx == orig_idx)
                orig_text = next(item["text"] for idx, item in chunk if idx == orig_idx)
                
                results[orig_idx] = translated_text
                # 3. Save to Cache
                save_translation(field_name, target_lang, orig_text, translated_text, is_verified=False)
        except Exception as e:
            print(f"Batch translation error for chunk {start_idx}: {e}")
            # Fallback for this chunk
            for idx, item in chunk:
                if results[idx] is None:
                    results[idx] = item["text"]

    # Fill any remaining Nones (shouldn't happen)
    return [r if r is not None else items[i]["text"] for i, r in enumerate(results)]

def get_labels(lang: str):
    """Returns the labels dictionary for the target language."""
    return LABELS.get(lang, LABELS["en"])

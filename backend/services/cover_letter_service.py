import os
import json
import httpx
import asyncio
from typing import Optional
import hashlib
import re
import time

# ─── CACHE CONFIG ────────────────────────────────────────────────────────────
CL_CACHE = {}  # { cache_key: (letter_text, timestamp) }
CL_CACHE_TTL = 3600  # 1 hour
CL_CACHE_MAX_SIZE = 50

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a professional cover letter writer specialising in international tech hiring.
Write like a real, intelligent person — not like AI-generated text.
Be direct and specific. Vague enthusiasm is worse than silence.

TONE & VOICE:
Never use any of these phrases (they are banned):
"propelled me towards", "thought leader", "avenues for growth",
"strong professional evolution", "transformative solutions", "passionate about",
"driven to contribute", "leverage my expertise", "I am eager to",
"meaningful difference", "make a difference", "revolutionize",
"cutting-edge solutions", "I thrive on", "push the boundaries",
"like-minded professionals", "tangible impact", "upon joining",
"long-term vision is to establish myself", "delivering significant value",
"foster a culture of", "world-class", "global tech ecosystem",
"I am excited to", "I am delighted to", "honed my skills",
"seasoned professional", "results-driven", "go-getter", "team player",
"excited about", "make a meaningful contribution", "drive impact",
"forward-thinking organization", "seamless transition", "I am confident that",
"passion for", "eager to".

CRITICAL RULES:
- Do NOT mention years of experience as a number (no "4+ years", no "X years", 
  no "X年の経験", no "X년 경험"). Describe what was built, not how long.
- Do NOT include a salutation (no "Dear Hiring Manager") — added separately.
- Do NOT include a sign-off (no "Best regards") — added separately.
- Return ONLY the letter body. Nothing else. No preamble, no explanation.

ACHIEVEMENT SELECTION:
- Read the full resume data provided.
- Identify the single strongest quantified achievement.
- Open with that achievement — not with background, not with passion.
- If a newer or stronger project exists in the data than ECG/cardiac work, use it.

STRUCTURE — exactly 4 parts/paragraphs:
  Part 1 (Growth): Career background, engineering development, and major accomplishments (e.g. cardiac abnormality model with 94% F1-score using 1D ResNet).
  Part 2 (Traits): Technical strengths, PyTorch/FastAPI proficiency, and production-grade architectures.
  Part 3 (Motivation): Why targeting this specific region/country ecosystem. Use the ecosystem context and reference specific local institutions/initiatives.
  Part 4 (Goal): Long-term contributions, relocation readiness, visa arrangements, and invitation to talk.
"""

# ─── COUNTRY CONFIGS ──────────────────────────────────────────────────────────
COUNTRY_CONFIGS = {
    "US": {
        "country_name": "United States",
        "ecosystem": "The US healthcare AI market is the largest in the world, driven by FDA-cleared diagnostic algorithms, NIH-funded research, and a strong venture-backed healthtech startup ecosystem. Culture rewards demonstrated results and technical depth over credentials.",
        "tone": "Direct and confident. Americans value results over process. Open with the number, not the story behind it. Avoid humility — state achievements as facts. Professional but not stiff.",
        "visa_statement": "I am based in India and would require H-1B visa sponsorship to work in the US. I am fully committed to relocation and happy to discuss timelines at any stage.",
        "language_note": ""
    },
    "UK": {
        "country_name": "United Kingdom",
        "ecosystem": "The UK has a strong healthcare AI sector built around NHS digital transformation, academic research from Oxford, Imperial, UCL, and Cambridge, and the Alan Turing Institute. NICE and MHRA are increasingly approving AI-based diagnostic tools. British companies value depth and measured confidence.",
        "tone": "Professional and measured. British business culture values understatement over self-promotion. 'I achieved X' rather than 'I delivered exceptional results in X'.",
        "visa_statement": "I am an Indian national and would require UK Skilled Worker visa sponsorship. I am fully prepared to relocate and committed to a long-term role in the UK.",
        "language_note": ""
    },
    "DE": {
        "country_name": "Germany",
        "ecosystem": "Germany is Europe's leading MedTech market, home to Siemens Healthineers, Philips Healthcare, and a growing AI healthtech startup scene in Berlin and Munich. Industry 4.0 is a national priority. Engineering culture values precision, thoroughness, and technical depth.",
        "tone": "Formal and precise. German business letters are structured and direct — no small talk. State qualifications clearly. Reference technical specifics. Mention EU Blue Card proactively.",
        "visa_statement": "As a qualified non-EU software engineer with a Master's degree, I am eligible for the EU Blue Card, which simplifies the visa sponsorship process considerably. I am fully committed to relocating to Germany.",
        "language_note": ""
    },
    "AE": {
        "country_name": "UAE",
        "ecosystem": "The UAE's National AI Strategy 2031 positions it as a global AI hub. Dubai and Abu Dhabi are investing heavily in smart city infrastructure, digital health, and fintech AI through companies like G42 and Presight AI. Healthcare AI is a focus area under Vision 2031.",
        "tone": "Professional and results-oriented. Reference AI Strategy 2031 specifically. Directness is valued. The market is international and fast-moving.",
        "visa_statement": "I am an Indian national, open to full relocation to the UAE. I understand that employment visa arrangements are typically handled as part of the hiring process and am ready to proceed.",
        "language_note": ""
    },
    "IN": {
        "country_name": "India",
        "ecosystem": "India's AI product ecosystem is growing rapidly — driven by companies like Sigmoid, Fractal Analytics, and a large wave of deep-tech startups. Healthcare AI is active given India's scale of patient population. Notice period and immediate availability matter to Indian recruiters.",
        "tone": "Direct and practical. Indian recruiters read fast and value clarity. Focus on technical achievements and immediate availability. Shorter is better.",
        "visa_statement": "I am an Indian national, immediately available, and require no notice period.",
        "language_note": ""
    },
    "GLOBAL": {
        "country_name": "international markets",
        "ecosystem": "This letter will be read by companies across multiple countries and sectors. Frame the candidate as someone with strong fundamentals who can contribute across healthcare AI and production ML regardless of geography. Do not reference any specific country.",
        "tone": "Neutral and universally professional. Avoid anything culturally specific. Clear, confident, clean.",
        "visa_statement": "I am open to relocating anywhere in the world and will require work visa sponsorship depending on the country. I am familiar with international hiring processes.",
        "language_note": ""
    },
    "JP_EN": {
        "country_name": "Japan",
        "ecosystem": "Japan is a global leader in medical robotics and AI-assisted diagnostics, driven by one of the world's oldest populations. Key players include Hitachi Health, Fujitsu, NTT Data. Japanese companies value long-term commitment, cultural awareness, and respect for team hierarchy.",
        "tone": "Respectful and structured. Show awareness of Japanese business culture without being performative. Mention Japanese language study honestly — do not overstate level. Express genuine long-term commitment to Japan.",
        "visa_statement": "I am fully prepared to relocate to Japan and would apply for the Engineer / Specialist in Humanities / International Services visa (技術・人文知識・国際業務) through employer sponsorship.",
        "language_note": "I am currently studying Japanese — beginner level — and committed to reaching working proficiency. I understand that language integration is part of working effectively within a Japanese team."
    },
    "JP_JA": {
        "country_name": "日本",
        "ecosystem": "日本は医療ロボット、AI診断支援、高齢者ケア技術において世界をリードしています。日立、富士通、NTTデータ、そして東京を拠点とする医療AIスタートアップが主要プレイヤーです。",
        "tone": "Formal Japanese business style (敬語). Structured and respectful. Honest about Japanese language level. Express genuine long-term intention.",
        "visa_statement": "就労ビザ（技術・人文知識・国際業務）については採用決定後に貴社のご支援のもとで申請予定です。",
        "language_note": "現在日本語を学習中です（初級レベル）。チームへの貢献に必要な語学力を身につけることを長期的な目標として真剣に取り組んでいます。"
    },
    "KR_EN": {
        "country_name": "Korea",
        "ecosystem": "Korea's AI ecosystem is world-class — anchored by KAIST, ETRI, and POSTECH in research, and Samsung, Kakao, and Naver in industry. Healthcare AI is active in diagnostic imaging and wearable health monitoring.",
        "tone": "Professional and achievement-focused. Reference Korea's research institutions by name. Mention Korean language study honestly. Express long-term commitment to Korea.",
        "visa_statement": "I would require E-7 Specially Designated Activities visa sponsorship and am fully prepared to relocate to Korea.",
        "language_note": "I am currently studying Korean — beginner level — and approaching it with the same commitment I bring to my technical work. Language ability is part of genuine integration into a Korean team."
    },
    "KR_KO": {
        "country_name": "한국",
        "ecosystem": "한국의 AI 생태계는 KAIST, ETRI, POSTECH 등 세계적인 연구기관과 삼성, LG, 카카오, 네이버 등 글로벌 기업이 주도하고 있습니다. 의료 AI 분야에서도 진단 영상, 웨어러블 헬스케어 등에서 혁신적인 연구가 활발히 이루어지고 있습니다.",
        "tone": "Professional, formal Korean. Follow 자기소개서 structure exactly.",
        "visa_statement": "E-7 비자 발급을 위한 회사의 스폰서십을 요청드리며, 한국으로의 이주에 완전히 준비되어 있습니다.",
        "language_note": "현재 한국어를 학습 중입니다（초급 수준）。장기적으로 비즈니스 수준의 한국어 능력을 목표로 성실히 학습하고 있습니다。"
    },
    "CN_EN": {
        "country_name": "China",
        "ecosystem": "China is the world's second-largest AI market. Healthcare AI investment flows through Tsinghua University, Peking University, Alibaba DAMO Academy, Baidu Health, Ping An Good Doctor, and ByteDance's medical AI division. Cardiac AI and medical imaging are particularly active.",
        "tone": "Professional and research-oriented. Reference Chinese institutions and companies by name. Mention Mandarin study honestly. Frame the candidate as committed to long-term contribution.",
        "visa_statement": "I would require Z work visa sponsorship through the hiring company and am fully prepared to relocate to China.",
        "language_note": "I am currently studying Mandarin Chinese — beginner level — and committed to steady progression. Language ability is part of genuine integration into a team."
    },
    "CN_CN": {
        "country_name": "中国",
        "ecosystem": "中国是全球最重要的AI市场之一，清华大学、北京大学等顶尖学术机构，以及阿里巴巴达摩院、百度健康、平安好医生等企业正在引领医疗AI的发展。心脏诊断、医学影像和预测健康领域尤为活跃。",
        "tone": "Professional and respectful (敬语). Focused on long-term contribution and research depth.",
        "visa_statement": "我将通过贵公司申请Z类工作签证，并已做好赴华工作的充分准备。",
        "language_note": "目前我正在系统学习普通话（初学者阶段），视语言能力为融入团队的重要组成部分，并将持续认真推进。"
    }
}

# ─── SALUTATIONS & SIGN-OFFS ──────────────────────────────────────────────────
SALUTATIONS = {
    "JP_JA": "拝啓　時下ますますご清栄のこととお慶び申し上げます。\n\n",
    "KR_KO": "",   # 자기소개서 has no salutation
    "CN_CN": "尊敬的招聘负责人：\n\n",
    "DEFAULT": "Dear Hiring Manager,\n\n"
}

SIGNOFFS = {
    "US":    "\n\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "UK":    "\n\nYours sincerely,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "DE":    "\n\nWith kind regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "AE":    "\n\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "IN":    "\n\nRegards,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "GLOBAL":"\n\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "JP_EN": "\n\nRespectfully,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "JP_JA": "\n\n敬具\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "KR_EN": "\n\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "KR_KO": "\n\n위 내용이 사실임을 확인합니다.\n\n2026년 5월\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "CN_EN": "\n\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
    "CN_CN": "\n\n此致\n敬礼\n\nDivya Nirankari\ndvnirankari@gmail.com | +91 9265768306",
}

# ─── NATIVE LANGUAGE SYSTEM PROMPT ADDITIONS ─────────────────────────────────
NATIVE_LANG_ADDITIONS = {
    "JP_JA": """\nWrite entirely in formal Japanese (敬語). Follow standard 自己紹介書 / 自己PR format with EXACTLY these 4 section headings in bold:
1. **成長過程 (Growth)**
2. **自身の強み・技術的特徴 (Traits)**
3. **志望動機 (Motivation)**
4. **今後の目標・入社後の抱負 (Goal)**
Each section: bold heading on its own line, then 1-2 paragraphs of content.
Do NOT include a salutation or sign-off — the system adds these.
Do NOT include the candidate name or date — the system adds these.
Return ONLY the 4 sections.""",
    "KR_KO": """\nWrite entirely in Korean (한국어). 
Follow the standard 자기소개서 format with EXACTLY these 4 section headings in bold:
1. **성장과정 (Growth)**
2. **성격의 장단점 (Traits)**
3. **지원동기 (Motivation)**
4. **입사 후 포부 (Goal)**
Each section: bold heading on its own line, then 1-2 paragraphs of content.
Do NOT include a salutation or sign-off — the system adds these.
Do NOT include the candidate name or date — the system adds these.
Return ONLY the 4 sections.""",
    "CN_CN": """\nWrite entirely in formal Simplified Chinese (简体中文). Follow the standard 求职信 format with EXACTLY these 4 section headings in bold:
1. **成长历程 (Growth)**
2. **专业特长 (Traits)**
3. **求职动机 (Motivation)**
4. **职业目标 (Goal)**
Each section: bold heading on its own line, then 1-2 paragraphs of content.
Do NOT include a salutation or sign-off — the system adds these.
Do NOT include the candidate name or date — the system adds these.
Return ONLY the 4 sections."""
}

# ─── HELPER: STRIP AI PREAMBLE ────────────────────────────────────────────────
STRIP_PREFIXES = (
    "Here is", "Certainly", "Okay", "Sure", "Of course",
    "Dear Hiring", "Dear ",
    "To the Hiring Manager",
    "Best regards,", "Sincerely,",
    "Respectfully,", "With kind regards,",
    "Regards,",
)

NATIVE_SIGNOFF_PREFIXES = {
    "JP_JA": ("敬具",),
    "CN_CN": ("此致", "敬礼"),
    "KR_KO": ("위 내용이",),
}

def _strip_ai_preamble(text: str, country_code: str) -> str:
    """
    Strips any salutation, date, candidate contact info, or sign-off lines from the LLM response.
    Highly robust against markdown (**, *, #) and various punctuations.
    """
    lines = text.strip().split('\n')
    
    # 1. Strip from the beginning (salutations, headers, candidate details)
    start_idx = 0
    while start_idx < len(lines):
        line = lines[start_idx].strip()
        clean_line = re.sub(r'[*_#`\-]+', '', line).strip()
        
        if not clean_line:
            start_idx += 1
            continue
            
        # Check if line is a salutation or contact/metadata header
        is_salutation = any(
            clean_line.lower().startswith(p.lower()) for p in [
                "dear", "to the", "subject:", "re:", "application for", "cover letter"
            ]
        ) or "hiring manager" in clean_line.lower() or "招聘负责人" in clean_line
        
        is_contact_or_metadata = any(
            p.lower() in clean_line.lower() for p in [
                "divya", "nirankari", "dvnirankari", "@gmail.com", "9192657", "92657"
            ]
        )
        
        if is_salutation or is_contact_or_metadata:
            start_idx += 1
        else:
            break
            
    # 2. Strip from the end (sign-offs, candidate signatures)
    end_idx = len(lines)
    while end_idx > start_idx:
        line = lines[end_idx - 1].strip()
        clean_line = re.sub(r'[*_#`\-]+', '', line).strip()
        
        if not clean_line:
            end_idx -= 1
            continue
            
        is_signoff = any(
            clean_line.lower().startswith(p.lower()) for p in [
                "best regards", "sincerely", "respectfully", "regards", 
                "yours sincerely", "with kind regards", "kind regards",
                "yours faithfully", "best wishes", "thank you"
            ]
        ) or any(
            p in clean_line for p in [
                "敬具", "此致", "敬礼", "위 내용이", "사실임을 확인합니다"
            ]
        )
        
        is_contact_or_name = any(
            p.lower() in clean_line.lower() for p in [
                "divya", "nirankari", "dvnirankari", "@gmail.com", "9192657", "92657", "tel:"
            ]
        )
        
        if is_signoff or is_contact_or_name:
            end_idx -= 1
        else:
            break
            
    body_lines = lines[start_idx:end_idx]
    return '\n'.join(body_lines).strip()


# ─── HELPER: ASSEMBLE FULL LETTER ─────────────────────────────────────────────
def _assemble_letter(country_code: str, body: str) -> str:
    """
    Wraps the AI-generated body with the correct salutation and sign-off.
    """
    salutation = SALUTATIONS.get(country_code, SALUTATIONS["DEFAULT"])
    signoff = SIGNOFFS.get(country_code, SIGNOFFS["US"])
    return f"{salutation}{body}{signoff}"


# ─── MAIN FUNCTION ────────────────────────────────────────────────────────────
async def generate_dynamic_cover_letter(
    region: str,
    lang: str,
    resume_data: dict
) -> str:
    """
    Generates a dynamic, AI-powered cover letter.
    Returns a fully assembled letter (salutation + body + signoff).
    """

    # 1. Resolve country code
    region_key_map = {
        'japan': 'JP', 'korea': 'KR', 'china': 'CN',
        'germany': 'DE', 'uk': 'UK', 'usa': 'US',
        'india': 'IN', 'uae': 'AE', 'international': 'GLOBAL'
    }
    base_code = region_key_map.get(region.lower(), 'GLOBAL')

    if base_code in ['JP', 'KR', 'CN']:
        lang_suffix_map = {
            ('JP', 'ja'): 'JP_JA',
            ('JP', 'en'): 'JP_EN',
            ('KR', 'ko'): 'KR_KO',
            ('KR', 'en'): 'KR_EN',
            ('CN', 'zh'): 'CN_CN',
            ('CN', 'en'): 'CN_EN',
        }
        country_code = lang_suffix_map.get((base_code, lang), f"{base_code}_EN")
    else:
        country_code = base_code

    config = COUNTRY_CONFIGS.get(country_code, COUNTRY_CONFIGS['GLOBAL'])

    # 2. Build minimised data payload
    min_data = {
        "profile": {
            "name": resume_data.get('profile', {}).get('name'),
            "role": resume_data.get('profile', {}).get('role'),
            "summary": _strip_years_phrasing(
                (resume_data.get('profile', {}).get('summary') or "")[:300]
            ),
        },
        "top_experience": [
            {
                "company": e.get('company'),
                "role": e.get('role'),
                "period": e.get('period'),
                "bullets": e.get('bullets', [])[:3]
            }
            for e in resume_data.get('experience', [])[:2]
        ],
        "top_projects": [
            {
                "name": p.get('name'),
                "summary": (p.get('summary') or p.get('description') or "")[:150],
                "outcomes": (p.get('outcomes') or "")[:100],
                "tech": p.get('techStack')
            }
            for p in resume_data.get('projects', [])[:3]
        ],
        "research": [
            {
                "title": r.get('title'),
                "metric": r.get('metric') or r.get('summary', '')[:80]
            }
            for r in resume_data.get('research', [])[:2]
        ],
        "skills": [c.get('label') for c in resume_data.get('skillCategories', [])]
    }

    # 3. Check cache with TTL
    cache_key = hashlib.md5(
        f"{country_code}_{lang}_{json.dumps(min_data, sort_keys=True)}".encode()
    ).hexdigest()
    
    if cache_key in CL_CACHE:
        cached_letter, cached_at = CL_CACHE[cache_key]
        if time.time() - cached_at < CL_CACHE_TTL:
            return cached_letter
        else:
            del CL_CACHE[cache_key]

    # 4. Build system prompt
    full_system_prompt = SYSTEM_PROMPT
    if country_code in NATIVE_LANG_ADDITIONS:
        full_system_prompt += NATIVE_LANG_ADDITIONS[country_code]

    # 5. Build user prompt
    user_prompt = f"""Generate a cover letter body for this candidate applying to companies in {config['country_name']}.

--- CANDIDATE DATA ---
{json.dumps(min_data, indent=2, ensure_ascii=False)}

--- COUNTRY CONTEXT ---
Country: {config['country_name']}
Ecosystem: {config['ecosystem']}
Tone: {config['tone']}
Visa: {config['visa_statement']}
{f"Language note: {config['language_note']}" if config['language_note'] else ""}

--- REMINDER ---
- Do NOT mention years of experience as a number.
- Para 3 must reference {config['country_name']} specifically — not generic "international markets".
- Return ONLY the letter body. No salutation. No sign-off. No preamble."""

    # 6. Call AI with retry
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ""

    model_to_use = "llama-3.3-70b-versatile"
    for attempt in range(3):
        if attempt > 0:
            model_to_use = "llama-3.1-8b-instant"
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_to_use,
                        "messages": [
                            {"role": "system", "content": full_system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.6,
                        "max_tokens": 1200
                    },
                    timeout=30.0
                )

                if response.status_code == 429:
                    print(f"Rate limit hit on {model_to_use}. Falling back to llama-3.1-8b-instant...")
                    model_to_use = "llama-3.1-8b-instant"
                    continue

                res_json = response.json()
                if 'choices' not in res_json:
                    return ""

                raw_body = res_json['choices'][0]['message']['content'].strip()

                # 7. Strip any AI-added preamble/sign-off
                clean_body = _strip_ai_preamble(raw_body, country_code)

                # 8. Assemble the full letter with salutation + signoff
                full_letter = _assemble_letter(country_code, clean_body)

                # 9. Save to cache
                if len(CL_CACHE) < CL_CACHE_MAX_SIZE:
                    CL_CACHE[cache_key] = (full_letter, time.time())

                return full_letter

        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2)

    return ""


# ─── HELPER: STRIP YEARS PHRASING ────────────────────────────────────────────
def _strip_years_phrasing(text: str) -> str:
    """
    Removes 'X+ years', 'X years of experience' etc.
    """
    patterns = [
        r'\b\d+\+?\s+years?\s+of\s+experience\b',
        r'\bover\s+\d+\+?\s+years?\b',
        r'\b\d+\+\s+years?\b',
        r'\bwith\s+\d+\+?\s+years?\b',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    text = re.sub(r'  +', ' ', text).strip()
    return text

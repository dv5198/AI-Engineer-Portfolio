import os
import json
import httpx
import asyncio
from typing import Optional
import hashlib
import re
import time
from dotenv import load_dotenv

load_dotenv()

# ─── CACHE CONFIG ───────────────────────────────────────────────────────
CL_CACHE = {}
CL_CACHE_TTL = 3600
CL_CACHE_MAX_SIZE = 100

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
"pushing the boundaries", "seamless integration",
"like-minded professionals", "tangible impact", "upon joining",
"long-term vision is to establish myself", "delivering significant value",
"foster a culture of", "world-class", "global tech ecosystem",
"I am excited to", "I am delighted to", "honed my skills",
"seasoned professional", "results-driven", "go-getter", "team player",
"excited about", "make a meaningful contribution", "drive impact",
"forward-thinking organization", "seamless transition", "I am confident that",
"passion for", "eager to", "strong fit", "make me a strong fit",
"I am eager to be a part of", "eager to be a part",
"pioneering technical business ecosystem",
"fine-tuning robust machine learning models",
"I hereby certify that the above statements are true and correct",
"Seal/Signature",
"spearheading backend optimizations",
"successfully manage large-scale traffic".

CRITICAL RULES:
- Do NOT mention years of experience as a number (no "4+ years", no "X years", 
  no "X年の経験", no "X年の经验", no "X년 경험"). Describe what was built, not how long.
- Do NOT reference physics labs or international research facilities like CERN.
- Do NOT include a salutation (no "Dear Hiring Manager") — added separately.
- Do NOT include a sign-off (no "Best regards") — added separately.
- Do NOT include any contact details, address, phone, email, date, or candidate's name — added separately by the system.
- Return ONLY the letter body. Nothing else. No preamble, no explanation.
- Keep the entire cover letter body brief (200–300 words, or 400–600 Japanese/Chinese characters) with short paragraphs (3-4 sentences each) so it fits on a single page.
- Do NOT repeat the same technical tools or achievements across paragraphs. Mention any specific technology (e.g. FastAPI, PostgreSQL, PyTorch) at most once in the entire letter.

ACHIEVEMENT SELECTION:
- Read the full resume data provided.
- Identify the single strongest quantified achievement.
- Open with that achievement — not with background, not with passion.
- If a newer or stronger project exists in the data than ECG/cardiac work, use it.

STRUCTURE — exactly 4 flowing paragraphs (NO section headings, NO bold labels, NO markdown):
Each paragraph has a fixed purpose — do not deviate:
Paragraph 1: Growth & Background — candidate's journey and how they arrived at this expertise, opening with candidate's strongest quantified achievement. The first sentence must begin with "I" (for example, "I developed a high-accuracy ECG..."), not with a bare action verb like "Developed...".
Paragraph 2: Strengths & Competencies — specific technical achievements with real numbers. Cite ONE specific technology, paper, or trend you follow (e.g. 1D ResNet for ECG, regulatory guidance on ML medical devices, PyTorch production patterns). NEVER write generic filler like "staying up-to-date with the latest advancements."
Paragraph 3: Motivation — why this country/company specifically. MANDATORY: Paragraph 3 MUST name at least one specific company or institution from the ecosystem context provided below. If ecosystem context is empty, throw an error — do not generate a generic paragraph. Do not repeat the word "ecosystem" twice in this paragraph.
Paragraph 4: Goals after Joining — concrete future contribution and visa/relocation statement (use the provided visa statement). Say "I welcome the opportunity to discuss…" not "I invite you to talk." Say "I am prepared to relocate" not "I will relocate" before being hired. Do not repeat or rephrase the visa statement.
Separate paragraphs with a single blank line only."""

# ─── COUNTRY CONFIGS ──────────────────────────────────────────────────────────
COUNTRY_CONFIGS = {
    "US": {
        "country_name": "United States",
        "ecosystem": "The US healthcare AI market is the largest in the world, driven by FDA-cleared diagnostic algorithms, NIH-funded research, and a strong venture-backed healthtech startup ecosystem with major players like Epic Systems, Google Health, and Microsoft Health. Culture rewards demonstrated results and technical depth over credentials.",
        "tone": "Direct and confident. Americans value results over process. Open with the number, not the story behind it. Avoid humility — state achievements as facts. Professional but not stiff.",
        "visa_statement": "I am based in India and would require H-1B visa sponsorship to work in the US. I am fully committed to relocation and happy to discuss timelines at any stage.",
        "language_note": ""
    },
    "UK": {
        "country_name": "United Kingdom",
        "ecosystem": "The UK has a strong healthcare AI sector built around NHS digital transformation, academic research from Oxford, Imperial, UCL, and Cambridge, and the Alan Turing Institute. NICE and MHRA are increasingly approving AI-based diagnostic tools. NHS Digital, DeepMind Health, and BenevolentAI are driving key industrial innovations. British companies value depth and measured confidence.",
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
        "ecosystem": "The UAE's National AI Strategy 2031 positions it as a global AI hub. Dubai and Abu Dhabi are investing heavily in smart city infrastructure, digital health, and fintech AI through companies like G42, Presight AI, Abu Dhabi Investment Office (ADIO), and Abu Dhabi Health Services (SEHA). Healthcare AI is a focus area under Vision 2031.",
        "tone": "Professional and results-oriented. Reference AI Strategy 2031 specifically. Directness is valued. The market is international and fast-moving.",
        "visa_statement": "I am an Indian national, open to full relocation to the UAE. I understand that employment visa arrangements are typically handled as part of the hiring process and am ready to proceed.",
        "language_note": ""
    },
    "IN": {
        "country_name": "India",
        "ecosystem": "India's AI product ecosystem is growing rapidly — driven by companies like Sigmoid, Fractal Analytics, and a large wave of deep-tech startups. Healthcare AI is active given India's scale of patient population, with innovative startups like Niramai, Qure.ai, and Tricog Health leading the way. Notice period and immediate availability matter to Indian recruiters.",
        "tone": "Direct and practical. Indian recruiters read fast and value clarity. Focus on technical achievements and immediate availability. Shorter is better.",
        "visa_statement": "I am an Indian national, immediately available, and require no notice period.",
        "language_note": ""
    },
    "GLOBAL": {
        "country_name": "international markets",
        "ecosystem": "This letter will be read by companies across multiple countries and sectors. Frame the candidate as someone with strong fundamentals who can contribute across healthcare AI and production ML regardless of geography. Do not reference any specific country, physics labs like CERN, or specific universities like UC Berkeley.",
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
        "ecosystem": "Korea's AI ecosystem is world-class — anchored by KAIST, ETRI, and POSTECH in research, and Samsung Medical, LG AI Research, and Naver in industry. Healthcare AI is active in diagnostic imaging and wearable health monitoring — cite specific Korean institutions, not generic 'local tech community' phrasing.",
        "tone": "Professional and achievement-focused. Reference Korea's research institutions by name. Mention Korean language study honestly. Express long-term commitment to Korea.",
        "visa_statement": "I require E-7 Specially Designated Activities visa sponsorship and am fully prepared to relocate to Korea.",
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
        "ecosystem": "China is the world's second-largest AI market. Healthcare AI investment flows through Tsinghua University, Peking University, Alibaba DAMO Academy, Baidu Health, and Ping An Good Doctor. Cardiac AI and medical imaging are particularly active — reference at least two of these by name in the motivation paragraph.",
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
    "US":    "\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "UK":    "\nYours sincerely,\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "DE":    "\nWith kind regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "AE":    "\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "IN":    "\nRegards,\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "GLOBAL":"\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "JP_EN": "\nRespectfully,\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "JP_JA": "\n敬具\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "KR_EN": "\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "KR_KO": "\n위 내용이 사실임을 확인합니다.\n\n{date_str}\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "CN_EN": "\nBest regards,\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
    "CN_CN": "\n此致\n敬礼\n\nDivya Nirankari\ndvnirankari@gmail.com | {phone}",
}

# ─── NATIVE LANGUAGE SYSTEM PROMPT ADDITIONS ─────────────────────────────────
NATIVE_LANG_ADDITIONS = {
    "JP_JA": """\nWrite entirely in formal Japanese (敬語). Use exactly 4 connected paragraphs — NO bold section headings.
Maintain consistent です・ます調 throughout. Do NOT invent any universities or institutions. Only mention companies or institutions explicitly listed in the ecosystem context (such as Hitachi, Fujitsu, NTT Data).
Do NOT include a salutation or sign-off — the system adds these.
Return ONLY the letter body.""",
    "KR_KO": """\nWrite entirely in formal Korean (합니다체). Follow 자기소개서 with EXACTLY these 4 section headings in bold:
1. **성장과정**
2. **역량**
3. **지원동기**
4. **입사 후 포부**
Use 저는/제 throughout — never 나는/내. In 지원동기, she is learning Korean (한국어), NOT English.
In 입사 후 포부 (Goals after Joining), focus on concrete technical contributions such as developing high-performance machine learning models, optimizing REST APIs, and contributing to the team's engineering excellence. Do NOT use repetitive boilerplate phrases like "최선을 다하겠습니다" (I will do my best) multiple times. Be specific about the engineering impact.
CRITICAL: Write entirely in formal Korean Hangul. Do NOT use any Chinese characters (Hanja) or Japanese Kanji (e.g. do NOT write 早期, 领域, 环境, 等, 検出, 知识, 高速, etc.; write them in Hangul as 초기, 분야, 환경, 등, 검출, 지식, 고속, etc.).
Do NOT include a salutation or sign-off — the system adds these.
Return ONLY the 4 sections.""",
    "CN_CN": """\nWrite entirely in formal Simplified Chinese (简体中文). Use exactly 4 connected paragraphs — NO bold section headings (standard 求职信 prose).
Do NOT include a salutation or sign-off — the system adds these.
Return ONLY the letter body."""
}

# Country codes that keep structured headings (자기소개서 only)
SECTIONED_COVER_CODES = frozenset({"KR_KO"})

# Phrase polish rules applied after generation/translation
_PHRASE_POLISH = [
    (r"\bI am excited by\b", "I welcome"),
    (r"\bworld-class\b", "high-calibre"),
    (r"\bdrive impact\b", "deliver results"),
    (r"\bforward-thinking organization\b", "this organization"),
    (r"\bforward-thinking\b", "progressive"),
    (r"\bdrive meaningful change\b", "deliver results"),
    (r"\bleverage my expertise\b", "apply my skills"),
    (r"\bUniversity of California,\s*Berkeley\b", "leading research institutions"),
    (r"\bUC Berkeley\b", "leading research institutions"),
    (r"make me a strong fit for this ecosystem", "make me a strong candidate for roles in this space"),
    (r"make me a strong fit", "make me a strong candidate"),
    (r"navigating the necessary arrangements", "complete the necessary visa process"),
    (r"I invite you to talk further about", "I welcome the opportunity to discuss"),
    (r"I invite you to talk further", "I welcome the opportunity to discuss"),
    (r"\bI will relocate to Korea\b", "I am prepared to relocate to Korea"),
    (r"\bI will relocate to Japan\b", "I am prepared to relocate to Japan"),
    (r"\bI will relocate to China\b", "I am prepared to relocate to China"),
    (r"Aspiring AI Engineer", "AI/ML Engineer"),
    (r"aspiring AI engineer", "AI/ML engineer"),
    (r"\bI am confident that\s*", ""),
    (r"\bI am excited to\s*", "I am prepared to "),
    (r"\bI am excited about\s*", "I am interested in "),
    (r"\bexcited about the prospect of\s*", "interested in the opportunity of "),
    (r"\bexcited about the prospect\s*", "interested in the opportunity"),
    (r"\bcutting-edge\b", "advanced"),
    (r"\bI am delighted to\s*", "I welcome the opportunity to "),
    (r"\bI am eager to be a part of\s*", "I look forward to contributing to "),
    (r"\beager to be a part of\s*", "ready to contribute to "),
    (r"\bI am eager to\s*", "I am prepared to "),
    (r"\beager to be a part\b", "ready to contribute"),
    (r"\bseamless integration\b", "integration"),
    (r"\bpushing the boundaries of\s*", "advancing "),
    (r"\bpushing the boundaries\b", "advancing development"),
    (r"\bhoned my skills in\s*", "developed my expertise in "),
    (r"\bhoned my skills\b", "developed my expertise"),
    (r"\bI am committed to staying at the forefront of\s*", "I follow advances in "),
    (r"\bcommitted to staying at the forefront of\s*", "focused on advances in "),
    (r"\bstaying at the forefront of\s*", "following advances in "),
    (r"\bI am committed to staying at the forefront\b", "I focus on new developments"),
    (r"\bcommitted to staying at the forefront\b", "focused on new developments"),
    (r"\bstaying at the forefront\b", "following new developments"),
    (r"meaningful contribution", "contribution"),
    (r"eager to learn", "ready to apply my skills"),
    (r"\bI look forward to exploring how my skills can be leveraged\b", "I look forward to discussing how my skills can contribute"),
    (r"\bUpon joining\b", "In this role"),
    # Japanese kanji fix (simplified Chinese form leaked)
    (r"拝见", "拝見"),
    # Japanese localization fixes (Cyrillic, mixed English, traditional characters, katakana terms)
    (r"обс論", "議論"),
    (r"обс", "議"),
    (r"preparedしております", "準備しております"),
    (r"preparedして", "準備して"),
    (r"醫療", "医療"),
    (r"マシーンラーニング", "機械学習"),
    (r"マシンラーニング", "機械学習"),
    # Japanese term fix: 心筋検出 (myocardial detection) → 心臓異常検出 (cardiac abnormality detection)
    (r"心筋検出", "心臓異常検出"),
    (r"心防検出", "心臓異常検出"),
    # Chinese: English word 'pattern' leaked into Chinese text
    (r"異常[.．]?pattern", "異常"),
    (r"异常[.．]?pattern", "异常"),
    (r"异常\.pattern", "异常"),
    (r"\bpattern\b", ""),  # standalone English 'pattern' in CJK text
    (r"In this role a company in China", "In this role at a company in China"),
    (r"committed to staying up-to-date with the latest advancements in AI and machine learning, continuously improving my skills and knowledge",
     "I follow advances in 1D ResNet architectures for ECG classification and FDA guidance on machine-learning medical devices, applying those insights to production PyTorch and FastAPI systems"),
    (r"this ecosystem\.\s*I am impressed by the work being done in this field and believe my skills and experience make me a strong fit for this ecosystem",
     "this market. I am impressed by the work being done in this field and believe my skills and experience make me a strong candidate for roles in this space"),
    (r"follow advances in the latest advancements", "follow latest advancements"),
    (r"advances in advancements", "advancements"),
    (r"I would require Z work visa sponsorship through the hiring company\.\s*I require Z-visa sponsorship for employment in China\.",
     "I would require Z work visa sponsorship through the hiring company."),
    (r"I require Z-visa sponsorship for employment in China\.\s*I would require Z work visa sponsorship through the hiring company\.",
     "I would require Z work visa sponsorship through the hiring company."),
    (r"地元の機関", "日本の著名な研究機関"),
    (r"영어를 계속 배우면서", "한국어를 계속 공부하면서"),
    (r"영어를 배우면서", "한국어를 공부하면서"),
    (r"albeit at a beginner level", "currently at an early stage of language study"),
    (r"char론할|चर론할|처론할", "논의할"),
    (r"機會", "기회"),
    (r"兴味", "興味"),
    (r"follow advances in advancements", "follow advancements"),
    (r"可扩缩的REST API", "可扩展的REST API"),
    (r"可扩缩的", "可扩展的"),
    (r"我非常看好中国的AI市场，认为这里有巨大的发展潜力", "我关注中国在医疗AI和医学影像领域的实际应用进展，并希望直接参与这一领域的产品开发。"),
    (r"我非常看好中国的AI市场", "我关注中国在医疗AI和医学影像领域的实际应用进展"),
    (r"认为这里有巨大的发展潜力", "并注意到该领域已涌现出可落地的产品机会"),
    (r"我々", "私"),
]

_SECTION_HEADER_LINE = re.compile(
    r"^\s*\*{0,2}\s*(Growth|Traits|Motivation|Goals?|成长|特质|动机|目标|"
    r"성장|특성|역량|동기|목표|グロース|成長|志望|入社|专业特长|职业目标|成长历程)\s*\*{0,2}\s*$",
    re.IGNORECASE,
)


def _to_prose_paragraphs(body: str) -> str:
    """Strip bold section labels and return flowing paragraphs."""
    if not body:
        return body
    paragraphs = []
    current = []
    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if _SECTION_HEADER_LINE.match(stripped) or re.match(r"^\*\*[^*]+\*\*\s*$", stripped):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        clean = re.sub(r"^\*\*|\*\*$", "", stripped).strip()
        if clean:
            current.append(clean)
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(p for p in paragraphs if p.strip())


# Korean CJK leak fixes — characters that Google Translate sometimes outputs
# in Korean text instead of proper Hangul equivalents
_KO_CJK_FIXES = [
    ("検出", "검출"),   # JP kanji for detection
    ("知识", "지식"),   # CN for knowledge
    ("高速", "고속"),   # JP/CN for high-speed
    ("機會", "기회"),   # JP/CN for opportunity (also in _PHRASE_POLISH but guard here too)
    ("技術", "기술"),   # JP for technology
    ("處理", "처리"),   # JP for processing
    ("早期", "초기"),   # CN/JP for early stage
    ("领域", "분야"),   # CN/JP for field
    ("环境", "환경"),   # CN/JP for environment
    ("等", "등"),       # CN/JP for etc.
    ("高精度", "고정밀"), # JP/CN for high precision
    ("心電図", "심전도"), # JP kanji for ECG
    ("이코시스템", "이 생태계"), # Korean transliteration artifact
    ("이کو시스템", "이 생태계"), # Arabic/Urdu character artifact in Korean
    ("développez", "개발"), # French translation leak
    ("développer", "개발"), # French translation leak variant
    ("遵守", "준수"),   # CN character leaked
    ("expertise", "전문성"),  # English word leaked into Korean
    ("experience", "경험"),   # English word leaked into Korean
    ("pattern", "패턴"),       # English word leaked into Korean
]


def _sanitize_korean_cl(text: str) -> str:
    """Remove leaked Japanese/Chinese CJK characters from Korean cover letter text."""
    for wrong, correct in _KO_CJK_FIXES:
        text = text.replace(wrong, correct)
    return text


def _clean_polished_casing(text: str) -> str:
    """Capitalizes the first letter of sentences and collapses multiple spaces."""
    if not text:
        return text
    paragraphs = text.split("\n\n")
    cleaned_paras = []
    for para in paragraphs:
        # Capitalize the first word of the paragraph if it's lowercase
        def cap_first(m):
            return m.group(1) + m.group(2).upper()
        para = re.sub(r"^(\s*)([a-z])", cap_first, para)
        # Capitalize after sentence-ending punctuation followed by space
        para = re.sub(r"([.!?]\s+)([a-z])", cap_first, para)
        # Collapse multiple spaces (except newlines)
        para = re.sub(r" +", " ", para)
        cleaned_paras.append(para.strip())
    return "\n\n".join(cleaned_paras)


def _ensure_first_person_opening(body: str) -> str:
    if not body:
        return body
    paragraphs = re.split(r"\n\s*\n", body)
    if not paragraphs:
        return body
    first_para = paragraphs[0].strip()
    if re.match(r'^(Developed|Built|Designed|Delivered|Implemented|Managed|Optimized|Improved|Created|Generated|Shipped|Deployed|Reduced|Scaled|Automated|Architected|Constructed)\s', first_para):
        paragraphs[0] = "I " + first_para[0].lower() + first_para[1:]
    return "\n\n".join(paragraphs)


def _append_kr_en_visa(body: str) -> str:
    if not body:
        return body
    if re.search(r"E-7\s+Specially\s+Designated\s+Activities\s+visa\s+sponsorship", body, re.IGNORECASE):
        return body
    paragraphs = re.split(r"\n\s*\n", body)
    if paragraphs:
        last_paragraph = paragraphs[-1].rstrip()
        if last_paragraph and last_paragraph[-1] not in '.!?':
            last_paragraph += '.'
        last_paragraph += " I require E-7 Specially Designated Activities visa sponsorship to work in Korea."
        paragraphs[-1] = last_paragraph
    return "\n\n".join(paragraphs)


def _append_cn_en_requirements(body: str, allow_language_note: bool = False) -> str:
    if not body:
        return body
    has_visa = bool(re.search(r"\bZ(?:[-\s]?work)?\s*visa\b|\bZ[-\s]?visa\b|Z签证", body, re.IGNORECASE))
    has_language = bool(re.search(r"Mandarin|Mandarin Chinese|普通话|Chinese", body, re.IGNORECASE))
    companies = ["Tsinghua", "Peking University", "Alibaba DAMO Academy", "Baidu Health", "Ping An Good Doctor"]
    present = [c for c in companies if c in body]
    append_parts = []
    if len(present) < 2:
        missing = [c for c in companies if c not in body]
        if len(missing) >= 2:
            append_parts.append(f"I have followed work from {missing[0]} and {missing[1]}.")
        elif missing:
            append_parts.append(f"I have followed work from {missing[0]}.")
    if not has_language and allow_language_note:
        append_parts.append("I am currently studying Mandarin Chinese and committed to steady progress.")
    if not has_visa:
        append_parts.append("I require Z-visa sponsorship for employment in China.")
    if not append_parts:
        return body
    paragraphs = re.split(r"\n\s*\n", body)
    last_paragraph = paragraphs[-1].rstrip()
    if last_paragraph and last_paragraph[-1] not in '.!?':
        last_paragraph += '.'
    last_paragraph += " " + " ".join(append_parts)
    paragraphs[-1] = last_paragraph
    return "\n\n".join(paragraphs)


def _clean_cn_cn_repetition(body: str) -> str:
    if not body:
        return body
    companies = ["清华大学", "北京大学", "阿里巴巴达摩院", "百度健康", "平安好医生"]
    paragraphs = re.split(r"\n\s*\n", body)
    cleaned = []
    for para in paragraphs:
        seen = set()
        for company in companies:
            parts = para.split(company)
            if len(parts) > 1:
                para = parts[0] + company + company.join(parts[1:]).replace(company, "")
        cleaned.append(re.sub(r"[，、]{2,}", "，", para))
    return "\n\n".join(cleaned)


def _deduplicate_sentences(text: str) -> str:
    """Removes duplicate sentences within the same paragraph or across the text."""
    if not text:
        return text
    paragraphs = text.split("\n\n")
    cleaned_paras = []
    seen_sentences = set()
    for para in paragraphs:
        sentences = re.split(r'(?<=[.。!?])\s+', para)
        cleaned_sentences = []
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            # Normalize sentence for duplicate check (remove spaces, punctuation, case)
            norm = re.sub(r'[^a-zA-Z0-9가-힣ㄱ-ㅎㅏ-ㅣ一-龠ぁ-ゔァ-ヴー]', '', s_clean).lower()
            if norm:
                if norm in seen_sentences:
                    continue
                seen_sentences.add(norm)
            cleaned_sentences.append(s_clean)
        cleaned_paras.append(" ".join(cleaned_sentences))
    return "\n\n".join(cleaned_paras)


def _polish_cover_letter_body(body: str, country_code: str, has_chinese_language: bool = False) -> str:
    if not body:
        return body

    # Clean missing dot in emails
    body = re.sub(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+)\s+com\b', r'\1.com', body)

    for pattern, replacement in _PHRASE_POLISH:
        body = re.sub(pattern, replacement, body, flags=re.IGNORECASE)

    # Collapse duplicate "ecosystem" in one sentence
    body = re.sub(
        r"(\becosystem\b[^.]{0,120})\becosystem\b",
        r"\1this space",
        body,
        flags=re.IGNORECASE,
    )

    # Detect script type
    has_hangul = bool(re.search(r'[\uac00-\ud7a3]', body))
    has_japanese = bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff]', body))

    # Korean-specific: sanitize leaked CJK/French and deduplicate 생태계
    if has_hangul:
        body = _sanitize_korean_cl(body)
        body = re.sub(r'(생태계[^.]{0,150})생태계', r'\1이 분야', body)
        # Fix awkward Korean closing phrases
        body = body.replace('이 기회를 받아들이는 것에 대해 매우 기대되어 있습니다', '이 기회에 대해 감사드리며, 더 자세한 논의를 기대합니다')
        body = body.replace('매우 기대되어 있습니다', '기대하고 있습니다')
        # Remove FDA references in Korean cover letters (irrelevant for Korea)
        body = re.sub(r'FDA의\s*MLMD\s*지침을[^.。]*[.。]\s*', '', body)
        body = re.sub(r'FDA\s*MLMD[^.。]*[.。]\s*', '', body)
        body = re.sub(r'FDA의[^.。]*지침[^.。]*[.。]\s*', '', body)
    
    # Fail-safe guard for Korea: replace any accidental China content
    if "KR" in country_code or has_hangul:
        body = body.replace("Mandarin Chinese", "Korean")
        body = body.replace("Mandarin", "Korean")
        body = body.replace("Chinese", "Korean")

    # Japanese-specific: remove FDA references (PMDA is the Japanese equivalent)
    if has_japanese:
        body = re.sub(r'FDA[のの]?\s*(?:Machine Learning Model Development|MLMD)?\s*(?:guidance|ガイダンス|指針)[^。.]*[。.]\s*', '', body)

    # Chinese-specific: remove banned Chinese phrases
    if country_code == 'CN_CN' or (not has_hangul and not has_japanese and bool(re.search(r'[\u4e00-\u9fff]', body))):
        body = re.sub(r'我相信自己的能力[^。]*。', '', body)
        body = re.sub(r'美好的未来[^。]*。', '', body)
        body = re.sub(r'我有信心[^。]*。', '', body)
        body = re.sub(r'我相信[^。]*。', '', body)
        body = re.sub(r'非常期待[^。]*。', '', body)
        body = re.sub(r'我非常有信心[^。]*。', '', body)
        body = re.sub(r'期待与您[^。]*。', '', body)
    if country_code == 'CN_CN' and '平安好医生' not in body:
        if '百度健康' in body:
            body = body.replace('百度健康', '百度健康、平安好医生', 1)
        elif '阿里巴巴达摩院' in body:
            body = body.replace('阿里巴巴达摩院', '阿里巴巴达摩院、平安好医生', 1)

    # English cover letters for Japan/Korea: remove out-of-context FDA references
    if country_code in ('JP_EN', 'KR_EN'):
        body = re.sub(r"I also follow FDA[^.]*guidance[^.]*\.\s*", '', body)
        body = re.sub(r"FDA'?s?\s*(?:Machine Learning Model Development\s*\(MLMD\)|MLMD)\s*guidance", 'regulatory guidance on ML medical devices', body)

    body = _ensure_first_person_opening(body)
    if country_code == 'KR_EN':
        body = _append_kr_en_visa(body)
    if country_code == 'CN_EN':
        body = _append_cn_en_requirements(body, allow_language_note=has_chinese_language)

    # Chinese cover letters: remove repeated institution mentions and tighten tone
    if country_code == 'CN_CN':
        body = _clean_cn_cn_repetition(body)

    # Deduplicate sentences to prevent any repeated content
    body = _deduplicate_sentences(body)

    # Capitalize sentences and clean multiple spaces for English cover letters
    if not has_japanese and not has_hangul and not bool(re.search(r'[\u4e00-\u9fff]', body)):
        body = _clean_polished_casing(body)

    body = body.strip()
    if country_code == 'CN_EN':
        body = _sanitize_cover_letter_body(body)
    return body


def _sanitize_cover_letter_body(body: str) -> str:
    """Clean up the generated cover letter body for China English letters."""
    if not body:
        return body
    body = re.sub(r"异常[.．]?pattern\b", "异常", body, flags=re.IGNORECASE)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if len(paragraphs) > 4:
        paragraphs = paragraphs[:3] + [" ".join(paragraphs[3:])]

    companies = ["Tsinghua", "Baidu Health", "Alibaba DAMO Academy", "Ping An Good Doctor", "Peking University"]
    seen = set()
    for i, paragraph in enumerate(paragraphs):
        for company in companies:
            if company in paragraph:
                if company in seen:
                    paragraphs[i] = paragraphs[i].replace(company, "that organization")
                else:
                    seen.add(company)

    z_visa_pattern = re.compile(r'[^.?!]*\b(?:Z(?:[-\s]?work)?\s*visa|Z[-\s]?visa|Z签证)\b[^.?!]*[.?!]', re.IGNORECASE)
    z_visa_sentence = None
    for i, paragraph in enumerate(paragraphs):
        if z_visa_sentence is None:
            match = z_visa_pattern.search(paragraph)
            if match:
                z_visa_sentence = match.group(0).strip()
        paragraphs[i] = z_visa_pattern.sub('', paragraph).strip()
    if z_visa_sentence and paragraphs:
        last_idx = len(paragraphs) - 1
        last_para = paragraphs[last_idx].strip()
        if last_para and last_para[-1] not in '.!?':
            last_para += '.'
        paragraphs[last_idx] = (last_para + ' ' + z_visa_sentence).strip()

    if len(paragraphs) >= 3 and "Ping An Good Doctor" not in body:
        p3 = paragraphs[2]
        if any(name in p3 for name in ["Tsinghua", "Peking University", "Alibaba DAMO Academy", "Baidu Health"]):
            paragraphs[2] = p3.strip() + " I also follow Ping An Good Doctor and its medical AI work in China."
    if len(paragraphs) >= 4:
        p4 = paragraphs[3]
        p4 = re.sub(r"\b(I am confident that|I am excited (about|to)|I am delighted to|By joining|I am eager to)[^.]*\\.\\s*", "", p4, flags=re.IGNORECASE)
        sentences = re.split(r'(?<=[.!?])\s+', p4.strip())
        if len(sentences) > 4 or "welcome the opportunity to discuss" not in p4.lower():
            p4 = "I welcome the opportunity to discuss how I can contribute to your team and support the visa process. I am prepared to relocate to China and can begin once sponsorship is arranged."
        p4 = re.sub(r'\bprogress(?:ion)?\s+I am prepared\b', r'progress. I am prepared', p4)
        paragraphs[3] = p4.strip()

    paragraphs = [p for p in paragraphs if p]
    return "\n\n".join(paragraphs)


def _remove_mandarin_language_reference(body: str) -> str:
    if not body:
        return body
    # Aggressively remove any Mandarin/Chinese study mentions in many phrasings
    body = re.sub(r'\s*I am currently studying Mandarin Chinese[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*As a beginner-level Mandarin speaker[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*As a beginner level Mandarin speaker[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*I[\'’]m currently studying Mandarin Chinese[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*I am currently studying Mandarin[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*I am currently learning Mandarin[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*I am currently studying Chinese[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*I am currently learning Chinese[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*My proficiency in languages? such as [^.?!]*\bChinese\b[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*My language proficiency[^.?!]*\bChinese\b[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'[^.?!]*\b(?:Chinese|Mandarin)\b[^.?!]*\b(?:language|languages|proficiency|speak|speaking|study|studying|learn|learning|ability|integration|genuine)\b[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*I am currently studying Mandarin Chinese[^.?!]*?\b(?:language|ability|integration|genuine|team)\b[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*I am currently learning Mandarin Chinese[^.?!]*?\b(?:language|ability|integration|genuine|team)\b[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*I am currently studying Mandarin[^.?!]*?\b(?:language|ability|integration|genuine|team)\b[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*I am currently learning Mandarin[^.?!]*?\b(?:language|ability|integration|genuine|team)\b[^.?!]*?(?:[.?!]|$)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\s*目前[，,]?我正在(?:系统)?学习普通话[^。]*。', '', body)
    body = re.sub(r'\s*我正在(?:系统)?学习普通话[^。]*。', '', body)
    body = re.sub(r'\s*普通话[^。]*学习[^。]*。', '', body)
    body = re.sub(r'[^。！？]*(?:语言学习|学习语言|语言能力|语言技能|继续学习|提升语言|继续提升语言能力)[^。！？]*[。！？]', '', body)
    # Fix grammar where a missing period joins clauses like "steady progress I am prepared"
    body = re.sub(r'(progress)\s+I\s+am\s+prepared', r'\1. I am prepared', body, flags=re.IGNORECASE)
    body = re.sub(r'(progress)\s+I\'m\s+prepared', r'\1. I\'m prepared', body, flags=re.IGNORECASE)
    # Remove any leftover short mentions of 'Mandarin' or 'Chinese' that stand alone
    body = re.sub(r'\b(Mandarin|Chinese|普通话|汉语|中文)\b', '', body, flags=re.IGNORECASE)
    return re.sub(r'\n{2,}', '\n\n', body).strip()

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

def _is_contact_line(clean_line: str) -> bool:
    clean_lower = clean_line.lower()
    # Check for name parts
    names = ["divya", "nirankari", "dvnirankari", "ディヴィア", "ニランカリ", "디비아", "니란카리"]
    if any(n in clean_lower for n in names):
        return True
    # Check for email
    if "@" in clean_lower or "gmail" in clean_lower or "mail" in clean_lower or "邮箱" in clean_lower or "이메일" in clean_lower or "メール" in clean_lower:
        return True
    # Check for phone keywords
    phone_kws = ["phone", "tel", "mobile", "contact", "电话", "電話", "전화", "연락처", "+91"]
    if any(pk in clean_lower for pk in phone_kws):
        return True
    # Check for location/address keywords
    locs = ["surat", "gujarat", "india", "スーラト", "グジャラート", "インド", "수라트", "구자라트", "인도", "苏拉特", "古吉拉特", "印度"]
    if any(lc in clean_lower for lc in locs):
        return True
    # Check for generic phone pattern (e.g. +91 9265768306 or similar numbers)
    if re.search(r'\+?\d{2,4}[-.\s]?\d{3,5}[-.\s]?\d{3,5}', clean_line):
        return True
    return False

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
        
        if is_salutation or _is_contact_line(clean_line):
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
                "yours faithfully", "best wishes", "thank you", "thanks"
            ]
        ) or any(
            p in clean_line for p in [
                "敬具", "此致", "敬礼", "위 내용이", "사실임을 확인합니다",
                "감사합니다", "고맙습니다", "검토", "よろしく", "宜しく", "ご検討",
                "ありがとうございました", "感谢", "谢谢", "盼复"
            ]
        )
        
        if is_signoff or _is_contact_line(clean_line):
            end_idx -= 1
        else:
            break
            
    body_lines = lines[start_idx:end_idx]
    return '\n'.join(body_lines).strip()


# ─── HELPER: SECTION-BY-SECTION TRANSLATION ────────────────────────────────────
async def translate_cover_letter_body(clean_body: str, lang: str, country_code: str = "") -> str:
    """
    Translates the cover letter body. Korean 자기소개서 keeps section headings;
    Chinese/Japanese/English use flowing prose without labels.
    """
    if country_code in ("JP_JA", "KR_KO", "CN_CN"):
        return _polish_cover_letter_body(clean_body, country_code)

    from services.translations import translate_text

    prose_mode = lang in ("en", "zh", "ja") or country_code not in SECTIONED_COVER_CODES
    if prose_mode:
        prose_body = _to_prose_paragraphs(clean_body)
        chunks = [p.strip() for p in re.split(r"\n\s*\n", prose_body) if p.strip()]
        if not chunks:
            chunks = [prose_body] if prose_body.strip() else []
        translated = []
        for i, chunk in enumerate(chunks):
            translated.append(
                await translate_text(chunk, lang, field_name=f"cl_para_{i}")
            )
        # Join with double newline so the template can split on \n\n into proper paragraphs
        return _polish_cover_letter_body("\n\n".join(translated), country_code)

    sections = [
        ("Growth", ["**Growth**", "**グロース**", "**成長・実績**", "**成長**", "**성장**", "**成长**"]),
        ("Traits", ["**Traits**", "**特徴**", "**특성**", "**역량**", "**特质**"]),
        ("Motivation", ["**Motivation**", "**動機**", "**동기**", "**动机**"]),
        ("Goal", ["**Goal**", "**Goals**", "**目標**", "**목표**", "**目标**"])
    ]
    
    lines = clean_body.split("\n")
    parsed_sections = {}
    current_section = "intro"
    parsed_sections[current_section] = []
    
    for line in lines:
        cleaned_line = line.strip()
        found_header = None
        for sec_name, sec_headers in sections:
            if any(cleaned_line.lower() == h.lower() or cleaned_line.lower().startswith(h.lower()) for h in sec_headers) or any(h.lower() in cleaned_line.lower() and "**" in cleaned_line for h in ["growth", "traits", "motivation", "goal"]):
                for s_n, s_hs in sections:
                    if s_n.lower() in cleaned_line.lower() or any(h.lower() in cleaned_line.lower() for h in s_hs):
                        found_header = s_n
                        break
                if found_header:
                    break
        
        if found_header:
            current_section = found_header
            parsed_sections[current_section] = []
        else:
            parsed_sections[current_section].append(line)
            
    translated_parts = []
    
    header_translations = {
        "ja": {
            "Growth": "**成長・実績**",
            "Traits": "**長所・短所**",
            "Motivation": "**志望動機**",
            "Goal": "**入社後の目標**"
        },
        "ko": {
            "Growth": "**성장과정**",
            "Traits": "**역량**",
            "Motivation": "**지원동기**",
            "Goal": "**입사 후 포부**"
        },
        "zh": {
            "Growth": "**成长**",
            "Traits": "**特质**",
            "Motivation": "**动机**",
            "Goal": "**目标**"
        }
    }
    
    if parsed_sections.get("intro"):
        intro_text = "\n".join(parsed_sections["intro"]).strip()
        if intro_text:
            trans_intro = await translate_text(intro_text, lang, field_name="cl_intro")
            translated_parts.append(trans_intro)
            
    for sec_name, _ in sections:
        if sec_name in parsed_sections:
            sec_text = "\n".join(parsed_sections[sec_name]).strip()
            if sec_text:
                heading = header_translations.get(lang, {}).get(sec_name, f"**{sec_name}**")
                trans_text = await translate_text(sec_text, lang, field_name=f"cl_{sec_name.lower()}")
                translated_parts.append(f"{heading}\n\n{trans_text}")
                
    result = "\n\n".join(translated_parts)
    return _polish_cover_letter_body(result, country_code or "KR_KO")


# ─── HELPER: ASSEMBLE FULL LETTER ─────────────────────────────────────────────
def _assemble_letter(country_code: str, body: str, phone: str, date_str: str) -> str:
    """
    Wraps the AI-generated body with the correct salutation and sign-off.
    """
    salutation = SALUTATIONS.get(country_code, SALUTATIONS["DEFAULT"])
    signoff_template = SIGNOFFS.get(country_code, SIGNOFFS["US"])
    signoff = signoff_template.format(phone=phone, date_str=date_str)
    body = body.strip()
    
    # Strip leading/trailing newlines from signoff to control spacing explicitly
    signoff_clean = signoff.strip()
    letter = f"{salutation}{body}\n\n{signoff_clean}"
    
    # Collapse runaway blank lines before the valediction (pre-wrap renders each as a full line).
    valediction = signoff_clean.split("\n", 1)[0]
    if valediction:
        letter = re.sub(
            rf"\n{{3,}}({re.escape(valediction)})",
            r"\n\n\1",
            letter,
        )
    return letter


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

    region_key_map = {
        'japan': 'JP', 'korea': 'KR', 'china': 'CN',
        'germany': 'DE', 'uk': 'UK', 'usa': 'US',
        'india': 'IN', 'uae': 'AE', 'middleeast': 'AE', 'international': 'GLOBAL'
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

    # 2. Extract minimal resume payload to avoid token bloat
    config = COUNTRY_CONFIGS.get(country_code, COUNTRY_CONFIGS["US"])
    resume_languages = []
    for lang_item in resume_data.get('languages', []):
        if isinstance(lang_item, dict):
            if lang_item.get('visible') is False:
                continue
            label = lang_item.get('label') or lang_item.get('name') or ''
        else:
            label = str(lang_item)
        if label:
            resume_languages.append(label)
    has_chinese_language = any(
        re.search(r'\b(mandarin|chinese|普通话|汉语|中文)\b', label, flags=re.IGNORECASE)
        for label in resume_languages
    )
    
    min_data = {
        "personal": {
            "name": resume_data.get('personal', {}).get('name'),
            "role": resume_data.get('personal', {}).get('role') or resume_data.get('profile', {}).get('role'),
            "summary": resume_data.get('personal', {}).get('summary') or resume_data.get('profile', {}).get('summary')
        },
        "experience": [
            {
                "role": exp.get('role'),
                "company": exp.get('company'),
                "metric": exp.get('metric') or exp.get('description', '')[:200]
            }
            for exp in resume_data.get('experience', [])[:3]
        ],
        "projects": [
            {
                "name": p.get('name'),
                "metric": p.get('metric') or p.get('summary', '')[:200]
            }
            for p in resume_data.get('projects', [])[:5]
        ],
        "research": [
            {
                "title": r.get('title'),
                "metric": r.get('metric') or r.get('summary', '')[:160]
            }
            for r in resume_data.get('research', [])[:3]
        ],
        "skills": [c.get('label') for c in resume_data.get('skillCategories', [])],
        "languages": resume_languages,
        "visa_statement": resume_data.get('profile', {}).get('visa', {}).get(
            'CN' if country_code == 'CN_CN' else
            'KR' if country_code == 'KR_KO' else
            'JP' if country_code == 'JP_JA' else
            country_code,
            resume_data.get('profile', {}).get('visa', {}).get(
                base_code,
                resume_data.get('profile', {}).get('visa', {}).get('GLOBAL', 'Relocation sponsorship required')
            )
        )
    }

    # 3. Check cache for base English clean body (ignores lang suffix)
    # This guarantees that the native resume and the English resume share the exact same generated clean body!
    base_cache_key = hashlib.md5(
        f"v2-prose_{country_code}_{json.dumps(min_data, sort_keys=True)}".encode()
    ).hexdigest()
    
    clean_body = None
    if base_cache_key in CL_CACHE:
        clean_body, cache_time = CL_CACHE[base_cache_key]
        if time.time() - cache_time > 3600:
            clean_body = None

    if not clean_body:
        language_note = config['language_note'] if has_chinese_language else ""
        user_prompt = f"""Generate a cover letter body for this candidate applying to companies in {config['country_name']}.

--- CANDIDATE DATA ---
{json.dumps(min_data, indent=2, ensure_ascii=False)}

--- COUNTRY CONTEXT ---
Country: {config['country_name']}
Ecosystem: {config['ecosystem']}
Tone: {config['tone']}
Visa: {min_data['visa_statement']}
{f"Language note: {language_note}" if language_note else ""}

--- REMINDER ---
- Each paragraph must be 4–5 sentences. Do not truncate outputs early.
- Do NOT mention years of experience as a number.
- Do NOT use section headings or bold labels — flowing paragraphs only (except KR_KO structured format).
- Do NOT repeat the same company or institution name across multiple paragraphs.
- Paragraph 3 MUST name {config['country_name']} and two specific local institutions/companies from the ecosystem context.
- Paragraph 4 MUST be concise, avoid repetition, include the visa statement, and contain "welcome the opportunity to discuss" (not "invite you to talk").
- Never use "Aspiring" to describe the candidate.
- Return ONLY the letter body. No salutation. No sign-off. No preamble."""

        # 5. Call AI with retry to generate English base letter
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return ""

        system_content = SYSTEM_PROMPT
        if country_code in NATIVE_LANG_ADDITIONS:
            system_content += NATIVE_LANG_ADDITIONS[country_code]

        model_to_use = "llama-3.3-70b-versatile"
        for attempt in range(3):
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
                                {"role": "system", "content": system_content},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0.75,
                            "max_tokens": 3500
                        },
                        timeout=90.0
                    )

                    if response.status_code == 429:
                        if attempt < 2:
                            wait_time = (attempt + 1) * 5
                            print(f"Rate limit hit on {model_to_use}. Waiting {wait_time}s before retry...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"Rate limit hit on {model_to_use} after retries. Falling back to llama-3.1-8b-instant...")
                            model_to_use = "llama-3.1-8b-instant"
                            continue

                    res_json = response.json()
                    if 'choices' not in res_json:
                        return ""

                    raw_body = res_json['choices'][0]['message']['content'].strip()

                    # Strip any AI-added preamble/sign-off
                    clean_body = _strip_ai_preamble(raw_body, country_code)

                    # Save the clean English body to cache
                    if len(CL_CACHE) < CL_CACHE_MAX_SIZE:
                        CL_CACHE[base_cache_key] = (clean_body, time.time())
                    break
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(2)

    # 5b. Guard: if all retries failed, clean_body is still None → return empty
    if not clean_body:
        print(f"[cover_letter] All API attempts failed for {country_code}. Returning empty.")
        return ""

    # 6. Prose format + phrase polish (English base)
    if country_code not in SECTIONED_COVER_CODES:
        clean_body = _to_prose_paragraphs(clean_body)
    clean_body = _strip_years_phrasing(clean_body)
    clean_body = _polish_cover_letter_body(clean_body, country_code, has_chinese_language=has_chinese_language)

    # 7. Translate the clean body if target language is not English
    if lang != 'en':
        clean_body = await translate_cover_letter_body(clean_body, lang, country_code)
    elif country_code not in SECTIONED_COVER_CODES:
        clean_body = _to_prose_paragraphs(clean_body)

    if not has_chinese_language and country_code in ('CN_EN', 'CN_CN'):
        clean_body = _remove_mandarin_language_reference(clean_body)



    # 7.5. Dynamic Signoff/Date info
    profile = resume_data.get('profile', {})
    phone_val = profile.get('phone') or ""
    phone_alt = profile.get('alternate_phone') or ""
    if phone_val and phone_alt:
        phone_full = f"{phone_val} / {phone_alt}"
    else:
        phone_full = (phone_val or phone_alt or "+91 9265768306").strip()
        if not phone_full:
            phone_full = "+91 9265768306"

    # Localized date
    from datetime import datetime
    now = datetime.now()
    if lang == 'ko':
        date_str = f"{now.year}년 {now.month}월"
    elif lang == 'ja':
        date_str = f"{now.year}年{now.month}月"
    elif lang == 'zh':
        date_str = f"{now.year}年{now.month}月"
    else:
        month_name = now.strftime("%B")
        date_str = f"{month_name} {now.year}"

    # 8. Assemble the full letter with salutation + signoff
    full_letter = _assemble_letter(country_code, clean_body, phone=phone_full, date_str=date_str)

    return full_letter


# ─── HELPER: STRIP YEARS PHRASING ────────────────────────────────────────────
def _strip_years_phrasing(text: str) -> str:
    """
    Removes 'X+ years', 'X years of experience' etc.
    """
    patterns = [
        r'\b\d+\+?\s+years?\s+of\s+(?:experience|expertise)\b',
        r'\bover\s+\d+\+?\s+years?\b',
        r'\b\d+\+?\s+years?\b',
        r'\bwith\s+\d+\+?\s+years?\b',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    text = re.sub(r'  +', ' ', text).strip()
    return text

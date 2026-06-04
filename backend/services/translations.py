import sqlite3
import json
import os
import re
import asyncio
from typing import List, Dict, Optional, Tuple
from deep_translator import GoogleTranslator

# ─── TRANSLATION CACHE (SQLite) ────────────────────────────────────────────────
from database import get_cached_translation, save_translation

# ─── REGIONAL VISA STATUS (resume display) ─────────────────────────────────────
CN_VISA_ZH_DEFAULT = "需要工作签证（Z签证），需由用人单位协助办理。"
EN_VISA_TO_ZH = {
    "Requires Z work visa sponsorship (Technology/Engineering category)": "需要工作签证（Z签证，技术/工程类），需由用人单位协助办理。",
    "Requires Z-visa sponsorship for employment in China.": "需要工作签证（Z签证），需由用人单位协助办理。",
    "需要工作签证（Z签证）办理。": "需要工作签证（Z签证）办理。",
    "需要工作签证（Z签证），需由用人单位协助办理。": "需要工作签证（Z签证），需由用人单位协助办理。",
}


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def resolve_region_visa_status(
    visa_map: dict,
    region_key: str,
    lang: str,
    *,
    existing: str = "",
) -> str:
    """
    Pick the visa line for a region/language.
    Admin text in profile.visa.{region} is always respected when set.
    Known English boilerplate for CN is mapped to Chinese; custom English is
    left as-is for the translation pipeline. Default Chinese is used only when empty.
    """
    visa_map = visa_map or {}
    if region_key == "CN":
        admin_cn = visa_map.get("CN", "").strip()
        admin_cn_en = visa_map.get("CN_EN", "").strip()
        if lang == "en":
            return (
                admin_cn_en
                or (existing or "").strip()
                or admin_cn
            )
        # zh — prefer admin China Visa field, then personal override
        if admin_cn:
            if _has_cjk(admin_cn):
                return admin_cn
            return EN_VISA_TO_ZH.get(admin_cn, admin_cn)
        if existing:
            return existing.strip()
        return CN_VISA_ZH_DEFAULT

    if lang == "en" and region_key in ("JP", "KR"):
        for key in (f"{region_key}_EN", region_key, "GLOBAL"):
            if visa_map.get(key):
                return visa_map[key]
        return (existing or "").strip()

    for key in (region_key, region_key.lower() if region_key else "", "GLOBAL"):
        if key and visa_map.get(key):
            return visa_map[key]
    return (existing or "").strip()


# ─── LABELS ───────────────────────────────────────────────────────────────────
LABELS = {
    "en": {
        "rirekisho_title": "Resume",
        "shokumu_title": "Job History",
        "jagi_title": "Cover Letter",
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
        "kakaotalk_id": "KakaoTalk ID",
        "wechat_id": "WeChat ID",
        "education": "Education",
        "work_experience": "Work Experience",
        "projects": "Technical Projects",
        "research": "Research in Progress",
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
        "cert_name_label": "Certificate/Exam",
        "cert_issuer_label": "Issuing Organization",
        "cert_date_label": "Acquisition Date",
        "generated_at": "Generated on:",
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
        "confirmation_text": "I hereby certify that the above statements are true and correct.",
        "job_duties_label": "Key Responsibilities",
        "achievements_label": "Key Achievements",
        "year_char": "",
        "writing_status": "In Progress",
        "proficient_label": "Proficient",
        "present": "Present",
        "korean_level": "Korean",
        "skills_label": "Skills"
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
        "fulltime": "正社員",
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
        "cert_name_label": "資格・試験名",
        "cert_issuer_label": "授与機関",
        "cert_date_label": "取得年月",
        "desired_conditions_label": "本人希望記入欄（特に給料・職種・勤務時間・勤務地・その他についての希望などがあれば記入）",
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
        "married": "既婚",
        "self_pr_label": "自己PR",
        "commute_time_label": "通勤時間",
        "dependents_label": "扶養家族数（配偶者を除く）",
        "people_count": "人",
        "spouse_label": "配偶者",
        "spouse_dependency_label": "配偶者の扶養義務",
        "instructions_label": "上記のとおり相違ありません。",
        "cl_header": "応募書類の送付につきまして",
        "cl_growth": "成長・実績",
        "cl_strengths": "長所・短所",
        "cl_motivation": "志望動機",
        "cl_goals": "入社後の目標",
        "job_duties_label": "職務内容",
        "achievements_label": "主な実績",
        "year_char": "年",
        "writing_status": "執筆中",
        "proficient_label": "熟練",
        "present": "現在",
        "projects": "プロジェクト経歴",
        "skills_label": "スキル",
        "end_of_doc": "以上"
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
        "kakaotalk_id": "카카오톡 ID",
        "photo": "사 진",
        "education": "학 력 사 항",
        "work_experience": "경 력 사 항",
        "certificates": "자격 및 면허",
        "cert_exam_label": "자격/시험",
        "cert_name_label": "자격/시험명",
        "cert_issuer_label": "발급 기관",
        "cert_date_label": "취득일",
        "remarks_label": "비고",
        "awards": "수상 경력",
        "skills": "보유 기술",
        "languages": "어학 능력",
        "research": "연구 및 프로젝트",
        "date_label": "작성일:",
        "cl_growth": "성장과정",
        "cl_strengths": "역량",
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
        "desired_conditions_label": "본인 희망 기입란",
        "single": "미혼",
        "married": "기혼",
        "job_duties_label": "담당 업무",
        "achievements_label": "주요 성과",
        "hobbies": "취미 및 특기",
        "year_char": "년",
        "writing_status": "작성 중",
        "proficient_label": "숙련",
        "present": "현재",
        "korean_level": "한국어",
        "projects": "주요 프로젝트",
        "skills_label": "기술",
        "end_of_doc": "이하 여백"
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
        "wechat_id": "微信号",
        "photo": "照片",
        "education": "教育背景",
        "work_experience": "工作经历",
        "certificates": "专业证书",
        "cert_exam_label": "证书/考试",
        "cert_name_label": "证书/考试名称",
        "cert_issuer_label": "颁发机构",
        "cert_date_label": "获得时间",
        "remarks_label": "备注",
        "awards": "获奖荣誉",
        "skills": "专业技能",
        "languages": "语言能力",
        "research": "科研经历",
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
        "married": "已婚",
        "cl_growth": "成长历程",
        "cl_strengths": "性格特质",
        "cl_motivation": "求职动机",
        "cl_goals": "入职目标",
        "job_duties_label": "工作职责",
        "achievements_label": "主要业绩",
        "hobbies": "兴趣爱好",
        "year_char": "年",
        "writing_status": "进行中",
        "proficient_label": "熟练",
        "present": "至今",
        "projects": "项目经历",
        "skills_label": "技能",
        "end_of_doc": "以下空白"
    }
}
RESUME_TERM_TRANSLATIONS = {
    "ja": {
        "Gujarat University": "グジャラート大学",
        "Gujarat Technological University": "グジャラート工科大学",
        "Data Structure Excellence Award": "データ構造優秀賞",
        "Database Management System Award": "データベース管理システム優秀賞",
        "Student of the Year": "最優秀学生賞",
        "Most Diligent Employee": "最優秀社員賞",
        "AI-Engineer-Portfolio": "AI-Engineer-Portfolio",
        "Deep Learning Architectures for Cardiac Abnormality Detection using 1D ResNet": "1D ResNetを用いた心臓異常検出のためのディープラーニングアーキテクチャ",
        "Optimized PostgreSQL queries reducing average response time by 40%": "PostgreSQLクエリを最適化し、平均応答時間を40%削減",
        "10k+ daily requests": "1日あたり1万件以上のリクエスト",
        "Logixbuilt Infotech": "Logixbuilt Infotech",
        "Python & AI/ML Engineer": "Python・AI/MLエンジニア",
        "Python Software Engineer": "Pythonソフトウェアエンジニア",
        "Full Stack / Lead Developer": "フルスタック／リードデベロッパー",
        "Lead Developer / Full Stack Engineer": "リードデベロッパー／フルスタックエンジニア",
        "Freelance": "フリーランス",
        "Writing": "執筆中",
        "In Progress": "進行中"
    },
    "ko": {
        "Gujarat University": "구자라트 대학교",
        "Gujarat Technological University": "구자라트 기술 대학교",
        "Data Structure Excellence Award": "데이터 구조 우수상",
        "Database Management System Award": "데이터베이스 관리 시스템 우수상",
        "Student of the Year": "올해의 학생상",
        "Most Diligent Employee": "최우수 사원상",
        "AI-Engineer-Portfolio": "AI-Engineer-Portfolio",
        "Deep Learning Architectures for Cardiac Abnormality Detection using 1D ResNet": "1D ResNet을 이용한 심장 이상 감지를 위한 딥러닝 아키텍처",
        "Optimized PostgreSQL queries reducing average response time by 40%": "PostgreSQL 쿼리 최적화로 평균 응답 시간 40% 단축",
        "10k+ daily requests": "일일 1만 건 이상의 요청",
        "Logixbuilt Infotech": "Logixbuilt Infotech",
        "Python & AI/ML Engineer": "Python 및 AI/ML 엔지니어",
        "Python Software Engineer": "Python 소프트웨어 엔지니어",
        "Full Stack / Lead Developer": "풀스택 / 리드 개발자",
        "Lead Developer / Full Stack Engineer": "리드 개발자 / 풀스택 엔지니어",
        "Freelance": "프리랜서",
        "Writing": "작성 중",
        "In Progress": "진행 중"
    },
    "zh": {
        "Gujarat University": "古吉拉特大学",
        "Gujarat Technological University": "古吉拉特科技大学",
        "Data Structure Excellence Award": "数据结构优秀奖",
        "Database Management System Award": "数据库管理系统优秀奖",
        "Student of the Year": "年度优秀学生",
        "Most Diligent Employee": "最优秀员工奖",
        "AI-Engineer-Portfolio": "AI-Engineer-Portfolio",
        "Deep Learning Architectures for Cardiac Abnormality Detection using 1D ResNet": "基于1D ResNet的心脏异常检测深度学习架构",
        "Optimized PostgreSQL queries reducing average response time by 40%": "优化PostgreSQL查询，使平均响应时间减少40%",
        "10k+ daily requests": "每日1万次以上的请求",
        "Logixbuilt Infotech": "Logixbuilt Infotech",
        # Geography terms — prevent Google Translate from garbling these
        "UAE": "阿联酋",
        "India, UAE, Europe": "印度、阿联酋、欧洲",
        "India, UAE, and Europe": "印度、阿联酋和欧洲",
        "India, semiconductor, Europe": "印度、阿联酋、欧洲",
        "Python & AI/ML Engineer": "Python/AI/ML工程师",
        "Python Software Engineer": "Python软件工程师",
        "Full Stack / Lead Developer": "全栈/主开发人员",
        "Lead Developer / Full Stack Engineer": "全栈/主开发人员",
        "Freelance": "自由职业",
        "Writing": "进行中",
        "In Progress": "进行中"
    }
}

# Unified Proficiency Mapping (to be used across all templates)
PROFICIENCY_LEVELS = {
    "en": {
        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "experienced": "Experienced",
        "advanced": "Advanced",
        "expert": "Expert"
    },
    "ja": {
        "beginner": "初級",
        "intermediate": "中級",
        "experienced": "経験豊富",
        "advanced": "上級",
        "expert": "エキスパート"
    },
    "ko": {
        "beginner": "초급",
        "intermediate": "중급",
        "experienced": "경험 풍부",
        "advanced": "고급",
        "expert": "전문가"
    },
    "zh": {
        "beginner": "初级",
        "intermediate": "中级",
        "experienced": "经验丰富",
        "advanced": "高级",
        "expert": "专家"
    }
}

NEVER_TRANSLATE = frozenset({
    "exp_bullet",
    "proj_summary",
    "proj_desc",
    "res_desc",
    "exp_desc",
})

STATIC_ONLY = frozenset({
    "exp_role",
    "exp_company",
    "proj_name",
    "proj_role",
    "edu_university",
    "edu_uni",
    "nationality",
    "res_status",
    "ach_issuer",
    "cert_issuer",
})

# ─── PROMPTS ──────────────────────────────────────────────────────────────────
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
    return bool(re.search(r'[\u3040-\u30ff]', text))

def contains_korean(text: str) -> bool:
    return bool(re.search(r'[\uac00-\ud7af]', text))

def contains_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def is_sufficiently_translated(text: str, target_lang: str) -> bool:
    """
    Checks if a text is already sufficiently translated to the target language
    by calculating the ratio of target language letters to total letters.
    Returns True if the ratio is >= 0.60, indicating it's already translated.
    """
    if not text:
        return True
        
    total_letters = 0
    target_count = 0
    
    for char in text:
        if char.isspace() or char.isdigit() or char in '.,;:!?()[]{}<>-_+=/*&^%$#@!~`|\'"\\':
            continue
            
        total_letters += 1
        val = ord(char)
        if target_lang == "ja":
            # Hiragana (0x3040-0x309F), Katakana (0x30A0-0x30FF), Kanji (0x4E00-0x9FFF)
            if (0x3040 <= val <= 0x30ff) or (0x4e00 <= val <= 0x9fff):
                target_count += 1
        elif target_lang == "ko":
            # Hangul Syllables (0xAC00-0xD7AF), Hangul Jamo (0x1100-0x11FF), Hangul Compatibility Jamo (0x3130-0x318F)
            if (0xac00 <= val <= 0xd7af) or (0x1100 <= val <= 0x11ff) or (0x3130 <= val <= 0x318f):
                target_count += 1
        elif target_lang == "zh":
            # CJK Unified Ideographs (0x4E00-0x9FFF)
            if 0x4e00 <= val <= 0x9fff:
                target_count += 1
                
    if total_letters == 0:
        return True
        
    ratio = target_count / total_letters
    return ratio >= 0.60


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

def get_translator(target_lang: str) -> GoogleTranslator:
    """Helper to map our lang codes to deep-translator codes."""
    lang_map = {
        "ja": "ja",
        "ko": "ko",
        "zh": "zh-CN",
        "de": "de",
        "fr": "fr",
        "en": "en"
    }
    return GoogleTranslator(source='en', target=lang_map.get(target_lang, target_lang))

def translate_text_sync(text: str, target_lang: str, field_name: str = "generic", verified_only: bool = False) -> str:
    """Synchronously translates text using deep-translator (Google) with SQLite caching."""
    if not text or target_lang == "en":
        return text
    
    # Tier 1 guard: NEVER_TRANSLATE fields are kept in English
    if field_name in NEVER_TRANSLATE:
        return text

    # Check static dict first
    cleaned = text.strip()
    term_dict = RESUME_TERM_TRANSLATIONS.get(target_lang, {})
    if cleaned in term_dict:
        return term_dict[cleaned]

    # Tier 2 guard: STATIC_ONLY fields are only translated if they match static dict
    if field_name in STATIC_ONLY:
        return text

    # skip if already in target language
    if target_lang in ("ja", "ko", "zh") and is_sufficiently_translated(text, target_lang):
        return text

    # 1. Check Cache
    cached = get_cached_translation(field_name, target_lang, text)
    if cached:
        if not verified_only or cached[1] == 1:
            return cached[0]
        if verified_only:
            return text

    if verified_only:
        return text

    try:
        translator = get_translator(target_lang)
        translated = translator.translate(text).strip()
        save_translation(field_name, target_lang, text, translated, is_verified=False)
        return translated
    except Exception as e:
        print(f"Deep-translator sync error: {e}")
        return text


def translate_batch_sync(items: List[Dict[str, str]], target_lang: str, verified_only: bool = False) -> List[str]:
    """Synchronously translates multiple texts using deep-translator with SQLite caching."""
    if not items:
        return []
    
    results = [None] * len(items)
    to_translate_indices = []
    texts_to_translate = []

    for i, item in enumerate(items):
        text = item["text"]
        field = item.get("field_name", "generic")
        if not text:
            results[i] = ""
            continue

        # Tier 1 guard
        if field in NEVER_TRANSLATE:
            results[i] = text
            continue

        term = text.strip()
        if target_lang in RESUME_TERM_TRANSLATIONS and term in RESUME_TERM_TRANSLATIONS[target_lang]:
            results[i] = RESUME_TERM_TRANSLATIONS[target_lang][term]
            continue

        # Tier 2 guard
        if field in STATIC_ONLY:
            results[i] = text
            continue

        cached = get_cached_translation(field, target_lang, text)
        if cached:
            if not verified_only or cached[1] == 1:
                results[i] = cached[0]
            else:
                results[i] = text
        elif target_lang in ("ja", "ko", "zh") and is_sufficiently_translated(text, target_lang):
            results[i] = text
        else:
            if verified_only:
                results[i] = text
            else:
                to_translate_indices.append(i)
                texts_to_translate.append(text)

    if texts_to_translate:
        try:
            translator = get_translator(target_lang)
            translated_list = translator.translate_batch(texts_to_translate)
            for idx, translated_text in zip(to_translate_indices, translated_list):
                if not translated_text:
                    results[idx] = items[idx]["text"]
                    continue
                results[idx] = translated_text.strip()
                save_translation(items[idx].get("field_name", "generic"), target_lang, items[idx]["text"], results[idx], is_verified=False)
        except Exception as e:
            print(f"Deep-translator batch sync error: {e}")
            for idx in to_translate_indices:
                results[idx] = translate_text_sync(items[idx]["text"], target_lang, items[idx].get("field_name", "generic"), verified_only=verified_only)

    return [r if r is not None else items[i]["text"] for i, r in enumerate(results)]


async def translate_text(text: str, target_lang: str, field_name: str = "generic", verified_only: bool = False) -> str:
    """Translates text using deep-translator (Google) with SQLite caching."""
    if not text or target_lang == "en":
        return text
    
    # Tier 1 guard: NEVER_TRANSLATE fields are kept in English
    if field_name in NEVER_TRANSLATE:
        return text

    # Check static dict first
    cleaned = text.strip()
    term_dict = RESUME_TERM_TRANSLATIONS.get(target_lang, {})
    if cleaned in term_dict:
        return term_dict[cleaned]

    # Tier 2 guard: STATIC_ONLY fields are only translated if they match static dict
    if field_name in STATIC_ONLY:
        return text

    # skip if already in target language
    if target_lang in ("ja", "ko", "zh") and is_sufficiently_translated(text, target_lang):
        return text

    # 1. Check Cache
    cached = get_cached_translation(field_name, target_lang, text)
    if cached:
        if not verified_only or cached[1] == 1:
            return cached[0] # translated_text
        if verified_only:
            return text

    if verified_only:
        return text

    # 2. Call deep-translator (asynchronous wrapper)
    try:
        translator = get_translator(target_lang)
        # Call translator.translate synchronously to avoid threading and event loop executor shutdown issues in Playwright tasks
        translated = translator.translate(text)
        translated = translated.strip()
        
        # 3. Save to Cache
        save_translation(field_name, target_lang, text, translated, is_verified=False)
        
        return translated
    except Exception as e:
        print(f"Deep-translator error: {e}")
        return text # Fallback to original English

async def translate_batch(items: List[Dict[str, str]], target_lang: str, verified_only: bool = False) -> List[str]:
    """
    Translates multiple strings in a single batch using deep-translator.
    items: List of {"text": "...", "field_name": "..."}
    """
    if not items:
        return []
    
    if target_lang == "en":
        return [item["text"] for item in items]

    results = [None] * len(items)
    to_translate_indices = []
    texts_to_translate = []

    # 1. Check Cache and static terms first
    for i, item in enumerate(items):
        text = item["text"]
        field = item["field_name"]
        if not text:
            results[i] = ""
            continue
            
        # Tier 1 guard
        if field in NEVER_TRANSLATE:
            results[i] = text
            continue

        term = text.strip()
        if target_lang in RESUME_TERM_TRANSLATIONS and term in RESUME_TERM_TRANSLATIONS[target_lang]:
            results[i] = RESUME_TERM_TRANSLATIONS[target_lang][term]
            continue
            
        # Tier 2 guard
        if field in STATIC_ONLY:
            results[i] = text
            continue

        cached = get_cached_translation(field, target_lang, text)
        if cached:
            if not verified_only or cached[1] == 1:
                results[i] = cached[0]
            else:
                results[i] = text
        elif target_lang in ("ja", "ko", "zh") and is_sufficiently_translated(text, target_lang):
            results[i] = text
        else:
            if verified_only:
                results[i] = text
            else:
                to_translate_indices.append(i)
                texts_to_translate.append(text)

    if not texts_to_translate:
        return results

    # 2. Call deep-translator batch
    try:
        translator = get_translator(target_lang)
        # Call translator.translate_batch synchronously to avoid threading and event loop executor shutdown issues in Playwright tasks
        translated_list = translator.translate_batch(texts_to_translate)
        
        for idx, translated_text in zip(to_translate_indices, translated_list):
            if not translated_text:
                results[idx] = items[idx]["text"]
                continue
                
            translated_text = translated_text.strip()
            results[idx] = translated_text
            save_translation(items[idx]["field_name"], target_lang, items[idx]["text"], translated_text, is_verified=False)
            
    except Exception as e:
        print(f"Deep-translator batch error: {e}")
        # Fallback to individual translations if batch fails
        for idx in to_translate_indices:
            if results[idx] is None:
                results[idx] = await translate_text(items[idx]["text"], target_lang, items[idx]["field_name"], verified_only=verified_only)

    return [r if r is not None else items[i]["text"] for i, r in enumerate(results)]

def get_labels(lang: str):
    """Returns the labels dictionary for the target language."""
    if lang not in LABELS:
        print(f"Warning: No labels found for language '{lang}', falling back to English.")
    return LABELS.get(lang, LABELS["en"])

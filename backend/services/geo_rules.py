# backend/services/geo_rules.py

GEO_RULES = {
    "korea": {
        "template": "Korean_resume_template.html",
        "css": "css/base.css",
        "specialty": True,
        "show_photo": True,
        "show_dob": True,
        "show_nationality": True,
        "show_marital": False,
        "show_gpa": False,
        "show_visa": True,
        "show_religion": False,
        "date_format": "YYYY/MM",
        "edu_order": "newest_first",
        "work_order": "newest_first",
        "cover_letter": True,
        "cover_letter_type": "jagi_sogaeseo",
        "prune_fields": [],
        "max_pages": 3,
        "format": "A4",
        "margin": {"top": "15mm", "right": "15mm", "bottom": "15mm", "left": "15mm"},
    },
    "japan": {
        "template": "template_japan_rirekisho.html", 
        "css": "css/japan.css",
        "specialty": True,
        "show_photo": True,
        "show_dob": True,
        "show_nationality": True,
        "show_marital": True,
        "show_gpa": False,
        "show_visa": True,
        "show_religion": False,
        "date_format": "japanese_era",
        "edu_order": "oldest_first",
        "work_order": "oldest_first",
        "cover_letter": True,
        "cover_letter_type": "jiko_pr",
        "prune_fields": [],
        "max_pages": 4,
        "format": "A4",
        "margin": {"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
    },
    "usa": {
        "template": "template_ats.html",
        "css": "css/ats.css",
        "specialty": False,
        "show_photo": False,
        "show_dob": False,
        "show_nationality": False,
        "show_marital": False,
        "show_gpa": True,
        "show_visa": True,
        "show_religion": False,
        "date_format": "MM/YYYY",
        "edu_order": "newest_first",
        "work_order": "newest_first",
        "cover_letter": True,
        "cover_letter_type": "ats_letter",
        "prune_fields": ["photo", "dob", "nationality", "marital_status"],
        "max_pages": 2,
        "format": "Letter",
        "margin": {"top": "20mm", "right": "20mm", "bottom": "20mm", "left": "20mm"},
    },
    "uk": {
        "template": "template_ats.html",
        "css": "css/ats.css",
        "specialty": False,
        "show_photo": False,
        "show_dob": False,
        "show_nationality": False,
        "show_marital": False,
        "show_gpa": False,
        "show_visa": True,
        "show_religion": False,
        "date_format": "MM/YYYY",
        "edu_order": "newest_first",
        "work_order": "newest_first",
        "cover_letter": True,
        "cover_letter_type": "ats_letter",
        "prune_fields": ["photo", "dob", "nationality", "marital_status"],
        "max_pages": 2,
        "format": "Letter",
        "margin": {"top": "20mm", "right": "20mm", "bottom": "20mm", "left": "20mm"},
    },
    "uae": {
        "template": "template_ats.html",
        "css": "css/ats.css",
        "specialty": False,
        "show_photo": True,
        "show_dob": True,
        "show_nationality": True,
        "show_marital": True,
        "show_gpa": False,
        "show_visa": True,
        "show_religion": False,
        "date_format": "MM/YYYY",
        "edu_order": "newest_first",
        "work_order": "newest_first",
        "cover_letter": True,
        "cover_letter_type": "ats_letter",
        "prune_fields": [],
        "max_pages": 3,
    },
    "china": {
        "template": "template_china.html",
        "css": "css/china.css",
        "specialty": True,
        "show_photo": True,
        "show_dob": True,
        "show_nationality": True,
        "show_marital": True,
        "show_gpa": True,
        "show_visa": True,
        "show_religion": False,
        "date_format": "YYYY年MM月",
        "edu_order": "newest_first",
        "work_order": "newest_first",
        "cover_letter": True,
        "cover_letter_type": "qiu_zhi_xin",
        "prune_fields": [],
        "max_pages": 2,
        "format": "A4",
        "margin": {"top": "15mm", "right": "15mm", "bottom": "15mm", "left": "15mm"},
    },
    "india": {
        "template": "template_ats.html",
        "css": "css/ats.css",
        "specialty": False,
        "show_photo": False,
        "show_dob": False,
        "show_nationality": False,
        "show_marital": False,
        "show_gpa": True,
        "show_visa": False,
        "show_religion": False,
        "date_format": "MM/YYYY",
        "edu_order": "newest_first",
        "work_order": "newest_first",
        "cover_letter": True,
        "cover_letter_type": "ats_letter",
        "prune_fields": ["photo", "dob", "nationality", "marital_status"],
        "max_pages": 2,
        "format": "A4",
        "margin": {"top": "20mm", "right": "20mm", "bottom": "20mm", "left": "20mm"},
    },
    "international": {
        "template": "template_ats.html",
        "css": "css/ats.css",
        "specialty": False,
        "show_photo": False,
        "show_dob": False,
        "show_nationality": False,
        "show_marital": False,
        "show_gpa": True,
        "show_visa": True,
        "show_religion": False,
        "date_format": "MM/YYYY",
        "edu_order": "newest_first",
        "work_order": "newest_first",
        "cover_letter": True,
        "cover_letter_type": "ats_letter",
        "prune_fields": ["photo", "dob", "nationality", "marital_status"],
        "max_pages": 2,
        "format": "A4",
        "margin": {"top": "20mm", "right": "20mm", "bottom": "20mm", "left": "20mm"},
    },
}

ATS_COUNTRIES = [
    "usa", "uk", "canada", "australia", "india",
    "singapore", "france", "germany",
    "uae", "saudi_arabia", "europe", "international"
]

SPECIALTY_COUNTRIES = [
    "japan", "korea", "china"
]

def get_geo_rule(region: str):
    """Returns rule for a region, falling back to international (ATS)."""
    region_key = region.lower()
    if region_key in GEO_RULES:
        return GEO_RULES[region_key]
    
    # Default to International ATS
    return GEO_RULES.get("usa") # USA rules are a good base for general ATS

def calculate_ats_score(data: dict, region: str):
    """Calculates a compliance score based on regional ATS standards."""
    rule = get_geo_rule(region)
    score = 0
    checks = []

    profile = data.get("profile", {})
    personal = profile.get("personal", {})
    
    # 1. Contact Info (Base for all)
    if profile.get("email") and profile.get("phone"):
        score += 10
        checks.append("Contact info present")

    # 2. Professional Summary
    if profile.get("summary") or profile.get("bio"):
        score += 10
        checks.append("Professional summary present")

    # 3. Skills
    skills = data.get("skills", [])
    if len(skills) >= 5:
        score += 10
        checks.append("5+ relevant skills")
    
    # 4. Experience
    exp = data.get("experience", [])
    if len(exp) >= 3:
        score += 20
        checks.append("Strong career history (3+ roles)")
    elif len(exp) > 0:
        score += 10
        checks.append("Work history present")

    # 5. Region Specific Rules
    region_key = region.lower()
    if region_key in ["usa", "uk", "germany", "international", "india"]:
        # Photo Check (ATS compliant = no photo)
        if not data.get("profile_photo_url") and not data.get("profile_photo"):
            score += 20
            checks.append("Privacy Compliance (No photo for ATS)")
        
        # DOB Check
        if not personal.get("dob"):
            score += 10
            checks.append("Privacy Compliance (No DOB for ATS)")
            
        # Visa Status Check (Standard for International, optional for others)
        if region_key == "international" and personal.get("visa_status"):
            score += 10
            checks.append("Visa Status / Work Authorization included")
            
        # Education
        if len(data.get("education", [])) > 0:
            score += 20
            checks.append("Academic background present")

    elif region_key == "japan":
        # Photo is REQUIRED in Japan
        if data.get("profile_photo_url") or data.get("profile_photo"):
            score += 20
            checks.append("Photo attached (Required for Japan)")
        
        # Marital Status
        if personal.get("marital_status"):
            score += 10
            checks.append("Marital status included")
            
        # Self-PR
        if personal.get("self_pr_ja") or profile.get("summary"):
            score += 20
            checks.append("Japanese Self-PR/Summary present")
            
        # Education
        if len(data.get("education", [])) >= 2:
            score += 20
            checks.append("Complete educational history")

    elif region_key == "korea":
        # Photo is standard
        if data.get("profile_photo_url") or data.get("profile_photo"):
            score += 20
            checks.append("Photo attached")
            
        # Jagi-sogaeseo (4 parts)
        cl = data.get("cover_letter", {})
        parts = ["growth_background", "strengths_weaknesses", "motivation", "goals_after_joining"]
        present_parts = [p for p in parts if cl.get(p)]
        if len(present_parts) >= 2:
            score += 30
            checks.append(f"Korean Self-Introduction ({len(present_parts)}/4 sections)")
        
        if len(data.get("education", [])) > 0:
            score += 10
        
    # Final Cap at 100
    return {
        "score": min(score, 100),
        "checks": checks
    }

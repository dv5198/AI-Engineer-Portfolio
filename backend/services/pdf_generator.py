# backend/services/pdf_generator.py

import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, ListFlowable, ListItem

def clean_text(text: str) -> str:
    """Removes or replaces non-printable/mangled characters for ReportLab PDF."""
    if not text: return ""
    replacements = {
        "\u00e2\u20ac\u201c": "-", # En-dash
        "\u00e2\u20ac\u2122": "'", # Smart quote
        "\u2013": "-",
        "\u2014": "-",
        "\u2019": "'",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def get_age(dob_str: str) -> int:
    """Calculates age from DOB string (expected format: DD-MM-YYYY or MM-DD-YYYY)."""
    try:
        # Try DD-MM-YYYY first
        dob = datetime.strptime(dob_str, "%d-%m-%Y")
    except ValueError:
        try:
            # Fallback to MM-DD-YYYY
            dob = datetime.strptime(dob_str, "%m-%d-%Y")
        except ValueError:
            return 0
    
    today = datetime.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def build_header_no_photo(story, profile, S):
    """
    Single column header — clean, ATS safe.
    Used for: international only.
    Strictly excludes DOB, gender, nationality, photo.
    """
    # Name
    story.append(Paragraph(profile.get('name', 'Divya Nirankari'), S['Name']))
    # Role
    story.append(Paragraph(profile.get('role', 'Software Engineer'), S['SubTitle']))
    
    # Contact Info Line
    contact_parts = [
        profile.get('location', ''),
        profile.get('email', ''),
        profile.get('phone', ''),
        f"<a href='{profile.get('linkedin', '')}' color='blue'>LinkedIn</a>",
        f"<a href='{profile.get('github', '')}' color='blue'>GitHub</a>"
    ]
    contact_line = " • ".join([p for p in contact_parts if p])
    story.append(Paragraph(contact_line, S['ContactInfo']))
    
    # Timezone line for remote clarity (International only)
    if profile.get('timezone'):
        story.append(Paragraph(f"Timezone: {profile['timezone']}", S['SmallCenter']))
    
    story.append(Spacer(1, 0.5 * cm))

def build_header_with_photo(story, profile, photo_path, S, region):
    """
    Two-column header — contact info left, photo right.
    Used for: korea, japan, china, germany, middleeast.
    """
    # Personal Info to show based on region
    personal_info = []
    
    # General Photo Region Rules
    if region == 'japan':
        age = get_age(profile.get('dateOfBirth', ''))
        if age: personal_info.append(f"Age: {age}")
    else:
        if profile.get('dateOfBirth'): personal_info.append(f"DOB: {profile['dateOfBirth']}")
    
    if profile.get('gender'): personal_info.append(f"Gender: {profile['gender']}")
    if profile.get('nationality'): personal_info.append(f"Nationality: {profile['nationality']}")
    
    if region in ['china', 'middleeast']:
        if profile.get('maritalStatus'): personal_info.append(f"Marital Status: {profile['maritalStatus']}")
    
    if region == 'middleeast':
        if profile.get('visaStatus'): personal_info.append(f"Visa: {profile['visaStatus']}")

    # Create Left Column Content (Info)
    info_elements = [
        Paragraph(profile.get('name', 'Divya Nirankari'), S['NameLeft']),
        Paragraph(profile.get('role', 'Software Engineer'), S['SubTitleLeft']),
        Spacer(1, 0.2 * cm),
        Paragraph(f"Email: {profile.get('email', '')}", S['SmallLeft']),
        Paragraph(f"Phone: {profile.get('phone', '')}", S['SmallLeft']),
        Paragraph(f"Location: {profile.get('location', '')}", S['SmallLeft']),
        Spacer(1, 0.2 * cm),
        Paragraph(" | ".join(personal_info), S['SmallLeft']) if personal_info else Spacer(1, 0.1),
        Spacer(1, 0.2 * cm),
        Paragraph(f"<a href='{profile.get('linkedin', '')}' color='blue'>LinkedIn</a>  |  <a href='{profile.get('github', '')}' color='blue'>GitHub</a>", S['SmallLeft'])
    ]
    
    # Create Photo Column
    photo_cell = []
    if photo_path and os.path.exists(photo_path):
        # Scale photo based on region rules if necessary, here using a standard size
        img = Image(photo_path, width=3.0*cm, height=4.0*cm)
        photo_cell.append(img)
    
    # Header Table
    data = [[info_elements, photo_cell]]
    table = Table(data, colWidths=[14*cm, 4*cm])
    table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

def generate_resume_by_region(data: dict, live_projects: list, region: str, include_photo: bool) -> BytesIO:
    """Generates a regional PDF resume."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    # Styles
    styles = getSampleStyleSheet()
    S = {}
    S['Name'] = ParagraphStyle('Name', parent=styles['Heading1'], fontSize=24, alignment=1, spaceAfter=2)
    S['NameLeft'] = ParagraphStyle('NameLeft', parent=styles['Heading1'], fontSize=22, alignment=0, spaceAfter=2)
    S['SubTitle'] = ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=12, alignment=1, textColor=colors.grey, spaceAfter=6)
    S['SubTitleLeft'] = ParagraphStyle('SubTitleLeft', parent=styles['Normal'], fontSize=11, alignment=0, textColor=colors.grey, spaceAfter=6)
    S['ContactInfo'] = ParagraphStyle('ContactInfo', parent=styles['Normal'], fontSize=9, alignment=1, spaceAfter=2)
    S['SmallCenter'] = ParagraphStyle('SmallCenter', parent=styles['Normal'], fontSize=8, alignment=1, textColor=colors.grey)
    S['SmallLeft'] = ParagraphStyle('SmallLeft', parent=styles['Normal'], fontSize=9, alignment=0)
    S['SectionHeading'] = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6, borderPadding=2, borderSide='bottom', borderColor=colors.black, borderWidth=0.5)
    S['Body'] = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=4, leading=12)
    S['Bullet'] = ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=10, leftIndent=12, spaceAfter=2, leading=12)
    S['BoldBody'] = ParagraphStyle('BoldBody', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')

    story = []
    profile = data.get('profile', {})
    
    # Header Logic
    photo_path = profile.get('photo') # Should be absolute or relative to backend root
    if photo_path and not os.path.isabs(photo_path):
        photo_path = os.path.join(os.getcwd(), photo_path)

    if region == 'international':
        build_header_no_photo(story, profile, S)
    else:
        # Photo handling based on availability and region rules
        actual_include_photo = include_photo and photo_path and os.path.exists(photo_path)
        if actual_include_photo:
            build_header_with_photo(story, profile, photo_path, S, region)
        else:
            build_header_no_photo(story, profile, S)

    # Professional Summary
    summary = profile.get('summary') or profile.get('bio')
    if summary:
        story.append(Paragraph("Professional Summary", S['SectionHeading']))
        story.append(Paragraph(clean_text(summary), S['Body']))

    # Experience
    if data.get('experience'):
        story.append(Paragraph("Professional Experience", S['SectionHeading']))
        for exp in data['experience']:
            if exp.get('visible') is False: continue
            title_line = f"<b>{exp.get('company', '')}</b> | {exp.get('role', '')}"
            date_line = f"{exp.get('startDate', '')} — {exp.get('endDate', '')}"
            
            exp_table = Table([[Paragraph(title_line, S['Body']), Paragraph(date_line, ParagraphStyle('Date', parent=S['Body'], alignment=2))]], colWidths=[13*cm, 5*cm])
            story.append(exp_table)
            
            for bullet in exp.get('bullets', []):
                story.append(Paragraph(f"• {clean_text(bullet)}", S['Bullet']))
            story.append(Spacer(1, 0.2 * cm))

    # Projects
    if live_projects:
        story.append(Paragraph("Technical Projects", S['SectionHeading']))
        for proj in live_projects:
            # proj is a dict with name, summary, techStack, github, etc.
            name = f"<b>{proj.get('name', '')}</b>"
            stack = f"({proj.get('techStack', '')})" if proj.get('techStack') else ""
            summary = proj.get('summary') or proj.get('description') or ""
            
            story.append(Paragraph(f"{name} {stack}", S['Body']))
            story.append(Paragraph(clean_text(summary), S['Bullet']))
            if proj.get('github'):
                story.append(Paragraph(f"<a href='{proj['github']}' color='blue'>View Source Code</a>", S['Bullet']))
            story.append(Spacer(1, 0.2 * cm))

    # Skills
    if data.get('skillCategories'):
        story.append(Paragraph("Technical Skills", S['SectionHeading']))
        for cat in data['skillCategories']:
            if cat.get('visible') is False: continue
            label = f"<b>{cat.get('label', '')}:</b> "
            items = ", ".join(cat.get('items', []))
            story.append(Paragraph(label + items, S['Body']))

    # Education (Oldest first for Japan, otherwise reverse chron)
    edu_list = data.get('education', [])
    if edu_list:
        story.append(Paragraph("Education", S['SectionHeading']))
        if region == 'japan':
            # Note: Assuming education has a way to determine order, or just reverse if stored as reverse chron
            edu_list = list(reversed(edu_list))
            
        for edu in edu_list:
            if edu.get('visible') is False: continue
            
            inst_name = edu.get('university') or edu.get('institution') or ''
            degree_name = edu.get('degree', '')
            
            title_text = ""
            if inst_name and degree_name:
                title_text = f"<b>{inst_name}</b> — {degree_name}"
            elif inst_name:
                title_text = f"<b>{inst_name}</b>"
            elif degree_name:
                title_text = f"<b>{degree_name}</b>"
                
            story.append(Paragraph(title_text, S['Body']))
            
            details = []
            yr = edu.get('year') or (f"{edu.get('startDate', '')} — {edu.get('endDate', '')}" if edu.get('startDate') else "")
            if yr and yr != " — ": details.append(yr)
            if edu.get('awarded'): details.append(f"Awarded: {edu.get('awarded')}")
            if edu.get('gpa'): details.append(f"GPA: {edu.get('gpa')}")
            
            if details:
                story.append(Paragraph(" | ".join(details), S['SmallLeft']))
            
            if edu.get('notes'):
                story.append(Paragraph(clean_text(edu.get('notes', '')), S['Bullet']))
                
            story.append(Spacer(1, 0.1 * cm))

    # Certifications
    cert_list = data.get('certifications', [])
    if cert_list:
        story.append(Paragraph("Certifications", S['SectionHeading']))
        for cert in cert_list:
            if cert.get('visible') is False: continue
            cert_name = f"<b>{cert.get('name', '')}</b>"
            issuer = cert.get('issuer', '')
            yr = cert.get('year', '')
            
            line = cert_name
            if issuer: line += f", {issuer}"
            if yr: line += f" ({yr})"
            story.append(Paragraph(line, S['Bullet']))
        story.append(Spacer(1, 0.2 * cm))

    doc.build(story)
    buffer.seek(0)
    return buffer

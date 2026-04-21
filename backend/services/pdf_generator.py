# backend/services/pdf_generator.py

import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

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
    """Calculates age from DOB string."""
    try:
        dob = datetime.strptime(dob_str, "%d-%m-%Y")
    except ValueError:
        try:
            dob = datetime.strptime(dob_str, "%m-%d-%Y")
        except ValueError:
            return 0
    today = datetime.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def build_header_no_photo(story, profile, S):
    """Clean, ATS safe header."""
    story.append(Paragraph(profile.get('name', 'Divya Nirankari'), S['Name']))
    story.append(Paragraph(profile.get('role', 'Software Engineer'), S['SubTitle']))
    
    contact_parts = [
        profile.get('location', ''),
        profile.get('email', ''),
        profile.get('phone', ''),
        f"<a href='{profile.get('linkedin', '')}' color='blue'>LinkedIn</a>",
        f"<a href='{profile.get('github', '')}' color='blue'>GitHub</a>"
    ]
    contact_line = " • ".join([p for p in contact_parts if p])
    story.append(Paragraph(contact_line, S['ContactInfo']))
    
    if profile.get('timezone'):
        story.append(Paragraph(f"Timezone: {profile['timezone']}", S['SmallCenter']))
    story.append(Spacer(1, 0.5 * cm))

def build_header_with_photo(story, profile, photo_path, S, region):
    """Visual header with photo for specific regions."""
    personal_info = []
    
    if region == 'japan':
        age = get_age(profile.get('dateOfBirth', ''))
        if age: personal_info.append(f"Age: {age}")
    elif region in ['korea', 'china', 'germany', 'middleeast']:
        if profile.get('dateOfBirth'): personal_info.append(f"DOB: {profile['dateOfBirth']}")
    
    if region == 'korea' and profile.get('gender'): 
        personal_info.append(f"Gender: {profile['gender']}")
    if region in ['korea', 'japan', 'china', 'germany', 'middleeast'] and profile.get('nationality'): 
        personal_info.append(f"Nationality: {profile['nationality']}")
    if region == 'china' and profile.get('maritalStatus'):
        personal_info.append(f"Marital Status: {profile['maritalStatus']}")
    if region == 'middleeast' and profile.get('visaStatus'):
        personal_info.append(f"Visa: {profile['visaStatus']}")

    info_elements = [
        Paragraph(profile.get('name', 'Divya Nirankari'), S['NameLeft']),
        Paragraph(profile.get('role', 'Software Engineer'), S['SubTitleLeft']),
        Spacer(1, 0.2 * cm),
        Paragraph(f"Email: {profile.get('email', '')}", S['SmallLeft']),
        Paragraph(f"Phone: {profile.get('phone', '')}", S['SmallLeft']),
        Paragraph(f"Location: {profile.get('location', '')}", S['SmallLeft']),
        Spacer(1, 0.2 * cm),
    ]
    if personal_info:
        info_elements.append(Paragraph(" | ".join(personal_info), S['SmallLeft']))
        info_elements.append(Spacer(1, 0.2 * cm))
    info_elements.append(Paragraph(f"<a href='{profile.get('linkedin', '')}' color='blue'>LinkedIn</a>  |  <a href='{profile.get('github', '')}' color='blue'>GitHub</a>", S['SmallLeft']))
    
    photo_cell = []
    if photo_path and os.path.exists(photo_path):
        if region in ['korea', 'germany', 'middleeast']:
            photo_w, photo_h = 3.5*cm, 4.5*cm
        elif region == 'japan':
            photo_w, photo_h = 3.0*cm, 4.0*cm
        elif region == 'china':
            photo_w, photo_h = 2.5*cm, 3.5*cm
        else:
            photo_w, photo_h = 3.0*cm, 4.0*cm
        img = Image(photo_path, width=photo_w, height=photo_h)
        photo_cell.append(img)
    
    data = [[info_elements, photo_cell]]
    table = Table(data, colWidths=[14*cm, 4*cm])
    table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

def generate_ats_resume(data: dict, live_projects: list, region: str) -> BytesIO:
    """Strict ATS implementation (Single column, no photos/colors)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    S = {
        'Name': ParagraphStyle('Name', parent=styles['Heading1'], fontSize=24, alignment=1, spaceAfter=2),
        'SubTitle': ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=12, alignment=1, textColor=colors.grey, spaceAfter=6),
        'ContactInfo': ParagraphStyle('ContactInfo', parent=styles['Normal'], fontSize=9, alignment=1, spaceAfter=2),
        'SmallCenter': ParagraphStyle('SmallCenter', parent=styles['Normal'], fontSize=8, alignment=1, textColor=colors.grey),
        'SectionHeading': ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=14, spaceBefore=10, spaceAfter=6, borderPadding=2, borderSide='bottom', borderColor=colors.black, borderWidth=0.5),
        'Body': ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=4, leading=12),
        'Bullet': ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=10, leftIndent=12, spaceAfter=2, leading=12),
        'SmallLeft': ParagraphStyle('SmallLeft', parent=styles['Normal'], fontSize=9, alignment=0)
    }

    story = []
    profile = data.get('profile', {})
    
    build_header_no_photo(story, profile, S)
    
    populate_common_ats_sections(story, data, live_projects, region, S)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_photo_resume(data: dict, live_projects: list, region: str, photo_path: str) -> BytesIO:
    """Visual template implementation for Photo-required regions."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    # Different visual style: Colored headings, different structural margins
    primary_color = colors.HexColor('#2c3e50')
    secondary_color = colors.HexColor('#7f8c8d')
    
    S = {
        'NameLeft': ParagraphStyle('NameLeft', parent=styles['Heading1'], fontSize=22, alignment=0, spaceAfter=2, textColor=primary_color),
        'SubTitleLeft': ParagraphStyle('SubTitleLeft', parent=styles['Normal'], fontSize=11, alignment=0, textColor=secondary_color, spaceAfter=6),
        'SmallLeft': ParagraphStyle('SmallLeft', parent=styles['Normal'], fontSize=9, alignment=0),
        'SectionHeading': ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=14, spaceBefore=12, spaceAfter=8, textColor=primary_color, borderPadding=4, borderSide='bottom', borderColor=primary_color, borderWidth=1),
        'Body': ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=4, leading=14),
        'Bullet': ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=10, leftIndent=12, spaceAfter=4, leading=14, bulletColor=primary_color),
        'SmallLeft': ParagraphStyle('SmallLeft', parent=styles['Normal'], fontSize=9, alignment=0)
    }

    story = []
    profile = data.get('profile', {})
    
    build_header_with_photo(story, profile, photo_path, S, region)
    
    populate_common_ats_sections(story, data, live_projects, region, S)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def populate_common_ats_sections(story, data, live_projects, region, S):
    """Shared body section generator. Can be further diverged if needed."""
    profile = data.get('profile', {})
    
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
            is_gh = proj.get('is_github', False)
            name_text = proj.get('name', 'Project')
            if is_gh:
                stars = proj.get('stars', 0)
                star_text = f" | \u2605 {stars}" if stars > 0 else ""
                name_line = f"<b>{name_text}</b> <font color='grey' size='9'>(GitHub{star_text})</font>"
            else:
                name_line = f"<b>{name_text}</b>"
            
            stack = f" — {proj.get('techStack', '')}" if proj.get('techStack') else ""
            summary = proj.get('summary') or proj.get('description') or ""
            
            story.append(Paragraph(f"{name_line}{stack}", S['Body']))
            story.append(Paragraph(clean_text(summary), S['Bullet']))
            
            project_url = proj.get('url') or proj.get('github')
            if project_url:
                story.append(Paragraph(f"<a href='{project_url}' color='blue'>View Implementation</a>", S['Bullet']))
            story.append(Spacer(1, 0.2 * cm))

    # Skills
    if data.get('skillCategories'):
        story.append(Paragraph("Technical Skills", S['SectionHeading']))
        for cat in data['skillCategories']:
            if cat.get('visible') is False: continue
            label = f"<b>{cat.get('label', '')}:</b> "
            items = ", ".join(cat.get('items', []))
            story.append(Paragraph(label + items, S['Body']))

    # Education
    edu_list = data.get('education', [])
    if edu_list:
        story.append(Paragraph("Education", S['SectionHeading']))
        if region == 'japan':
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

def generate_resume_by_region(data: dict, live_projects: list, region: str, include_photo: bool) -> BytesIO:
    """Master router orchestrating regional template deployment."""
    profile = data.get('profile', {})
    photo_path = profile.get('photo')
    if photo_path and not os.path.isabs(photo_path):
        photo_path = os.path.join(os.getcwd(), photo_path)

    # Completely distinct logic branches!
    if include_photo and photo_path and os.path.exists(photo_path) and region != 'international':
        return generate_photo_resume(data, live_projects, region, photo_path)
    else:
        return generate_ats_resume(data, live_projects, region)

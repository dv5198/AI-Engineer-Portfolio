import os
import io
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from database import load_data

def generate_resume_pdf():
    # Load data
    data = load_data()
    
    # Setup Jinja2 environment
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('resume_template.html')
    
    # Render HTML
    html_out = template.render(
        profile=data.get('profile', {}),
        about=data.get('about', []),
        skills=data.get('skills', []),
        experience=data.get('experience', []),
        education=data.get('education', []),
        achievements=data.get('achievements', []),
        stats=data.get('stats', {})
    )
    
    # Generate PDF bytes
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html_out.encode("utf-8")), dest=result)
    
    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed: {pisa_status.err}")
        
    return result.getvalue()

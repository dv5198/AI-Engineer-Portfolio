from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from services.pdf_generator import generate_resume_pdf
import io

router = APIRouter()

@router.get("/download")
async def download_resume():
    try:
        pdf_bytes = generate_resume_pdf()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=Divya_Nirankari_CV.pdf"
            }
        )
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")

@router.get("/")
def get_resume():
    # Redirect or inform that resume is now auto-generated
    return {"message": "Resume is auto-generated. Use /api/resume/download to get the PDF."}

# Task 2: Remove resume upload endpoint and static storage
# (logic removed from here)

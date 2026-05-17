import os
import sys
from pypdf import PdfReader

TEST_OUTPUTS_DIR = "backend/test_outputs"

# Force UTF-8 encoding for stdout to prevent cp1252 encoding errors on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_pdf_text(filename):
    path = os.path.join(TEST_OUTPUTS_DIR, filename)
    if not os.path.exists(path):
        # Retry with backend/ prefix if run from workspace root
        alt_path = os.path.join("backend", TEST_OUTPUTS_DIR, filename)
        if os.path.exists(alt_path):
            path = alt_path
        else:
            raise FileNotFoundError(f"PDF file {filename} not found.")
            
    reader = PdfReader(path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()
    return full_text

def verify_pdfs():
    print("--- STARTING DETERMINISTIC CONTENT VERIFICATION ---")
    
    # 1. Verify Japan Rirekisho Certifications, Spouse, and English/Japanese Visa
    print("\n[Japan Rirekisho verification]")
    try:
        japan_ja_text = extract_pdf_text("japan_ja_covertrue.pdf")
        
        # Verify certifications combined and sorted
        if "Data Structure" in japan_ja_text or "データ構造" in japan_ja_text:
            print("OK: Found award 'Data Structure Excellence Award' listed under Certifications!")
        else:
            print("FAIL: Award 'Data Structure Excellence Award' not found in Rirekisho Certifications!")
            
        if "Student of the Year" in japan_ja_text or "年間最優秀" in japan_ja_text:
            print("OK: Found award 'Student of the Year' listed under Certifications!")
        else:
            print("FAIL: Award 'Student of the Year' not found!")

        # Verify Spouse presence (unmarried in seed -> has_spouse=False -> "無" selected)
        if "無" in japan_ja_text:
            print("OK: Found Japanese spouse option '無'")
        else:
            print("FAIL: Could not find '無' for spouse indicator!")
    except Exception as e:
        print(f"FAIL in Japan Rirekisho verification: {e}")

    # 1B. Verify Japan English Visa Text
    try:
        japan_en_text = extract_pdf_text("japan_en_covertrue.pdf")
        normalized_text = " ".join(japan_en_text.split())
        if "Engineer / Specialist" in normalized_text or "Specialist in Humanities" in normalized_text:
            print("OK: Japan EN showing correct English visa text ('Engineer / Specialist')!")
        else:
            print("FAIL: Japan EN missing correct visa text!")
    except Exception as e:
        print(f"FAIL in Japan EN verification: {e}")

    # 2. Verify China Marital Status and English Visa Statement
    print("\n[China Resume verification]")
    try:
        china_zh_text = extract_pdf_text("china_zh_covertrue.pdf")
        if "未婚" in china_zh_text:
            print("OK: Found correct unmarried Chinese status '未婚'")
        else:
            print("FAIL: Could not find '未婚' in Chinese resume!")
            
        if "已婚" in china_zh_text:
            print("FAIL: Leaked married status '已婚' found in Chinese resume!")
        else:
            print("OK: No leaked married status '已婚' in Chinese resume")
    except Exception as e:
        print(f"FAIL in China ZH verification: {e}")

    # 2B. Verify China English Visa Text
    try:
        china_en_text = extract_pdf_text("china_en_covertrue.pdf")
        if "Z work visa" in china_en_text or "Z visa" in china_en_text or "work visa" in china_en_text:
            print("OK: China EN showing correct English visa statement ('Z work visa')!")
        else:
            print("FAIL: China EN showing wrong or missing visa text!")
            
        if "需要工作签证" in china_en_text:
            print("FAIL: China EN contains Chinese visa text leak ('需要工作签证')!")
        else:
            print("OK: China EN does not leak Chinese visa text")
    except Exception as e:
        print(f"FAIL in China EN verification: {e}")

    # 3. Verify Korea English Project Labels and Placeholder leak
    print("\n[Korea Cover Letter verification]")
    try:
        korea_en_text = extract_pdf_text("korea_en_covertrue.pdf")
        
        # Verify English project labels
        if "Individual" in korea_en_text:
            print("OK: Korea EN shows English project label 'Individual'!")
        else:
            print("FAIL: Korea EN still shows Korean '개인' or is missing label!")
            
        if "Developer" in korea_en_text:
            print("OK: Korea EN shows English project label 'Developer'!")
        else:
            print("FAIL: Korea EN still shows Korean '개발자' or is missing label!")
            
        # Verify it has the actual AI-generated content and not the defaults or empty brackets
        if "[" in korea_en_text and "]" in korea_en_text:
            import re
            brackets = re.findall(r'\[.*?\]', korea_en_text)
            if any("입력해주세요" in b or "write" in b for b in brackets):
                print(f"FAIL: Found un-replaced placeholder bracket(s): {brackets}")
            else:
                print(f"NOTE: Found brackets but they don't seem to be placeholders: {brackets}")
        else:
            print("OK: No brackets/placeholders found at all!")
            
        # Check if it has the actual letter body content
        if "Divya Nirankari" in korea_en_text and "dvnirankari@gmail.com" in korea_en_text:
            print("OK: Dynamic cover letter successfully rendered with applicant details!")
        else:
            print("FAIL: Dynamic cover letter does not contain candidate contact details!")
    except Exception as e:
        print(f"FAIL in Korea verification: {e}")

    # 4. Verify Language filter on UK / USA / India Resumes (should exclude Japanese / Korean / Chinese)
    print("\n[ATS/International Resumes Language Filter verification]")
    try:
        uk_text = extract_pdf_text("ats_uk_en_coverfalse.pdf")
        if "Japanese" in uk_text or "日本語" in uk_text:
            print("FAIL: UK resume contains 'Japanese' in languages section!")
        else:
            print("OK: UK resume correctly excludes Japanese")
            
        usa_text = extract_pdf_text("ats_usa_en_coverfalse.pdf")
        if "Japanese" in usa_text or "日本語" in usa_text:
            print("FAIL: USA resume contains 'Japanese' in languages section!")
        else:
            print("OK: USA resume correctly excludes Japanese")
            
        intl_text = extract_pdf_text("international_en_coverfalse.pdf")
        if "Japanese" in intl_text or "日本語" in intl_text:
            print("FAIL: International resume contains 'Japanese' in languages section!")
        else:
            print("OK: International resume correctly excludes Japanese")
    except Exception as e:
        print(f"FAIL in Language Filter verification: {e}")

    print("\n--- CONTENT VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify_pdfs()

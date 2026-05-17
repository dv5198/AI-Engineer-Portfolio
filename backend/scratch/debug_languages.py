import os
import sys
from pypdf import PdfReader

TEST_OUTPUTS_DIR = "backend/test_outputs"

# Force UTF-8 stdout
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_pdf_languages(filename):
    path = os.path.join(TEST_OUTPUTS_DIR, filename)
    if not os.path.exists(path):
        path = os.path.join("backend", TEST_OUTPUTS_DIR, filename)
    
    print(f"\n==================== LANGUAGES IN {filename} ====================")
    reader = PdfReader(path)
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        print(f"--- PAGE {i+1} ---")
        lines = text.split('\n')
        # Find lines near "Languages"
        for idx, line in enumerate(lines):
            if "Languages" in line or "languages" in line.lower() or "Language" in line:
                print("CONTEXT:")
                start = max(0, idx - 2)
                end = min(len(lines), idx + 8)
                for c_line in lines[start:end]:
                    print("  >", c_line)
        print("-" * 40)

if __name__ == "__main__":
    debug_pdf_languages("ats_uk_en_coverfalse.pdf")

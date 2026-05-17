import os
import sys
from pypdf import PdfReader

# Force UTF-8 encoding for stdout on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TEST_OUTPUTS_DIR = "backend/test_outputs"

def debug_pdf(filename):
    path = os.path.join(TEST_OUTPUTS_DIR, filename)
    if not os.path.exists(path):
        print(f"File {filename} not found.")
        return
        
    print(f"\n==================== DEBUGGING {filename} ====================")
    reader = PdfReader(path)
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        print(f"--- PAGE {i+1} ---")
        print(text[:2000]) # Print first 2000 characters
        print("-" * 40)

if __name__ == "__main__":
    debug_pdf("korea_ko_covertrue.pdf")
    debug_pdf("korea_en_covertrue.pdf")

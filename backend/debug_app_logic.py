import asyncio
import json
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from services.pdf_playwright import generate_resume_playwright

async def main():
    # Load data
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Mock some data if needed, but data.json should be full
    # Call the actual generation function
    html = await generate_resume_playwright(data, live_projects=[], include_photo=True, region='korea', return_html=True)
    
    # Save to file
    with open('debug_korea_real.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("HTML saved to debug_korea_real.html")

if __name__ == "__main__":
    asyncio.run(main())

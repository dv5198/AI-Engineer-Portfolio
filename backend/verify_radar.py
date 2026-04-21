import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_hiring_radar():
    print(f"[INFO] Starting Hiring Radar Verification...")
    
    # 1. Check if NTFY_TOPIC is set
    topic = os.getenv("NTFY_TOPIC")
    if not topic:
        print("[ERROR] NTFY_TOPIC not found in .env")
        return
    print(f"Secret Topic: {topic}")
    print(f"Subscribe here: https://ntfy.sh/{topic}")
    
    # 2. Simulate Download Request (Localhost)
    url = "http://localhost:8001/api/resume/download"
    print(f"[INFO] Simulating download from: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            # We don't actually need to save the PDF, just trigger the request
            response = await client.get(url)
            print(f"Status Code: {response.status_code}")
            
            # 3. Wait a moment for background tasks to finish
            print("Waiting for background tasks (Logging & Push)...")
            await asyncio.sleep(4)
            
            # 4. Check data.json for analytics
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(backend_dir, "data.json")
            
            with open(data_file, "r") as f:
                data = json.load(f)
                analytics = data.get("analytics", [])
                
            if analytics:
                latest = analytics[0]
                print("Latest Analytics Entry Found:")
                print(json.dumps(latest, indent=2))
                if latest.get("event") == "resume_download":
                    print("SUCCESS: Database Logging: PASSED")
                else:
                    print("FAILED: Database Logging: FAILED (Wrong key/type)")
            else:
                print("FAILED: Database Logging: FAILED (No entries found)")
                
        except Exception as e:
            print(f"Verification Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_hiring_radar())

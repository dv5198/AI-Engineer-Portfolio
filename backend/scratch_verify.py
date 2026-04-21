import asyncio
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ntfy import send_hiring_alert
from database import log_resume_download

async def test():
    try:
        print("Testing Analytics Log...")
        log_resume_download("127.0.0.1", "India", "international", "Standard")
        print(" [OK] Logged to data.json")
        
        print("Testing NTFY Push...")
        # This will send a real notification if NTFY_TOPIC is set
        await send_hiring_alert("India", "IN", "International")
        print(" [OK] NTFY Alert Sent")
        
        print("\n[SUCCESS] Hiring Radar systems are operational.")
    except Exception as e:
        print(f"\n[FAILED] Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())

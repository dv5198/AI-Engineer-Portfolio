import httpx
import os
from dotenv import load_dotenv

load_dotenv()

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "antigravity_radar_default")

async def send_ntfy_notification(title: str, message: str, priority: int = 3, tags: list = None):
    """
    Sends a push notification via ntfy.sh.
    Priority: 1 (min) to 5 (max). Default 3.
    """
    import base64
    def rfc2047(text):
        return "=?" + "utf-8" + "?B?" + base64.b64encode(text.encode('utf-8')).decode('ascii') + "?="

    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    
    headers = {
        "Title": rfc2047(title),
        "Priority": str(priority),
    }
    
    if tags:
        headers["Tags"] = ",".join(tags)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, content=message, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending ntfy notification: {e}")
            return False

async def send_hiring_alert(location: str, country: str, region: str):
    """
    Specific helper for resume download alerts.
    """
    title = "🎯 Resume Downloaded!"
    message = f"Someone in {location}, {country} just downloaded your {region} resume."
    tags = ["tada", "briefcase", "earth_asia"]
    
    return await send_ntfy_notification(title, message, priority=4, tags=tags)

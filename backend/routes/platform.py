from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import load_data, save_data
from services.email_service import notify_contact_form
from datetime import datetime, timedelta
import hashlib
import os
import hmac

router = APIRouter()

# --- Models ---
class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class AnalyticsEvent(BaseModel):
    event: str
    data: Optional[dict] = {}

# --- Contact Form ---
@router.post("/contact/send/")
async def send_contact(req: ContactFormRequest, background_tasks: BackgroundTasks, request: Request):
    data = load_data()
    client_ip = request.client.host
    
    # Rate Limiting (Simulated simple check against data.json)
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    recent_msgs = [m for m in data.get("contactMessages", []) 
                   if m.get("ip") == hashlib.sha256(client_ip.encode()).hexdigest() 
                   and datetime.fromisoformat(m["timestamp"]) > one_hour_ago]
    
    if len(recent_msgs) >= 3:
        raise HTTPException(status_code=429, detail="Too many messages. Please try again later.")

    # Save to data.json
    msg_entry = {
        "id": f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "name": req.name,
        "email": req.email,
        "subject": req.subject,
        "message": req.message,
        "timestamp": now.isoformat(),
        "ip": hashlib.sha256(client_ip.encode()).hexdigest(),
        "read": False
    }
    data["contactMessages"].append(msg_entry)
    save_data(data)

    # Send Email in background
    background_tasks.add_task(notify_contact_form, req.name, req.email, req.subject, req.message)
    
    return {"message": "Success"}

@router.get("/messages")
async def get_messages():
    data = load_data()
    return sorted(data.get("contactMessages", []), key=lambda x: x["timestamp"], reverse=True)

@router.post("/messages/{msg_id}/toggle-read")
async def toggle_read_message(msg_id: str):
    data = load_data()
    messages = data.get("contactMessages", [])
    found_msg = None
    for msg in messages:
        if msg.get("id") == msg_id:
            msg["read"] = not msg.get("read", False)
            found_msg = msg
            break
    
    if not found_msg:
        raise HTTPException(status_code=404, detail=f"Message {msg_id} not found")
        
    save_data(data)
    return {"status": "success", "read": found_msg["read"]}

@router.delete("/messages/{msg_id}")
async def delete_message(msg_id: str):
    data = load_data()
    messages = data.get("contactMessages", [])
    data["contactMessages"] = [m for m in messages if m.get("id") != msg_id]
    save_data(data)
    return {"status": "success"}



# --- Analytics ---
@router.post("/event/")
async def log_analytics(req: AnalyticsEvent, request: Request):
    data = load_data()
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    
    event_entry = {
        "event": req.event,
        "timestamp": datetime.now().isoformat(),
        "ip": hashlib.sha256(client_ip.encode()).hexdigest(),
        "userAgent": user_agent,
        "data": req.data
    }
    data["analytics"].append(event_entry)
    # Optional: Keep only last 500 events to prevent massive data.json
    data["analytics"] = data["analytics"][-500:]
    save_data(data)
    return {"status": "logged"}

@router.get("/activity/")
async def get_activity():
    data = load_data()
    return sorted(data.get("analytics", []), key=lambda x: x["timestamp"], reverse=True)

@router.get("/summary/")
async def get_analytics_summary():
    data = load_data()
    events = data.get("analytics", [])
    
    total_views = len([e for e in events if e["event"] == "page_view"])
    total_messages = len(data.get("contactMessages", []))
    unique_ips = len(set([e["ip"] for e in events]))
    resume_downloads = len([e for e in events if e["event"] == "resume_download"])
    
    # traffic over time (last 7 days)
    traffic = {}
    for i in range(7):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        traffic[date_str] = 0
    
    for e in events:
        if e["event"] == "page_view":
            date_str = e["timestamp"][:10]
            if date_str in traffic:
                traffic[date_str] += 1
                
    traffic_over_time = [{"date": d, "visits": v} for d, v in sorted(traffic.items())]

    return {
        "total_visits": total_views,
        "unique_visitors": unique_ips,
        "resume_downloads": resume_downloads,
        "messages_total": total_messages,
        "traffic_over_time": traffic_over_time
    }

# --- Webhook ---
@router.post("/webhook/github")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not GITHUB_WEBHOOK_SECRET:
        return {"status": "Webhook secret not configured, skipping verification"}

    body = await request.body()
    signature = "sha256=" + hmac.new(GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(signature, x_hub_signature_256 or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Clear project cache (logic to be implemented in Project service if needed)
    print("GitHub Push detected. Invalidating cache...")
    return {"status": "verified"}
# --- GitHub Contributions ---
@router.get("/github/contributions/")
async def get_github_contributions(username: str):
    from services.github_graphql import fetch_github_contributions
    contributions = await fetch_github_contributions(username)
    if not contributions:
        raise HTTPException(status_code=503, detail="GitHub API Error")
    return contributions

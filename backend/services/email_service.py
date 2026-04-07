import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
CONTACT_RECEIVER = os.getenv("CONTACT_RECEIVER", "dvnirankari@gmail.com")

async def send_email_notification(subject: str, body: str):
    if not all([SMTP_USER, SMTP_PASS]):
        print("SMTP credentials not configured. Skipping email.")
        return False

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = CONTACT_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Using loop.run_in_executor for standard smtplib to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_sync_email, msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def _send_sync_email(msg):
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

async def notify_contact_form(name: str, email: str, subject: str, message: str):
    full_subject = f"Portfolio Contact: {subject}"
    body = f"From: {name} ({email})\nSubject: {subject}\n\nMessage:\n{message}"
    return await send_email_notification(full_subject, body)

import asyncio
import os
import sys
import json
import httpx
from dotenv import load_dotenv

# Force UTF-8 stdout
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv("d:/project/backend/.env")

async def test_groq_fallback():
    api_key = os.getenv("GROQ_API_KEY")
    print("GROQ_API_KEY:", api_key)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "user", "content": "Hello! Reply with OK if you receive this."}
                    ],
                    "temperature": 0.6,
                    "max_tokens": 10
                },
                timeout=10.0
            )
            print("STATUS CODE FOR 8B:", response.status_code)
            print("RESPONSE TEXT FOR 8B:", response.text)
        except Exception as e:
            print("EXCEPTION:", e)

if __name__ == "__main__":
    asyncio.run(test_groq_fallback())

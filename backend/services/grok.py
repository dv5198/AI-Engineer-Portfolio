import os
import json
from typing import List, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# We use GROQ_API_KEY and the openai client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
# Good standard model on Groq
GROQ_MODEL = "llama-3.3-70b-versatile"

client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL
)

async def call_grok_json(system_prompt: str, user_prompt: str) -> dict:
    """
    Helper to call Groq API with JSON response format.
    Uses OpenAI-compatible endpoint.
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not configured"}

    try:
        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Groq API Error: {e}")
        return {"error": str(e)}

async def rewrite_text(text: str, instruction: str) -> str:
    """Generic text rewriter for About/Bio edits in admin panel."""
    system = "You are a professional editor. Return ONLY a JSON object: {\"rewritten\": \"<your rewritten text here>\"}"
    user = f"Rewrite the following text according to this instruction: '{instruction}'. Text: {text}"
    res = await call_grok_json(system, user)
    return res.get("rewritten", text)

async def execute_admin_command(command: str, current_data: dict) -> dict:
    """Interprets natural language commands to update the portfolio state."""
    system = "You are a JSON state manager. Return ONLY a raw JSON object representing path updates. No markdown."
    user = f"""
    Current state keys: {list(current_data.keys())}
    Command: "{command}"
    Return ONLY a raw JSON object representing the exact updates to apply to the state.
    """
    return await call_grok_json(system, user)

async def call_grok(prompt: str) -> str:
    """
    Generic helper to call Groq API for plain text responses.
    """
    if not GROQ_API_KEY:
        return "GROQ API Key not configured."

    try:
        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API Plain Text Error: {e}")
        return f"Error: {str(e)}"

async def summarize_about(about_list: list) -> str:
    """
    Summarizes a list of 'About' strings into a 4-7 line ATS professional summary.
    """
    if not about_list:
        return ""
        
    about_text = "\n".join(about_list)
    prompt = f"""
    Rewrite and condense the following 'About Me' section into a cohesive, professional summary for a resume.
    
    Rules:
    1. Length: Between 4 and 7 lines of dense, impactful text.
    2. Tone: Professional, third-person (refer to the candidate by name or title, no "I" or "my").
    3. Goal: Highlight core technical expertise and value proposition.
    4. Focus: Backend Engineering, Python, AI/ML, and Scalable Systems.
    
    Content to summarize:
    {about_text}
    """
    
    try:
        response = await call_grok(prompt)
        # Groq might wrap in markdown, though we asked it not to. Let's do a basic strip just in case.
        return response.strip().replace('```', '')
    except Exception as e:
        print(f"Error summarizing about section: {e}")
        return about_text[0] if about_list else ""


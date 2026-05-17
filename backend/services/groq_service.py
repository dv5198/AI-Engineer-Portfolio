import os
import json
from typing import List, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# We use GROQ_API_KEY and the openai client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
# Good standard model on Groq - Use 8B for most tasks to avoid TPM limits
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_MODEL_70B = "llama-3.3-70b-versatile"

client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL
)

class GroqError(Exception):
    def __init__(self, message, solution, error_type="unknown"):
        self.message = message
        self.solution = solution
        self.error_type = error_type
        super().__init__(self.message)

async def call_groq_json(system_prompt: str, user_prompt: str) -> dict:
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
        err_info = handle_groq_error(e)
        raise GroqError(err_info["error"], err_info["solution"], err_info["type"])

def handle_groq_error(e: Exception) -> dict:
    """Translates technical Groq/OpenAI errors into user-friendly solutions."""
    err_str = str(e)
    
    if "429" in err_str:
        return {
            "error": "Rate Limit Reached (429)",
            "solution": "The AI is currently busy. Please wait 30-60 seconds and try again. This limit resets every minute.",
            "type": "rate_limit"
        }
    
    if "authentication" in err_str.lower() or "api_key" in err_str.lower() or "401" in err_str:
        return {
            "error": "Authentication Failed",
            "solution": "The Groq API Key is missing or invalid. Please verify the GROQ_API_KEY in your .env file.",
            "type": "auth"
        }
        
    if "timeout" in err_str.lower() or "deadline" in err_str.lower():
        return {
            "error": "Request Timeout",
            "solution": "The connection to the AI service timed out. Please check your internet or try again in a moment.",
            "type": "timeout"
        }
        
    if "insufficient_quota" in err_str.lower():
        return {
            "error": "Quota Exceeded",
            "solution": "Your Groq account has run out of credits or reached its monthly limit. Please check your Groq dashboard.",
            "type": "quota"
        }

    return {
        "error": "AI Service Error",
        "solution": f"An unexpected error occurred: {err_str}. Please try again in a few minutes.",
        "type": "unknown"
    }

async def rewrite_text(text: str, instruction: str) -> str:
    """Generic text rewriter for About/Bio edits in admin panel."""
    system = "You are a professional editor. Return ONLY a JSON object: {\"rewritten\": \"<your rewritten text here>\"}"
    user = f"Rewrite the following text according to this instruction: '{instruction}'. Text: {text}"
    res = await call_groq_json(system, user)
    return res.get("rewritten", text)

async def execute_admin_command(command: str, current_data: dict) -> dict:
    """Interprets natural language commands to update the portfolio state."""
    system = "You are a JSON state manager. Return ONLY a raw JSON object representing path updates. No markdown."
    user = f"""
    Current state keys: {list(current_data.keys())}
    Command: "{command}"
    Return ONLY a raw JSON object representing the exact updates to apply to the state.
    """
    return await call_groq_json(system, user)

# ── Regional Cover Letter Prompt Map (G6) ────────────────────────────────────
COVER_LETTER_PROMPTS = {
    "JP": {
        "ecosystem": "Japan's healthcare AI and medical robotics sector",
        "tone": "formal and respectful, Japanese business culture aware",
        "visa": "willing to relocate to Japan and apply for the Engineer/Specialist visa (技術・人文知識・国際業務)",
        "language_note": "currently studying Japanese and committed to cultural integration"
    },
    "JP_EN": {
        "ecosystem": "Japan's healthcare AI and medical robotics sector",
        "tone": "formal and respectful, Japanese business culture aware",
        "visa": "willing to relocate to Japan and apply for the Engineer/Specialist visa (Engineer/Specialist in Humanities/International Services)",
        "language_note": "currently studying Japanese and committed to cultural integration"
    },
    "KR": {
        "ecosystem": "Korea's world-class AI research institutions and semiconductor-driven tech sector",
        "tone": "professional and achievement-oriented, Korean business culture aware",
        "visa": "willing to relocate to Korea and apply for E-7 Specially Designated Activities visa",
        "language_note": "currently studying Korean"
    },
    "KR_EN": {
        "ecosystem": "Korea's world-class AI research institutions and semiconductor-driven tech sector",
        "tone": "professional and achievement-oriented, Korean business culture aware",
        "visa": "willing to relocate to Korea and apply for E-7 Specially Designated Activities visa",
        "language_note": "currently studying Korean"
    },
    "CN": {
        "ecosystem": "China's leading AI research institutions and healthtech companies",
        "tone": "professional, collaborative",
        "visa": "willing to relocate to China and apply for Z work visa through employer sponsorship",
        "language_note": "currently studying Mandarin Chinese"
    },
    "CN_EN": {
        "ecosystem": "China's leading AI research institutions and healthtech companies",
        "tone": "professional, collaborative",
        "visa": "willing to relocate to China and apply for Z work visa through employer sponsorship",
        "language_note": "currently studying Mandarin Chinese"
    },
    "DE": {
        "ecosystem": "Germany's engineering-led MedTech and Industry 4.0 ecosystem",
        "tone": "precise, formal, achievement-focused — German professional culture",
        "visa": "eligible for EU Blue Card as a qualified non-EU engineer — requires employer sponsorship",
        "language_note": ""
    },
    "UK": {
        "ecosystem": "the UK's growing AI and digital health innovation sector",
        "tone": "professional but approachable, British business style",
        "visa": "requires UK Skilled Worker visa sponsorship",
        "language_note": ""
    },
    "US": {
        "ecosystem": "the US's leading AI research labs and healthtech startup ecosystem",
        "tone": "confident, results-driven, American professional style",
        "visa": "requires H-1B visa sponsorship",
        "language_note": ""
    },
    "IN": {
        "ecosystem": "India's rapidly expanding AI product companies, deep-tech startups, and research institutions",
        "tone": "professional, enthusiastic",
        "visa": "Indian national — no visa required, immediately eligible to work",
        "language_note": ""
    },
    "AE": {
        "ecosystem": "UAE's AI Strategy 2031, smart city technology, and fintech sector",
        "tone": "professional, results-oriented",
        "visa": "requires UAE employment visa — open to relocation",
        "language_note": ""
    },
    "GLOBAL": {
        "ecosystem": "the global AI research and healthcare technology ecosystem",
        "tone": "neutral, professional, internationally aware",
        "visa": "open to worldwide relocation — requires work visa sponsorship depending on country",
        "language_note": ""
    },
}


async def generate_regional_cover_letter(region: str, experience_years: str = "3+") -> str:
    """
    Generates a country-specific cover letter using the regional prompt map.
    Returns a plain text cover letter body.
    """
    ctx = COVER_LETTER_PROMPTS.get(region, COVER_LETTER_PROMPTS["GLOBAL"])
    language_line = f"- Language commitment: {ctx['language_note']}" if ctx['language_note'] else ""

    prompt = f"""Write a strong, specific professional cover letter for a Python and AI/ML Engineer
applying to companies in {region}.

Candidate background:
- {experience_years} years of Python/AI/ML engineering experience
- Specialises in Healthcare AI, ECG signal processing, deep learning (1D ResNet, CNN, LSTM)
- Research paper in progress on ECG cardiac abnormality detection (PhysioNet dataset)
- Key achievements: 94% F1-score ECG classification model, REST APIs serving 10k+ daily requests at 99.9% uptime, 40% database query optimisation

Country context:
- Target ecosystem: {ctx['ecosystem']}
- Tone: {ctx['tone']}
- Visa situation: {ctx['visa']}
{language_line}

Rules:
- Do NOT use generic phrases like "global tech ecosystem" or "I am driven to contribute"
- Do NOT say "propelled me towards" or "strong professional evolution"
- Reference the specific country or ecosystem by name at least once
- Be specific about technical achievements — use the numbers above
- Maximum 4 paragraphs
- Each cover letter must feel written for {region}, not copy-pasted from another country
- Return ONLY the cover letter body text, no subject line, no salutation header"""

    return await call_groq(prompt)


async def call_groq(prompt: str) -> str:
    """
    Generic helper to call Groq API for plain text responses.
    """
    if not GROQ_API_KEY:
        return "GROQ API Key not configured."

    model_to_use = GROQ_MODEL_70B if "cover letter" in prompt.lower() else GROQ_MODEL
    try:
        response = await client.chat.completions.create(
            model=model_to_use,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API Plain Text Error on {model_to_use}: {e}")
        if model_to_use == GROQ_MODEL_70B:
            print("Falling back to llama-3.1-8b-instant...")
            try:
                response = await client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                return response.choices[0].message.content
            except Exception as fallback_e:
                print(f"Fallback Groq API Plain Text Error: {fallback_e}")
                e = fallback_e

        err_info = handle_groq_error(e)
        raise GroqError(err_info["error"], err_info["solution"], err_info["type"])

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
        response = await call_groq(prompt)
        # Groq might wrap in markdown, though we asked it not to. Let's do a basic strip just in case.
        return response.strip().replace('```', '')
    except Exception as e:
        print(f"Error summarizing about section: {e}")
        return about_text[0] if about_list else ""

async def auto_regenerate_summary_task():
    """Background task to auto-regenerate and save the profile summary."""
    from database import load_data, save_data
    from routes.dynamic_sections import log_activity
    
    data = load_data()
    about_list = data.get("profile", {}).get("about", [])
    if not about_list:
        return
        
    try:
        new_summary = await summarize_about(about_list)
        if new_summary:
            fresh_data = load_data()
            if "profile" not in fresh_data:
                fresh_data["profile"] = {}
            fresh_data["profile"]["summary"] = new_summary
            save_data(fresh_data)
            log_activity("System auto-regenerated summary", "System", None)
    except Exception as e:
        print(f"Auto-regenerate summary failed: {e}")

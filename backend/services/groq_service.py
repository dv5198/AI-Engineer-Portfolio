import os
import json
from groq import AsyncGroq

API_KEY = os.getenv("GROQ_API_KEY")

def get_client():
    if not API_KEY:
        return None
    return AsyncGroq(api_key=API_KEY)

async def generate_project_summary(repo_name: str, repo_desc: str) -> str:
    client = get_client()
    if not client:
        return f"AI summary unavailable (no API key). Original desc: {repo_desc}"
    
    prompt = f"Summarize this open-source project in one concise, engaging sentence suitable for a professional portfolio. Repo name: {repo_name}. Description: {repo_desc}"
    
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional technical writer. Return only the summary JSON object: {\"summary\": \"text\"}"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            response_format={"type": "json_object"}
        )
        result = json.loads(chat_completion.choices[0].message.content)
        return result.get("summary", "AI summary generation failed.")
    except Exception as e:
        print(f"Groq API Error: {e}")
        return "AI summary generation failed."

async def rewrite_text(text: str, instruction: str) -> str:
    client = get_client()
    if not client:
        return text
        
    prompt = f"Rewrite the following text according to this instruction: '{instruction}'. Maintain a professional and engaging tone. Text: {text}"
    
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional editor. Reward the user's text as requested. Return only the rewritten text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192"
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception:
        return text

async def execute_admin_command(command: str, current_data: dict) -> dict:
    client = get_client()
    if not client:
        return {"error": "Groq API key not configured"}
        
    prompt = f"""
    You are an AI assistant managing a portfolio website's JSON state.
    Current state keys: {list(current_data.keys())}
    Command: "{command}"
    
    Return ONLY a raw JSON object representing the exact updates to apply to the state. Do not change keys that the user didn't mention.
    For example, if the command is "Hide the skills section", return {{"sections_visibility": {{"skills": false}}}}.
    Return pure JSON with no markdown block formatting.
    """
    
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON state manager. Return only one action JSON object. No markdown."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

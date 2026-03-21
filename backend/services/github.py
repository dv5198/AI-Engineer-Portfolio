import httpx
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

async def fetch_github_projects(username: str):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            repos = response.json()
            
            # Filter out forks
            filtered = [r for r in repos if not r.get("fork")]
            return filtered
        except Exception as e:
            print(f"Error fetching from GitHub API: {e}")
            return None

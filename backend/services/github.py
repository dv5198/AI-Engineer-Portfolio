import httpx
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

async def fetch_github_projects(username: str):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=15"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            repos = response.json()
            
            # Process and refine repos
            refined_repos = []
            for r in repos:
                if r.get("fork"):
                    continue
                
                refined_repos.append({
                    "id": f"gh_{r.get('id')}",
                    "name": r.get("name"),
                    "summary": r.get("description") or "Open source project on GitHub.",
                    "techStack": r.get("language") or "Code",
                    "stars": r.get("stargazers_count", 0),
                    "url": r.get("html_url"),
                    "updated_at": r.get("updated_at"),
                    "is_github": True # Metadata to distinguish from manual projects
                })
            
            return refined_repos
        except Exception as e:
            print(f"Error fetching from GitHub API: {e}")
            return []

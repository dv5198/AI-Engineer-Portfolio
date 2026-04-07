import httpx
import os
from dotenv import load_dotenv

async def fetch_github_contributions(username: str):
    load_dotenv(override=True)
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token or github_token == "your_github_token_here_optional":
        return {"error": "GITHUB_TOKEN not configured properly"}

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
              }
            }
          }
        }
      }
    }
    """
    
    headers = {"Authorization": f"bearer {github_token}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": {"login": username}},
                headers=headers
            )
            data = response.json()
            
            if "message" in data and data["message"] == "Bad credentials":
                return {"error": "Invalid GitHub Token - Bad Credentials"}
            
            if "errors" in data:
                return {"error": data["errors"][0]["message"]}
                
            return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        except Exception as e:
            return {"error": f"Exception: {str(e)} - Raw Response: {data}"}


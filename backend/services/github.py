import httpx
import os
import re
import base64
import time
import asyncio
from services.cache_service import get_cached_project_bullets, set_cached_project_bullets

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# ─────────────────────────────────────────────
# README IMAGE PARSING HELPERS
# ─────────────────────────────────────────────

# Patterns to find images in README markdown, in priority order
_IMAGE_PATTERNS = [
    # 1. HTML img tag  <img src="...">
    re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE),
    # 2. Markdown image  ![alt](url)
    re.compile(r'!\[[^\]]*\]\(([^)]+)\)'),
    # 3. Markdown image with title  ![alt](url "title")
    re.compile(r'!\[[^\]]*\]\(([^\s)]+)\s+"[^"]*"\)'),
]

# File extensions we accept as images
_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}

# Paths we skip — badges, logos, icons that aren't project screenshots
_SKIP_PATTERNS = re.compile(
    r'(badge|shield|travis|coveralls|codecov|npm|pypi|license|'
    r'logo|icon|avatar|banner|hits|visitor|made.with|built.with|'
    r'vercel\.app|buymeacoffee\.com|ko-fi\.com|paypalobjects\.com|'
    r'discordapp\.com/api/guilds|herokuapp\.com)',
    re.IGNORECASE
)


def _is_valid_image_url(url: str) -> bool:
    """Returns True if URL looks like a real project screenshot, not a badge."""
    if not url:
        return False
    # Must have an image extension or be a known image host
    has_ext = any(url.lower().endswith(ext) for ext in _IMAGE_EXTENSIONS)
    is_image_host = any(host in url for host in [
        'raw.githubusercontent.com',
        'user-images.githubusercontent.com',
        'imgur.com',
        'i.imgur.com',
    ])
    if not (has_ext or is_image_host):
        return False
    # Skip badges and icons
    if _SKIP_PATTERNS.search(url):
        return False
    return True


def _resolve_image_url(raw_url: str, username: str, repo: str, default_branch: str = "main") -> str:
    """
    Converts any README image reference to a fully qualified raw URL.

    Handles:
    - Already absolute URLs  → return as-is
    - Relative paths like  screenshots/demo.png
      → https://raw.githubusercontent.com/{username}/{repo}/{branch}/{path}
    - Paths starting with ./  → strip ./ and resolve
    """
    url = raw_url.strip()

    # Already absolute
    if url.startswith('http://') or url.startswith('https://'):
        # Convert github.com blob URLs to raw URLs
        if 'github.com' in url and '/blob/' in url:
            url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        return url

    # Relative path — resolve to raw.githubusercontent.com
    path = url.lstrip('.').lstrip('/')
    return f"https://raw.githubusercontent.com/{username}/{repo}/{default_branch}/{path}"


def _extract_first_image(readme_content: str, username: str, repo: str, branch: str) -> str | None:
    """
    Extracts the first valid project screenshot from README markdown content.
    Returns a fully resolved raw URL, or None if no suitable image found.
    """
    for pattern in _IMAGE_PATTERNS:
        matches = pattern.findall(readme_content)
        for raw_url in matches:
            # Skip data URIs
            if raw_url.startswith('data:'):
                continue
            resolved = _resolve_image_url(raw_url, username, repo, branch)
            if _is_valid_image_url(resolved):
                return resolved
    return None


# ─────────────────────────────────────────────
# README FETCHER
# ─────────────────────────────────────────────

async def fetch_readme_image(
    client: httpx.AsyncClient,
    headers: dict,
    username: str,
    repo: str,
    default_branch: str = "main"
) -> str | None:
    """
    Fetches the README for a repo and extracts the first project screenshot.

    Tries default_branch first, then falls back to 'master' if not found.
    Returns image URL string or None — never raises.
    """
    for branch in [default_branch, "master", "main"]:
        try:
            url = f"https://api.github.com/repos/{username}/{repo}/readme"
            response = await client.get(url, headers=headers, timeout=8.0)

            if response.status_code == 404:
                continue
            response.raise_for_status()

            data = response.json()
            # README content is base64 encoded by GitHub API
            content_b64 = data.get("content", "")
            if not content_b64:
                return None

            readme_text = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            image_url = _extract_first_image(readme_text, username, repo, branch)
            if image_url:
                return image_url

        except Exception as e:
            print(f"[fetch_readme_image] {repo} ({branch}): {e}")
            continue

    return None


# ─────────────────────────────────────────────
# IN-MEMORY README IMAGE CACHE
# ─────────────────────────────────────────────

_readme_image_cache: dict = {}       # repo_name → image_url or None
_readme_image_cache_ts: dict = {}    # repo_name → timestamp
_README_CACHE_TTL = 3600             # 1 hour — READMEs don't change often


def _get_cached_readme_image(repo: str) -> tuple[bool, str | None]:
    """Returns (found, value). found=True means cache hit (even if value is None)."""
    if repo not in _readme_image_cache:
        return False, None
    if time.time() - _readme_image_cache_ts.get(repo, 0) > _README_CACHE_TTL:
        del _readme_image_cache[repo]
        del _readme_image_cache_ts[repo]
        return False, None
    return True, _readme_image_cache[repo]


def _set_cached_readme_image(repo: str, url: str | None) -> None:
    _readme_image_cache[repo] = url
    _readme_image_cache_ts[repo] = time.time()


def clear_readme_image_cache() -> None:
    """Call this when GitHub webhook fires to force fresh README fetches."""
    _readme_image_cache.clear()
    _readme_image_cache_ts.clear()

def clear_readme_cache_for_repo(repo: str) -> None:
    """Selectively clears the README image cache for a specific repo."""
    _readme_image_cache.pop(repo, None)
    _readme_image_cache_ts.pop(repo, None)


# ─────────────────────────────────────────────
# MAIN FETCH FUNCTION
# ─────────────────────────────────────────────

async def fetch_github_projects(username: str) -> list:
    """
    Fetches GitHub repos for a user and enriches each with:
    - README image (first project screenshot found)
    - Existing metadata: name, description, tech, stars, url

    README images are fetched concurrently with a soft limit
    and cached for 1 hour to avoid GitHub API rate limits.

    Returns list of project dicts ready for portfolio rendering.
    """
    token = os.getenv("GITHUB_TOKEN") or GITHUB_TOKEN
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=15"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            repos = response.json()
        except Exception as e:
            print(f"[fetch_github_projects] Error fetching repo list: {e}")
            return []

        # Filter forks
        repos = [r for r in repos if not r.get("fork")]

        async def enrich_repo(r: dict) -> dict:
            repo_name = r.get("name", "")
            default_branch = r.get("default_branch", "main")

            # Check cache first
            cached_hit, cached_image = _get_cached_readme_image(repo_name)
            if cached_hit:
                image_url = cached_image
            else:
                # Fetch README image — runs concurrently with other repos
                image_url = await fetch_readme_image(
                    client, headers, username, repo_name, default_branch
                )
                _set_cached_readme_image(repo_name, image_url)

            return {
                "id": f"gh_{r.get('id')}",
                "name": repo_name,
                "summary": r.get("description") or "Open source project on GitHub.",
                "description": r.get("description") or "",
                "techStack": r.get("language") or "Code",
                "stars": r.get("stargazers_count", 0),
                "url": r.get("html_url"),
                "updated_at": r.get("updated_at"),
                "default_branch": default_branch,
                # NEW — README image for portfolio cards and resume
                "image": image_url,          # None if no image found
                "has_image": image_url is not None,
                "is_github": True,
            }

        # Run all README fetches concurrently (httpx client is shared — efficient)
        enriched = await asyncio.gather(
            *[enrich_repo(r) for r in repos],
            return_exceptions=False
        )

        return list(enriched)

import time
from typing import Dict, Tuple

# Stores region -> (pdf_bytes, timestamp)
pdf_cache: Dict[str, Tuple[bytes, float]] = {}
PDF_TTL = 300  # 5 minutes

# Stores IP -> country_dict
ip_cache: Dict[str, dict] = {}

def get_cached_pdf(region: str) -> bytes:
    if region in pdf_cache:
        pdf_bytes, ts = pdf_cache[region]
        if time.time() - ts < PDF_TTL:
            return pdf_bytes
    return None

def set_cached_pdf(region: str, pdf_bytes: bytes):
    pdf_cache[region] = (pdf_bytes, time.time())

def clear_pdf_cache():
    pdf_cache.clear()

# Project bullet cache — persists for 24 hours
# Key: project name (lowercased, stripped)
# Value: list of bullet strings
_project_bullet_cache: dict = {}
_project_bullet_cache_ttl: dict = {}
PROJECT_BULLET_CACHE_TTL = 86400  # 24 hours

def get_cached_project_bullets(project_name: str) -> list | None:
    """Returns cached bullets for a project, or None if expired/missing."""
    key = project_name.lower().strip()
    if key not in _project_bullet_cache:
        return None
    if time.time() - _project_bullet_cache_ttl.get(key, 0) > PROJECT_BULLET_CACHE_TTL:
        del _project_bullet_cache[key]
        del _project_bullet_cache_ttl[key]
        return None
    return _project_bullet_cache[key]

def set_cached_project_bullets(project_name: str, bullets: list) -> None:
    """Caches generated bullets for a project."""
    key = project_name.lower().strip()
    _project_bullet_cache[key] = bullets
    _project_bullet_cache_ttl[key] = time.time()

def clear_project_bullet_cache() -> None:
    """Clears all cached project bullets (call when projects are updated)."""
    _project_bullet_cache.clear()
    _project_bullet_cache_ttl.clear()

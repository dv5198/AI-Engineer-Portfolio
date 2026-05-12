import time
from typing import Dict, Tuple

from database import get_cached_pdf_db, save_cached_pdf_db, clear_pdf_cache_db
PDF_TTL = 300  # 5 minutes

# Stores IP -> country_dict
ip_cache: Dict[str, dict] = {}

def get_cached_pdf(region: str) -> bytes:
    return get_cached_pdf_db(region, ttl_seconds=PDF_TTL)

def set_cached_pdf(region: str, pdf_bytes: bytes):
    save_cached_pdf_db(region, pdf_bytes)

def clear_pdf_cache():
    clear_pdf_cache_db()

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

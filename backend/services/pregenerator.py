# backend/services/pregenerator.py
"""
Pre-generation service.

Builds all regional resume PDFs in the background and stores them on disk.
User downloads then become instant file-serves (~200ms) instead of 20-45s pipelines.

Folder layout:
    backend/generated_pdfs/
        metadata.json          ← generation timestamp + per-region status
        international_en.pdf
        ats_usa_en.pdf
        ats_uk_en.pdf
        india_en.pdf
        germany_en.pdf
        middleeast_en.pdf
        japan_ja.pdf           ← merged Rirekisho + Shokumu
        japan_en.pdf           ← Japan English variant
        korea_ko.pdf
        korea_en.pdf
        china_zh.pdf
        china_en.pdf
"""

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from database import load_data
from services.github import fetch_github_projects

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent.parent
OUTPUT_DIR      = BASE_DIR / "generated_pdfs"
METADATA_FILE   = OUTPUT_DIR / "metadata.json"

# All 12 resume variants: (region_key, lang, include_cover, output_filename)
RESUME_VARIANTS = [
    ("international", "en",  True,  "international_en.pdf"),
    ("ats_usa",       "en",  False, "ats_usa_en.pdf"),
    ("ats_uk",        "en",  False, "ats_uk_en.pdf"),
    ("india",         "en",  False, "india_en.pdf"),
    ("germany",       "en",  True,  "germany_en.pdf"),
    ("middleeast",    "en",  True,  "middleeast_en.pdf"),
    ("japan",         "ja",  True,  "japan_ja.pdf"),
    ("japan",         "en",  True,  "japan_en.pdf"),
    ("korea",         "ko",  True,  "korea_ko.pdf"),
    ("korea",         "en",  True,  "korea_en.pdf"),
    ("china",         "zh",  True,  "china_zh.pdf"),
    ("china",         "en",  True,  "china_en.pdf"),
]

# ── State ─────────────────────────────────────────────────────────────────────
_generation_lock = asyncio.Lock()
_is_generating   = False


# ── Metadata helpers ──────────────────────────────────────────────────────────

def _read_metadata() -> dict:
    if METADATA_FILE.exists():
        try:
            return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"status": "never_generated", "last_generated": None, "variants": {}}


def _write_metadata(data: dict):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_status() -> dict:
    meta = _read_metadata()
    return {
        "status":         meta.get("status", "never_generated"),
        "last_generated": meta.get("last_generated"),
        "is_generating":  _is_generating,
        "variants":       meta.get("variants", {}),
    }


# ── Disk-based PDF serve ──────────────────────────────────────────────────────

def get_prebuilt_pdf(region: str, lang: str) -> Optional[bytes]:
    """
    Returns the pre-built PDF bytes for the given region+lang, or None if not
    available (i.e. first deploy, or still generating).
    """
    filename = _region_lang_to_filename(region, lang)
    if filename is None:
        return None
    path = OUTPUT_DIR / filename
    if path.exists():
        try:
            return path.read_bytes()
        except Exception:
            return None
    return None


def _region_lang_to_filename(region: str, lang: str) -> Optional[str]:
    for r, l, _, fname in RESUME_VARIANTS:
        if r == region and l == lang:
            return fname
    return None


# ── Core generation logic ─────────────────────────────────────────────────────

async def _build_merged_projects(data: dict) -> list:
    """Fetches GitHub projects and merges with manual projects — same logic as resume.py."""
    profile        = data.get("profile", {})
    github_username = profile.get("github_username")
    github_projects = []
    if github_username:
        try:
            github_projects = await fetch_github_projects(github_username)
        except Exception as e:
            print(f"[pregenerator] GitHub fetch failed: {e}")

    manual_projects = data.get("projects", [])
    visible_manual  = [p for p in manual_projects if p.get("visible") is not False]

    visibility_map = data.get("project_visibility", {})
    hidden_list    = data.get("hiddenProjects", [])
    manual_names   = {p.get("name", "").lower().strip() for p in visible_manual}

    final_github = [
        p for p in github_projects
        if visibility_map.get(p.get("name")) is not False
        and p.get("name") not in hidden_list
        and p.get("name", "").lower().strip() not in manual_names
    ]
    final_github.sort(key=lambda x: (x.get("stars", 0), x.get("updated_at", "")), reverse=True)

    return visible_manual + final_github[:3]


async def _generate_one(
    data:          dict,
    merged_projects: list,
    region:        str,
    lang:          str,
    include_cover: bool,
    output_path:   Path,
) -> bool:
    """Generates a single PDF variant and saves it to disk. Returns True on success."""
    from services.pdf_playwright import generate_resume_playwright
    from services.geo_rules import get_geo_rule

    geo = get_geo_rule(region)
    include_photo = geo.get("photo", False)

    try:
        buffer = await generate_resume_playwright(
            data,
            live_projects=merged_projects,
            region=region,
            include_photo=include_photo,
            lang=lang,
            include_cover=include_cover,
        )
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(buffer.getvalue())
        return True
    except Exception as e:
        print(f"[pregenerator] Failed to generate {output_path.name}: {e}")
        return False


async def regenerate_all(triggered_by: str = "manual") -> dict:
    """
    Generates all 12 PDF variants sequentially, updating metadata after each one.
    Uses a lock so only one generation can run at a time.
    Safe to call from background tasks.
    """
    global _is_generating

    if _is_generating:
        return {"status": "already_running", "message": "Generation already in progress."}

    async with _generation_lock:
        _is_generating = True
        meta = _read_metadata()
        meta["status"]       = "generating"
        meta["triggered_by"] = triggered_by
        meta["started_at"]   = datetime.now(timezone.utc).isoformat()
        _write_metadata(meta)

        print(f"[pregenerator] Starting full regeneration (triggered by: {triggered_by})")

        try:
            data            = load_data()
            merged_projects = await _build_merged_projects(data)
            results         = {}

            for region, lang, include_cover, filename in RESUME_VARIANTS:
                output_path = OUTPUT_DIR / filename
                t_start     = time.monotonic()
                success     = await _generate_one(data, merged_projects, region, lang, include_cover, output_path)
                elapsed     = round(time.monotonic() - t_start, 1)
                results[filename] = {
                    "ok":      success,
                    "elapsed": f"{elapsed}s",
                    "region":  region,
                    "lang":    lang,
                }
                status_icon = "OK" if success else "FAIL"
                print(f"[pregenerator] {status_icon} {filename} ({elapsed}s)")

            all_ok = all(v["ok"] for v in results.values())
            meta.update({
                "status":         "ready" if all_ok else "partial",
                "last_generated": datetime.now(timezone.utc).isoformat(),
                "variants":       results,
            })
            _write_metadata(meta)
            print(f"[pregenerator] Done — {'all OK' if all_ok else 'some variants failed'}.")
            return {"status": meta["status"], "variants": results}

        except Exception as e:
            meta["status"] = "error"
            meta["error"]  = str(e)
            _write_metadata(meta)
            print(f"[pregenerator] Fatal error: {e}")
            raise
        finally:
            _is_generating = False


async def regenerate_if_empty():
    """
    Called on server startup. Generates all PDFs only if the output folder is
    empty (first deploy / fresh server). Runs in background — does not block startup.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing_pdfs = list(OUTPUT_DIR.glob("*.pdf"))
    if not existing_pdfs:
        print("[pregenerator] No pre-built PDFs found. Running cold-start generation...")
        await regenerate_all(triggered_by="startup")
    else:
        print(f"[pregenerator] Found {len(existing_pdfs)} pre-built PDFs. Skipping startup generation.")

# backend/services/geo.py

import httpx

# Mapping of country codes to resume regions
REGION_MAP = {
    # ── No photo — ATS strict (Western/International) ──
    'US': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'GB': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'CA': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'AU': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'NZ': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'IE': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'NL': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'SE': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'NO': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'DK': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'FI': { 'region': 'international', 'photo': False, 'label': 'International (ATS)', 'filename': 'divya_nirankari_resume.pdf' },
    'SG': { 'region': 'international', 'photo': False, 'label': 'Singapore', 'filename': 'divya_nirankari_resume.pdf' },
    'HK': { 'region': 'international', 'photo': False, 'label': 'Hong Kong', 'filename': 'divya_nirankari_resume.pdf' },
    'IN': { 'region': 'international', 'photo': False, 'label': 'India (ATS)', 'filename': 'divya_nirankari_resume.pdf' },

    # ── Photo mandatory — East Asia ──────────────────
    'KR': { 'region': 'korea', 'photo': True, 'label': 'South Korea (이력서)', 'filename': 'divya_nirankari_이력서.pdf' },
    'JP': { 'region': 'japan', 'photo': True, 'label': 'Japan (履歴書)', 'filename': 'divya_nirankari_履歴書.pdf' },
    'CN': { 'region': 'china', 'photo': True, 'label': 'China (简历)', 'filename': 'divya_nirankari_简历.pdf' },
    'TW': { 'region': 'china', 'photo': True, 'label': 'Taiwan', 'filename': 'divya_nirankari_resume_tw.pdf' },

    # ── Photo expected — Europe ────────────────────
    'DE': { 'region': 'germany', 'photo': True, 'label': 'Germany (Lebenslauf)', 'filename': 'divya_nirankari_lebenslauf.pdf' },
    'AT': { 'region': 'germany', 'photo': True, 'label': 'Austria', 'filename': 'divya_nirankari_lebenslauf.pdf' },
    'CH': { 'region': 'germany', 'photo': True, 'label': 'Switzerland', 'filename': 'divya_nirankari_lebenslauf.pdf' },
    'FR': { 'region': 'germany', 'photo': True, 'label': 'France', 'filename': 'divya_nirankari_resume_fr.pdf' },
    'ES': { 'region': 'germany', 'photo': True, 'label': 'Spain', 'filename': 'divya_nirankari_resume_es.pdf' },
    'IT': { 'region': 'germany', 'photo': True, 'label': 'Italy', 'filename': 'divya_nirankari_resume_it.pdf' },
    'PL': { 'region': 'germany', 'photo': True, 'label': 'Poland', 'filename': 'divya_nirankari_resume_pl.pdf' },
    'PT': { 'region': 'germany', 'photo': True, 'label': 'Portugal', 'filename': 'divya_nirankari_resume_pt.pdf' },
    'BE': { 'region': 'germany', 'photo': True, 'label': 'Belgium', 'filename': 'divya_nirankari_resume_be.pdf' },
    'CZ': { 'region': 'germany', 'photo': True, 'label': 'Czech Republic', 'filename': 'divya_nirankari_resume_cz.pdf' },
    'RO': { 'region': 'germany', 'photo': True, 'label': 'Romania', 'filename': 'divya_nirankari_resume_ro.pdf' },
    'HU': { 'region': 'germany', 'photo': True, 'label': 'Hungary', 'filename': 'divya_nirankari_resume_hu.pdf' },

    # ── Photo expected — Middle East ─────────────────
    'AE': { 'region': 'middleeast', 'photo': True, 'label': 'UAE', 'filename': 'divya_nirankari_resume_uae.pdf' },
    'SA': { 'region': 'middleeast', 'photo': True, 'label': 'Saudi Arabia', 'filename': 'divya_nirankari_resume_sa.pdf' },
    'QA': { 'region': 'middleeast', 'photo': True, 'label': 'Qatar', 'filename': 'divya_nirankari_resume_qa.pdf' },
    'KW': { 'region': 'middleeast', 'photo': True, 'label': 'Kuwait', 'filename': 'divya_nirankari_resume_kw.pdf' },
    'BH': { 'region': 'middleeast', 'photo': True, 'label': 'Bahrain', 'filename': 'divya_nirankari_resume_bh.pdf' },
    'OM': { 'region': 'middleeast', 'photo': True, 'label': 'Oman', 'filename': 'divya_nirankari_resume_om.pdf' },

    # ── Development / Localhost ─
    'DEV': { 'region': 'international', 'photo': False, 'label': 'Development (default)', 'filename': 'divya_nirankari_resume.pdf' },
}

DEFAULT_REGION = {
    'region': 'international',
    'photo': False,
    'label': 'International (ATS)',
    'filename': 'divya_nirankari_resume.pdf',
}

async def get_country_from_ip(ip: str) -> dict:
    """Detects country code and name from IP using ip-api.com."""
    local_ips = ['127.0.0.1', 'localhost', '::1', '0.0.0.0']
    if ip in local_ips or ip.startswith('192.168.') or ip.startswith('10.'):
        return {'code': 'IN', 'name': 'India'}
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f'http://ip-api.com/json/{ip}?fields=status,countryCode,country')
            data = res.json()
            if data.get('status') == 'success':
                return {
                    'code': data.get('countryCode', 'US'),
                    'name': data.get('country', 'United States')
                }
    except Exception:
        pass
    return {'code': 'US', 'name': 'United States'}


def get_visitor_ip(request) -> str:
    """Extracts visitor IP from request headers (proxy/direct)."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host

def country_to_region(country_code: str) -> dict:
    """Maps country code to region configuration."""
    return REGION_MAP.get(country_code, DEFAULT_REGION)

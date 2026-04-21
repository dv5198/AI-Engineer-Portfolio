# backend/services/geo.py

import httpx
import ipaddress
import json
import os
from datetime import datetime, timedelta

# In-memory cache for IP lookups to avoid rate limits
IP_CACHE = {}
CACHE_TTL_HOURS = 24

def load_geo_config():
    """Loads regional mapping config from JSON file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'geo_regions.json')
    mapping = {}
    
    # ── Hard Fallback (in case JSON is missing) ──────────────────
    default_config = { 'region': 'international', 'photo': False, 'label': 'India (ATS)', 'filename': 'divya_nirankari_resume.pdf' }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Expand standard categories
                for category, details in data.items():
                    if category == 'specific_overrides': continue
                    for country_code in details.get('countries', []):
                        mapping[country_code] = details['config']
                
                # Apply specific overrides (e.g., individual labels for SG, HK)
                overrides = data.get('specific_overrides', {})
                for country_code, config in overrides.items():
                    mapping[country_code] = config
        else:
            print(f"Warning: {config_path} not found. Using minimal fallback.")
            mapping['IN'] = default_config
    except Exception as e:
        print(f"Error loading geo config: {e}")
        mapping['IN'] = default_config
        
    return mapping

# Global Map Initialized on Startup
REGION_MAP = load_geo_config()
DEFAULT_REGION = REGION_MAP.get('IN', { 'region': 'international', 'photo': False, 'label': 'India (ATS)', 'filename': 'divya_nirankari_resume.pdf' })

async def get_country_from_ip(ip: str) -> dict:
    """Detects country code and name from IP using ip-api.com with local caching."""
    now = datetime.now()
    
    # 1. Local/Private IP Check
    try:
        if ip in ['localhost', '::1']:
            return {'code': 'IN', 'name': 'India (Localhost)'}
        
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            return {'code': 'IN', 'name': 'India (Private Network)'}
    except ValueError:
        return {'code': 'IN', 'name': 'India (Unknown/Local)'}
    
    # 2. Cache Check
    if ip in IP_CACHE:
        entry = IP_CACHE[ip]
        if entry['expires'] > now:
            return entry['data']

    # 3. API Lookup
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f'http://ip-api.com/json/{ip}?fields=status,countryCode,country')
            data = res.json()
            if data.get('status') == 'success':
                geo_info = {
                    'code': data.get('countryCode', 'IN'),
                    'name': data.get('country', 'India')
                }
                # Update Cache
                IP_CACHE[ip] = {
                    'data': geo_info,
                    'expires': now + timedelta(hours=CACHE_TTL_HOURS)
                }
                return geo_info
    except Exception as e:
        print(f"Geo-Detection Error for {ip}: {e}")
        pass
        
    return {'code': 'IN', 'name': 'India (Fallback)'}


def get_visitor_ip(request) -> str:
    """Extracts visitor IP from request headers (proxy/direct)."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host

def country_to_region(country_code: str) -> dict:
    """Maps country code to region configuration."""
    return REGION_MAP.get(country_code, DEFAULT_REGION)

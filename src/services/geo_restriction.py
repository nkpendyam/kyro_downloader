"""Geo-restriction bypass service."""

import requests
from src.utils.logger import get_logger
logger = get_logger(__name__)

COUNTRY_CODES = {
    "US": "United States", "GB": "United Kingdom", "CA": "Canada", "AU": "Australia",
    "DE": "Germany", "FR": "France", "JP": "Japan", "KR": "South Korea",
    "IN": "India", "BR": "Brazil", "MX": "Mexico", "RU": "Russia",
    "CN": "China", "IT": "Italy", "ES": "Spain", "NL": "Netherlands",
    "SE": "Sweden", "NO": "Norway", "DK": "Denmark", "FI": "Finland",
}

def get_proxy_for_country(country_code: str) -> str | None:
    proxy_url = __import__("os").environ.get("KYRO_PROXY_URL")
    if proxy_url:
        return proxy_url
    return None

def build_geo_opts(proxy_url: str | None = None, geo_bypass_country: str | None = None) -> dict[str, str]:
    opts: dict[str, str] = {}
    if proxy_url:
        opts["proxy"] = proxy_url
    if geo_bypass_country and geo_bypass_country in COUNTRY_CODES:
        opts["geo_bypass_country"] = geo_bypass_country
    return opts

def check_geo_restriction(url: str, country_code: str | None = None) -> bool:
    try:
        headers: dict[str, str] = {}
        if country_code and country_code in COUNTRY_CODES:
            headers["Accept-Language"] = f"{country_code.lower()}-{country_code.upper()}"
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True, stream=True)
        response.close()
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Geo check failed: {e}")
        return False

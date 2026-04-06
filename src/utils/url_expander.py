"""URL shortener expansion utility."""

import requests

from src.utils.logger import get_logger

logger = get_logger(__name__)


def expand_url(short_url: str, max_redirects: int = 10) -> str:
    del max_redirects
    try:
        r = requests.head(short_url, allow_redirects=True, timeout=10)
        if r.status_code in (200, 301, 302):
            return r.url
        r = requests.get(short_url, allow_redirects=True, timeout=10, stream=True)
        r.close()
        return r.url
    except Exception as e:
        logger.warning(f"Failed to expand URL: {e}")
        return short_url

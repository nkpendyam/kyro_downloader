"""Link grabber - extract all video URLs from a webpage."""
import re
import requests
from urllib.parse import urlparse
from src.utils.logger import get_logger
logger = get_logger(__name__)

_BLOCKED_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0", "::1"}
_BLOCKED_PREFIXES = ("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.", "169.254.")

VIDEO_PATTERNS = [
    r'youtube\.com/watch\?v=[\w-]+',
    r'youtu\.be/[\w-]+',
    r'vimeo\.com/[\d]+',
    r'dailymotion\.com/video/[\w]+',
    r'twitch\.tv/videos/[\d]+',
    r'soundcloud\.com/[\w-]+/[\w-]+',
    r'/watch\?v=[\w-]+',
    r'/video/[\d]+',
]

def _is_safe_url(url):
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if host in _BLOCKED_HOSTS:
            return False
        return not any(host.startswith(p) for p in _BLOCKED_PREFIXES)
    except Exception:
        return False

def grab_links(url, patterns=None):
    """Extract all video URLs from a webpage."""
    patterns = patterns or VIDEO_PATTERNS
    if not _is_safe_url(url):
        logger.warning(f"Blocked SSRF attempt: {url}")
        return []
    found = set()
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if match.startswith("http"):
                    if _is_safe_url(match):
                        found.add(match)
                elif match.startswith("/"):
                    from urllib.parse import urljoin
                    full = urljoin(url, match)
                    if _is_safe_url(full):
                        found.add(full)
                else:
                    full = f"https://www.youtube.com{match}"
                    if _is_safe_url(full):
                        found.add(full)
    except Exception as e:
        logger.warning(f"Link grabber failed: {e}")
    return list(found)

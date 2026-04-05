"""Input validation utilities."""
import re
import os
from pathlib import Path
from urllib.parse import urlparse

SUPPORTED_PLATFORMS = ["youtube.com","youtu.be","vimeo.com","dailymotion.com","twitter.com","x.com","twitch.tv","reddit.com","tiktok.com","instagram.com","facebook.com","soundcloud.com","bandcamp.com","peertube.tv","threads.net","pinterest.com","snapchat.com","linkedin.com","tumblr.com","bilibili.com"]

def validate_url(url):
    if not url or not isinstance(url, str):
        return False
    return bool(re.match(r"^https?://(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}|(?:\d{1,3}\.){3}\d{1,3})(?::\d+)?(?:/[^\s]*)?$", url))

def validate_platform(url):
    if not validate_url(url): return None
    try:
        domain = urlparse(url).netloc.lower().replace("www.","")
        for p in SUPPORTED_PLATFORMS:
            if domain == p or domain.endswith(f".{p}"): return p
    except: pass
    return None

def validate_output_path(path):
    if not path or not path.strip(): path = os.path.join(os.getcwd(), "downloads")
    output_path = Path(path).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

def validate_integer(value, min_val=None, max_val=None):
    try:
        num = int(value)
        if min_val is not None and num < min_val: return None
        if max_val is not None and num > max_val: return None
        return num
    except (ValueError, TypeError): return None

def sanitize_filename(filename):
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename).strip()
    return sanitized[:200] if sanitized else "untitled"

def validate_batch_file(filepath):
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Batch file not found: {filepath}")
    urls = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and validate_url(line):
                    urls.append(line)
    except PermissionError as e:
        raise PermissionError(f"Cannot read batch file: {filepath}") from e
    return urls

"""Watch Later integration."""
from typing import Any

from src.utils.logger import get_logger
from src.core.downloader import get_video_info
logger = get_logger(__name__)
WATCH_LATER_PLAYLIST_ID = "WL"
WATCH_LATER_URL_TEMPLATE = "https://www.youtube.com/playlist?list={}"

def get_watch_later_url(playlist_id: str = WATCH_LATER_PLAYLIST_ID) -> str:
    return WATCH_LATER_URL_TEMPLATE.format(playlist_id)

def get_watch_later_info() -> Any:
    url = get_watch_later_url()
    try: return get_video_info(url)
    except Exception as e:
        logger.warning(f"Could not fetch Watch Later info: {e}")
        return None

def extract_playlist_id(url: str) -> str | None:
    import re
    match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url)
    if match: return match.group(1)
    return None

def is_watch_later_url(url: str) -> bool:
    playlist_id = extract_playlist_id(url)
    return playlist_id == WATCH_LATER_PLAYLIST_ID or "watchlater" in url.lower()

def build_watch_later_download_config(cookies_file: str | None = None) -> dict[str, Any]:
    return {"cookies_file": cookies_file, "prefer_format": "mp4", "embed_thumbnail": True, "embed_metadata": True, "playlist": {"sleep_interval": 2, "concurrent_downloads": 1}}

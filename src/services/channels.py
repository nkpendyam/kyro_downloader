"""Channel download service."""
from typing import Any

import yt_dlp
from src.utils.logger import get_logger
logger = get_logger(__name__)

def get_channel_info(channel_url: str) -> dict[str, Any] | None:
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
        return {"title": info.get("title", ""), "uploader": info.get("uploader", ""), "entries": info.get("entries", []), "entry_count": len(info.get("entries", []))}
    except Exception as e:
        logger.error(f"Channel info failed: {e}")
        return None

def download_channel(channel_url: str, output_path: str, config: dict[str, Any] | None = None, progress_tracker: Any | None = None) -> Any:
    from src.core.downloader import download_playlist
    return download_playlist(url=channel_url, output_path=output_path, config=config, progress_tracker=progress_tracker)

"""Search within platforms service."""
import yt_dlp
from src.utils.logger import get_logger
logger = get_logger(__name__)

def search_platform(query, platform="youtube", max_results=10, sort_by="relevance"):
    ydl_opts = {
        "quiet": True, "no_warnings": True, "skip_download": True,
        "extract_flat": True, "playlistend": max_results,
    }
    if platform == "youtube":
        search_query = f"ytsearch{max_results}:{query}"
    elif platform == "soundcloud":
        search_query = f"scsearch{max_results}:{query}"
    else:
        search_query = f"{platform}search{max_results}:{query}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(search_query, download=False)
        entries = results.get("entries", [])
        return [{"title": e.get("title", ""), "url": e.get("url", ""), "duration": e.get("duration", 0), "uploader": e.get("uploader", ""), "view_count": e.get("view_count", 0)} for e in entries if e.get("url")]
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

def search_all_platforms(query, max_results=5):
    platforms = ["youtube", "soundcloud"]
    all_results = {}
    for platform in platforms:
        results = search_platform(query, platform, max_results)
        if results: all_results[platform] = results
    return all_results

"""SponsorBlock integration."""
from typing import Any

import requests
from src.utils.logger import get_logger
logger = get_logger(__name__)
SPONSORBLOCK_API = "https://sponsor.ajay.app/api"
CATEGORY_NAMES = {"sponsor": "Sponsor", "intro": "Intermission/Intro", "outro": "Endcards/Credits", "selfpromo": "Self Promotion", "preview": "Preview/Recap", "filler": "Filler Tangent", "interaction": "Interaction Reminder", "music_offtopic": "Music Off Topic"}

def get_segments(video_id: str, categories: list[str] | None = None) -> list[dict[str, Any]]:
    categories = categories or ["sponsor", "intro", "outro", "selfpromo"]
    try:
        params = [("videoID", video_id)]
        for cat in categories:
            params.append(("category", cat))
        response = requests.get(f"{SPONSORBLOCK_API}/skipSegments", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        segments = []
        for entry in data:
            segment = entry.get("segment", {})
            segments.append({"start": segment[0], "end": segment[1], "category": entry.get("category", "unknown"), "category_name": CATEGORY_NAMES.get(entry.get("category", ""), "Unknown"), "uuid": entry.get("UUID", ""), "votes": entry.get("votes", 0)})
        logger.info(f"SponsorBlock: {len(segments)} segments found for {video_id}")
        return segments
    except Exception as e:
        logger.warning(f"SponsorBlock API error: {e}")
        return []

def extract_video_id(url: str) -> str | None:
    import re
    patterns = [r"(?:v=|/v/|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})", r"(?:\?v=|&v=)([a-zA-Z0-9_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match: return match.group(1)
    return None

def format_segments_for_display(segments: list[dict[str, Any]]) -> str:
    if not segments: return "No sponsor segments found"
    lines = ["\n[bold yellow]SponsorBlock Segments:[/bold yellow]"]
    for seg in segments:
        start_min = int(seg["start"]) // 60
        start_sec = int(seg["start"]) % 60
        end_min = int(seg["end"]) // 60
        end_sec = int(seg["end"]) % 60
        lines.append(f"  {seg['category_name']}: {start_min}:{start_sec:02d} - {end_min}:{end_sec:02d}")
    return "\n".join(lines)

def build_sponsorblock_opts(categories: list[str] | None = None) -> dict[str, str]:
    cats = categories or ["sponsor"]
    return {"sponsorblock_mark": ",".join(cats), "sponsorblock_remove": ",".join(cats)}

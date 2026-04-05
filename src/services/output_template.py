"""Output template service for customizable file naming."""
from typing import Any

import re
from datetime import datetime
from pathlib import Path
from src.utils.logger import get_logger
logger = get_logger(__name__)

DEFAULT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"
PLAYLIST_TEMPLATE = "%(playlist)s/%(playlist_index)s - %(title)s [%(id)s].%(ext)s"
CHANNEL_TEMPLATE = "%(uploader)s/%(upload_date)s_%(title)s [%(id)s].%(ext)s"
DATE_TEMPLATE = "%(upload_date)s/%(title)s [%(id)s].%(ext)s"

TEMPLATES = {
    "default": DEFAULT_TEMPLATE,
    "playlist": PLAYLIST_TEMPLATE,
    "channel": CHANNEL_TEMPLATE,
    "date": DATE_TEMPLATE,
}

def apply_template(template: str | None, info: dict[str, Any]) -> str:
    if not template or template in TEMPLATES:
        template = TEMPLATES.get(template, DEFAULT_TEMPLATE)
    result = template
    defaults = {
        "upload_date": datetime.now().strftime("%Y%m%d"),
        "ext": "mp4",
        "title": "untitled",
        "id": "unknown",
        "uploader": "unknown",
        "playlist_index": "1",
    }
    merged = {**defaults, **{k: (v or "") for k, v in info.items()}}
    playlist_val = info.get("playlist_title") or info.get("playlist") or "Playlist"
    merged["playlist"] = playlist_val
    merged["playlist_title"] = playlist_val
    for key, value in merged.items():
        result = result.replace(f"%({key})s", str(value))
    result = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", result)
    return result

def get_output_path(template: str | None, info: dict[str, Any], output_dir: str | Path) -> str:
    filename = apply_template(template, info)
    return str(Path(output_dir) / filename)

"""Format selection and sorting service."""
from src.utils.logger import get_logger
logger = get_logger(__name__)

SORT_KEYS = {
    "res": lambda f: f.get("height") or 0,
    "fps": lambda f: f.get("fps") or 0,
    "vcodec": lambda f: f.get("vcodec") or "",
    "acodec": lambda f: f.get("acodec") or "",
    "filesize": lambda f: f.get("filesize") or f.get("filesize_approx") or 0,
    "abr": lambda f: f.get("abr") or 0,
    "vbr": lambda f: f.get("vbr") or 0,
    "tbr": lambda f: f.get("tbr") or 0,
    "proto": lambda f: f.get("protocol") or "",
    "ext": lambda f: f.get("ext") or "",
}

def sort_formats(formats, sort_by="res", reverse=True):
    key_func = SORT_KEYS.get(sort_by, SORT_KEYS["res"])
    return sorted(formats, key=key_func, reverse=reverse)

def filter_formats(formats, filters=None):
    if not filters: return formats
    result = formats
    for f in filters:
        if f.startswith("height<="):
            h = int(f.split("<=")[1])
            result = [fmt for fmt in result if (fmt.get("height") or 0) <= h]
        elif f.startswith("height>="):
            h = int(f.split(">=")[1])
            result = [fmt for fmt in result if (fmt.get("height") or 0) >= h]
        elif f.startswith("height=="):
            h = int(f.split("==")[1])
            result = [fmt for fmt in result if (fmt.get("height") or 0) == h]
        elif f.startswith("ext=="):
            ext = f.split("==")[1]
            result = [fmt for fmt in result if fmt.get("ext") == ext]
        elif f.startswith("fps>="):
            fps = int(f.split(">=")[1])
            result = [fmt for fmt in result if (fmt.get("fps") or 0) >= fps]
    return result

def get_best_format(formats, quality="best", hdr=False, dolby=False):
    video_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") == "none"]
    audio_formats = [f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"]
    combined_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") != "none"]
    if not video_formats and not audio_formats and not combined_formats:
        return None
    if quality == "best":
        video = max(video_formats, key=lambda f: f.get("height") or 0) if video_formats else None
        audio = max(audio_formats, key=lambda f: f.get("abr") or 0) if audio_formats else None
    else:
        quality_map = {"8k": 4320, "4k": 2160, "2160p": 2160, "1080p": 1080, "720p": 720, "480p": 480}
        target_h = quality_map.get(quality, 1080)
        suitable = [f for f in video_formats if (f.get("height") or 0) <= target_h]
        video = max(suitable, key=lambda f: f.get("height") or 0) if suitable else (video_formats[0] if video_formats else None)
        audio = max(audio_formats, key=lambda f: f.get("abr") or 0) if audio_formats else None
    if not video and not audio and combined_formats:
        video = max(combined_formats, key=lambda f: f.get("height") or 0)
    return {"video": video, "audio": audio}

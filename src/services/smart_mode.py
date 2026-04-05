"""Smart mode - auto-detect best quality based on file size and speed."""
from src.utils.logger import get_logger
logger = get_logger(__name__)

def get_smart_quality(info, max_size_mb=None, min_speed_mbps=None):
    """Determine optimal quality based on video info and constraints.

    Args:
        info: VideoInfo object from get_video_info()
        max_size_mb: Maximum file size in MB (None for no limit)
        min_speed_mbps: Minimum download speed in Mbps (None for no limit)

    Returns:
        dict with quality, format_id, estimated_size_mb, reason
    """
    formats = info.formats or []
    if not formats:
        return {"quality": "best", "format_id": None, "estimated_size_mb": 0, "reason": "No formats available"}

    # Filter video-only formats
    video_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") == "none"]
    if not video_formats:
        video_formats = [f for f in formats if f.get("vcodec") != "none"]

    if not video_formats:
        return {"quality": "best", "format_id": None, "estimated_size_mb": 0, "reason": "No video formats"}

    # Sort by height descending
    video_formats.sort(key=lambda f: f.get("height") or 0, reverse=True)

    # If no constraints, pick best
    if not max_size_mb and not min_speed_mbps:
        best = video_formats[0]
        return {
            "quality": "best",
            "format_id": best.get("format_id"),
            "estimated_size_mb": (best.get("filesize") or best.get("filesize_approx") or 0) / 1_000_000,
            "reason": "Best quality (no constraints)"
        }

    # Find best format within constraints
    for fmt in video_formats:
        size_mb = (fmt.get("filesize") or fmt.get("filesize_approx") or 0) / 1_000_000
        if max_size_mb and size_mb > max_size_mb:
            continue
        height = fmt.get("height") or 0
        if min_speed_mbps and height > 1080:
            # Higher quality needs faster connection
            continue
        return {
            "quality": f"{height}p" if height else "best",
            "format_id": fmt.get("format_id"),
            "estimated_size_mb": size_mb,
            "reason": f"Best within constraints ({height}p, {size_mb:.0f}MB)"
        }

    # Fallback to lowest quality
    fallback = video_formats[-1]
    return {
        "quality": "480p",
        "format_id": fallback.get("format_id"),
        "estimated_size_mb": (fallback.get("filesize") or fallback.get("filesize_approx") or 0) / 1_000_000,
        "reason": "Fallback to lowest quality"
    }

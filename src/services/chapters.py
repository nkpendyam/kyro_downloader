"""Chapter extraction service."""
import os
import subprocess
import json
from src.utils.logger import get_logger
from src.utils.ffmpeg import check_ffmpeg
logger = get_logger(__name__)

def extract_chapters(video_path):
    if not check_ffmpeg():
        logger.error("FFmpeg not available")
        return []
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_chapters", str(video_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            chapters = []
            for ch in data.get("chapters", []):
                chapters.append({"title": ch.get("tags", {}).get("title", f"Chapter {len(chapters)+1}"), "start": float(ch.get("start_time", 0)), "end": float(ch.get("end_time", 0))})
            return chapters
        return []
    except Exception as e:
        logger.error(f"Chapter extraction failed: {e}")
        return []

def split_by_chapters(video_path, output_dir):
    chapters = extract_chapters(video_path)
    if not chapters:
        logger.warning("No chapters found")
        return []
    os.makedirs(output_dir, exist_ok=True)
    from src.services.trimming import clip_segment
    created = []
    for i, ch in enumerate(chapters):
        safe_name = "".join(c if c.isalnum() else "_" for c in ch["title"])
        output = os.path.join(output_dir, f"{i+1:02d}_{safe_name}.mp4")
        if clip_segment(video_path, output, ch["start"], ch["end"]):
            created.append(output)
    logger.info(f"Split into {len(created)} chapters")
    return created

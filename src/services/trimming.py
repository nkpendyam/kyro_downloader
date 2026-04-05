"""Video trimming and clipping service."""
from typing import Any

import os
import subprocess
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.ffmpeg import check_ffmpeg
logger = get_logger(__name__)

def trim_video(input_path: str | Path, output_path: str | Path, start_time: str | int | float | None = None, end_time: str | int | float | None = None, duration: str | int | float | None = None, fast: bool = True) -> bool:
    if not check_ffmpeg():
        logger.error("FFmpeg not available for trimming")
        return False
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        return False
    cmd = ["ffmpeg", "-y"]
    if start_time and fast: cmd.extend(["-ss", str(start_time)])
    cmd.extend(["-i", input_path])
    if start_time and not fast: cmd.extend(["-ss", str(start_time)])
    if end_time: cmd.extend(["-to", str(end_time)])
    if duration and not end_time: cmd.extend(["-t", str(duration)])
    if fast: cmd.extend(["-c", "copy"])
    else: cmd.extend(["-c:v", "libx264", "-c:a", "aac"])
    cmd.append(output_path)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logger.info(f"Video trimmed: {output_path}")
            return True
        else:
            logger.error(f"Trimming failed: {result.stderr[:500]}")
            return False
    except Exception as e:
        logger.error(f"Trimming error: {e}")
        return False

def clip_segment(input_path: str | Path, output_path: str | Path, start_seconds: str | int | float, end_seconds: str | int | float, fast: bool = True) -> bool:
    return trim_video(input_path, output_path, start_time=str(start_seconds), end_time=str(end_seconds), fast=fast)

def split_into_chapters(input_path: str | Path, output_dir: str | Path, chapters: list[dict[str, Any]], fast: bool = True) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    created = []
    for i, chapter in enumerate(chapters):
        name = chapter.get("name", f"chapter_{i+1}")
        safe_name = "".join(c if c.isalnum() else "_" for c in name)
        output = os.path.join(output_dir, f"{i+1:02d}_{safe_name}.mp4")
        if clip_segment(input_path, output, chapter["start"], chapter["end"], fast):
            created.append(output)
    logger.info(f"Split into {len(created)} clips")
    return created

def get_video_duration(filepath: str | Path) -> float | None:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath], capture_output=True, text=True, timeout=10)
        if result.returncode == 0: return float(result.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError, TimeoutError):
        pass
    return None

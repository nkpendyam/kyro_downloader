"""FFmpeg detection and validation."""

import shutil

from src.utils.logger import get_logger

logger = get_logger(__name__)


def check_ffmpeg() -> bool:
    path = shutil.which("ffmpeg")
    if path:
        logger.info(f"FFmpeg found at: {path}")
    else:
        logger.warning("FFmpeg not found in PATH")
    return path is not None


def check_ffprobe() -> bool:
    return shutil.which("ffprobe") is not None


def validate_ffmpeg(required: bool = True) -> bool:
    has_ffmpeg = check_ffmpeg()
    has_ffprobe = check_ffprobe()
    if not has_ffmpeg or not has_ffprobe:
        if required:
            raise RuntimeError(
                "FFmpeg is required but not found. Install: winget install ffmpeg (Windows) | brew install ffmpeg (macOS) | sudo apt install ffmpeg (Linux)"
            )
        else:
            logger.warning("FFmpeg not found. Audio extraction and merging disabled.")
            return False
    return True

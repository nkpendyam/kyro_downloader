"""Thumbnail download and embedding service."""
from pathlib import Path

import requests
from PIL import Image
from io import BytesIO
from src.utils.logger import get_logger
logger = get_logger(__name__)

def download_thumbnail(url: str, output_path: str | Path, filename: str = "thumbnail") -> Path | None:
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{filename}.jpg"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image.save(str(filepath), "JPEG", quality=95)
        logger.info(f"Thumbnail saved: {filepath}")
        return filepath
    except Exception as e:
        logger.warning(f"Thumbnail download failed: {e}")
        return None

def show_thumbnail_inline(url: str, max_width: int = 60) -> None:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image.show()
    except Exception as e:
        logger.warning(f"Thumbnail display failed: {e}")

def embed_thumbnail_in_video(video_path: str | Path, thumbnail_path: str | Path) -> bool:
    import subprocess
    if not Path(thumbnail_path).exists(): return False
    temp_path = Path(video_path).with_suffix(".temp.mp4")
    cmd = ["ffmpeg", "-y", "-i", video_path, "-i", thumbnail_path, "-map", "0", "-map", "1", "-c", "copy", "-disposition:v:1", "attached_pic", str(temp_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            temp_path.replace(video_path)
            logger.info(f"Thumbnail embedded in: {video_path}")
            return True
        else:
            if temp_path.exists(): temp_path.unlink()
            return False
    except Exception:
        if temp_path.exists(): temp_path.unlink()
        return False

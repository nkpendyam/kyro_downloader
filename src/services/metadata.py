"""Metadata embedding service."""
from typing import Any

import subprocess
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.ffmpeg import check_ffmpeg
logger = get_logger(__name__)

def embed_metadata(filepath: str | Path, title: str, artist: str = "", album: str = "", description: str = "", thumbnail_path: str | Path | None = None, upload_date: str = "", comment: str = "") -> bool:
    if not check_ffmpeg():
        logger.warning("FFmpeg not available, skipping metadata embedding")
        return False
    path = Path(filepath)
    if not path.exists():
        logger.error(f"File not found: {filepath}")
        return False
    temp_path = path.with_suffix(f".temp{path.suffix}")
    cmd = ["ffmpeg", "-y", "-i", str(path)]
    if thumbnail_path and Path(thumbnail_path).exists():
        cmd.extend(["-i", thumbnail_path, "-map", "0", "-map", "1"])
    else:
        cmd.extend(["-map", "0"])
    metadata_args = ["-metadata", f"title={title}", "-metadata", f"comment={comment or description[:200]}"]
    if artist: metadata_args.extend(["-metadata", f"artist={artist}"])
    if album: metadata_args.extend(["-metadata", f"album={album}"])
    if upload_date: metadata_args.extend(["-metadata", f"date={upload_date}"])
    cmd.extend(metadata_args)
    if path.suffix.lower() in (".mp4", ".m4a"): cmd.extend(["-c", "copy", "-movflags", "+faststart"])
    elif path.suffix.lower() == ".mp3": cmd.extend(["-c", "copy", "-id3v2_version", "3"])
    else: cmd.extend(["-c", "copy"])
    cmd.append(str(temp_path))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            temp_path.replace(path)
            logger.info(f"Metadata embedded: {title}")
            return True
        else:
            logger.warning(f"FFmpeg metadata failed: {result.stderr[:200]}")
            if temp_path.exists(): temp_path.unlink()
            return False
    except Exception as e:
        logger.error(f"Metadata embedding error: {e}")
        if temp_path.exists(): temp_path.unlink()
        return False

def extract_metadata_from_info(info: dict[str, Any]) -> dict[str, str]:
    return {"title": info.get("title", ""), "artist": info.get("uploader", info.get("artist", "")), "album": info.get("album", info.get("playlist_title", "")), "description": info.get("description", ""), "upload_date": info.get("upload_date", ""), "comment": info.get("description", "")[:500] if info.get("description") else ""}

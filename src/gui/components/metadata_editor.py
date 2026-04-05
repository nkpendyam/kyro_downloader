"""Metadata editor component."""
import subprocess
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.ffmpeg import check_ffmpeg
logger = get_logger(__name__)

class MetadataEditor:
    def edit_metadata(self, filepath, title=None, artist=None, album=None, comment=None, date=None):
        if not check_ffmpeg():
            logger.error("FFmpeg not available")
            return False
        path = Path(filepath)
        if not path.exists(): return False
        temp_path = path.with_suffix(f".temp{path.suffix}")
        cmd = ["ffmpeg", "-y", "-i", str(path), "-map", "0"]
        if title: cmd.extend(["-metadata", f"title={title}"])
        if artist: cmd.extend(["-metadata", f"artist={artist}"])
        if album: cmd.extend(["-metadata", f"album={album}"])
        if comment: cmd.extend(["-metadata", f"comment={comment}"])
        if date: cmd.extend(["-metadata", f"date={date}"])
        if path.suffix.lower() in (".mp4", ".m4a"): cmd.extend(["-c", "copy", "-movflags", "+faststart"])
        elif path.suffix.lower() == ".mp3": cmd.extend(["-c", "copy", "-id3v2_version", "3"])
        else: cmd.extend(["-c", "copy"])
        cmd.append(str(temp_path))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                temp_path.replace(path)
                logger.info(f"Metadata edited: {filepath}")
                return True
            return False
        except (OSError, subprocess.SubprocessError, TimeoutError):
            return False

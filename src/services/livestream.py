"""Live stream download service."""

import subprocess
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.ffmpeg import check_ffmpeg
logger = get_logger(__name__)

def download_livestream(url: str, output_path: str | Path, from_start: bool = False) -> str | None:
    if not check_ffmpeg():
        logger.error("FFmpeg not available for livestream")
        return None
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    import yt_dlp
    ydl_opts = {
        "outtmpl": str(output_path / "%(title)s.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
        "live_from_start": from_start,
        "wait_for_video": {"max_retries": 30},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logger.info(f"Livestream download complete: {url}")
        return str(output_path)
    except Exception as e:
        logger.error(f"Livestream download failed: {e}")
        return None

def record_livestream_ffmpeg(url: str, output_path: str | Path, timeout: int = 3600) -> str | None:
    """Record livestream using yt-dlp piped to ffmpeg.

    Uses subprocess with list args (no shell=True) to prevent injection.
    """
    if not check_ffmpeg():
        logger.error("FFmpeg not available")
        return None
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ytdlp_cmd = ["yt-dlp", "-o", "-", "-f", "best", "--no-playlist", url]
    ffmpeg_cmd = ["ffmpeg", "-y", "-i", "pipe:0", "-c", "copy", str(output_path)]
    try:
        ytdlp_proc = subprocess.Popen(ytdlp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ffmpeg_proc = subprocess.run(
            ffmpeg_cmd,
            stdin=ytdlp_proc.stdout,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        ytdlp_proc.wait()
        if ffmpeg_proc.returncode == 0:
            logger.info(f"FFmpeg livestream recording complete: {output_path}")
            return str(output_path)
        return None
    except subprocess.TimeoutExpired:
        ytdlp_proc.kill()
        logger.info(f"FFmpeg livestream recording timed out after {timeout}s")
        return str(output_path) if output_path.exists() else None
    except Exception as e:
        logger.error(f"FFmpeg livestream recording failed: {e}")
        return None

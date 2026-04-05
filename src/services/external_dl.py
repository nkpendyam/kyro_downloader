"""External downloader support (aria2c, etc.)."""
import subprocess
import shutil
import yt_dlp
from src.utils.logger import get_logger
logger = get_logger(__name__)

def check_aria2c() -> bool:
    return shutil.which("aria2c") is not None

def download_with_aria2c(url: str, output_path: str, max_connections: int = 16, rate_limit: str | None = None) -> bool | None:
    if not check_aria2c():
        logger.error("aria2c not found")
        return None
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        direct_url = info.get("url")
        if not direct_url:
            logger.error("Could not extract direct URL for aria2c")
            return None
    except Exception as e:
        logger.error(f"Failed to extract direct URL: {e}")
        return None
    cmd = ["aria2c", "-x", str(max_connections), "-s", str(max_connections), "-k", "1M", "--file-allocation=none", "--continue=true", "-d", output_path, direct_url]
    if rate_limit: cmd.extend(["--max-download-limit", rate_limit])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            logger.info(f"aria2c download complete: {url}")
            return True
        else:
            logger.error(f"aria2c download failed: {result.stderr[:200]}")
            return False
    except Exception as e:
        logger.error(f"aria2c download error: {e}")
        return False

def get_external_downloader() -> str | None:
    if check_aria2c(): return "aria2c"
    return None

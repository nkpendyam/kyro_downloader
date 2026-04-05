"""Format conversion service for downloaded media."""
import subprocess
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.ffmpeg import check_ffmpeg
logger = get_logger(__name__)

SUPPORTED_FORMATS = {
    "video": ["mp4", "mkv", "webm", "avi", "mov", "flv", "wmv"],
    "audio": ["mp3", "flac", "aac", "ogg", "wav", "opus", "m4a"],
}

def convert_file(input_path, output_format, quality=None, remove_original=False):
    if not check_ffmpeg():
        logger.error("FFmpeg not available for conversion")
        return None
    input_path = Path(input_path)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return None
    output_path = input_path.with_suffix(f".{output_format}")
    cmd = ["ffmpeg", "-y", "-i", str(input_path)]
    if output_format == "mp3":
        cmd.extend(["-q:a", "0" if quality == "best" else "2"])
    elif output_format == "flac":
        cmd.extend(["-compression_level", "12" if quality == "best" else "5"])
    elif output_format in ("mp4", "mkv"):
        cmd.extend(["-c:v", "copy", "-c:a", "copy"])
    elif output_format == "webm":
        cmd.extend(["-c:v", "libvpx-vp9", "-c:a", "libopus"])
    cmd.append(str(output_path))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            if remove_original: input_path.unlink()
            logger.info(f"Converted: {input_path.name} -> {output_path.name}")
            return str(output_path)
        else:
            logger.error(f"Conversion failed: {result.stderr[:200]}")
            return None
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return None

def batch_convert(files, output_format, quality=None, remove_original=False):
    results = []
    for f in files:
        result = convert_file(f, output_format, quality, remove_original)
        results.append({"input": f, "output": result, "success": result is not None})
    return results

"""Video compression service."""
import subprocess
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.ffmpeg import check_ffmpeg
logger = get_logger(__name__)

def compress_video(input_path, output_path=None, quality="medium", preset="medium", remove_original=False):
    if not check_ffmpeg():
        logger.error("FFmpeg not available for compression")
        return None
    input_path = Path(input_path)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return None
    if not output_path:
        output_path = input_path.with_name(f"{input_path.stem}_compressed{input_path.suffix}")
    else:
        output_path = Path(output_path)
    crf_map = {"low": 28, "medium": 23, "high": 18, "best": 15}
    crf = crf_map.get(quality, 23)
    cmd = ["ffmpeg", "-y", "-i", str(input_path), "-c:v", "libx264", "-crf", str(crf), "-preset", preset, "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            original_size = input_path.stat().st_size
            compressed_size = output_path.stat().st_size
            reduction = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0 if original_size > 0 else 0
            if remove_original: input_path.unlink()
            logger.info(f"Compressed: {input_path.name} ({reduction:.1f}% smaller)")
            return {"output": str(output_path), "original_size": original_size, "compressed_size": compressed_size, "reduction_percent": reduction}
        else:
            logger.error(f"Compression failed: {result.stderr[:200]}")
            return None
    except Exception as e:
        logger.error(f"Compression error: {e}")
        return None

def batch_compress(files, quality="medium", preset="medium", remove_original=False):
    results = []
    for f in files:
        result = compress_video(f, quality=quality, preset=preset, remove_original=remove_original)
        results.append({"input": f, "output": result, "success": result is not None})
    return results

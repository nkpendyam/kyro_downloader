"""Subtitle download and embedding service."""
from pathlib import Path
from src.utils.logger import get_logger
logger = get_logger(__name__)

def build_subtitle_opts(languages=None, embed=False, auto_generated=True, subtitle_format="srt"):
    opts = {"writesubtitles": True, "writeautomaticsub": auto_generated, "subtitleslangs": languages or ["en"], "subtitlesformat": subtitle_format}
    if embed:
        opts["postprocessors"] = opts.get("postprocessors", [])
        opts["postprocessors"].append({"key": "FFmpegEmbedSubtitle"})
    return opts

def get_available_subtitles(info):
    if not info:
        return []
    subtitles = []
    for lang, sub_list in info.get("subtitles", {}).items():
        subtitles.append({"language": lang, "auto_generated": False, "ext": sub_list[0].get("ext", "unknown") if sub_list else "unknown"})
    for lang, sub_list in info.get("automatic_captions", {}).items():
        subtitles.append({"language": lang, "auto_generated": True, "ext": sub_list[0].get("ext", "unknown") if sub_list else "unknown"})
    return subtitles

def download_subtitles_separately(info, output_path, languages=None, subtitle_format="srt"):
    from yt_dlp import YoutubeDL
    languages = languages or ["en"]
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    title = info.get("title", "video")
    safe_title = "".join(c if c.isalnum() else "_" for c in title)
    ydl_opts = {"skip_download": True, "writesubtitles": True, "writeautomaticsub": True, "subtitleslangs": languages, "subtitlesformat": subtitle_format, "outtmpl": str(output_dir / f"{safe_title}.%(ext)s"), "quiet": True}
    webpage_url = info.get("webpage_url")
    if not webpage_url:
        logger.warning("No webpage_url in info, cannot download subtitles")
        return []
    downloaded = []
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([webpage_url])
        for ext in (subtitle_format, "vtt"):
            for f in output_dir.glob(f"*.{ext}"):
                downloaded.append(f)
                logger.info(f"Subtitle downloaded: {f.name}")
    except Exception as e:
        logger.warning(f"Subtitle download failed: {e}")
    return downloaded

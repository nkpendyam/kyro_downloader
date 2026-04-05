"""Core yt-dlp wrapper with error handling and post-processing."""
import os
import platform
import time
import yt_dlp
from src.core.progress import create_progress_hook
from src.core.retry import retry
from src.utils.logger import get_logger
from src.utils.validation import validate_url

logger = get_logger(__name__)

class DownloadError(Exception):
    def __init__(self, message, url="", error_code=None):
        super().__init__(message)
        self.url = url
        self.error_code = error_code

class VideoInfo:
    def __init__(self, info):
        self.raw = info
        self.title = info.get("title", "Unknown")
        self.duration = info.get("duration", 0)
        self.thumbnail = info.get("thumbnail", "")
        self.description = info.get("description", "")
        self.uploader = info.get("uploader", "")
        self.upload_date = info.get("upload_date", "")
        self.view_count = info.get("view_count", 0)
        self.formats = info.get("formats") or []
        self.is_playlist = info.get("_type") == "playlist"
        self.entries = info.get("entries") or []
        self.available = analyze_available_formats(self.formats)

    @property
    def duration_str(self):
        if not self.duration:
            return "Unknown"
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def view_count_str(self):
        if not self.view_count:
            return "Unknown"
        if self.view_count >= 1_000_000:
            return f"{self.view_count / 1_000_000:.1f}M"
        if self.view_count >= 1_000:
            return f"{self.view_count / 1_000:.1f}K"
        return str(self.view_count)

def analyze_available_formats(formats):
    """Analyze all available formats and return smart labels."""
    heights = set()
    has_hdr = False
    has_dolby = False
    audio_bitrates = set()
    audio_codecs = set()
    audio_streams = []

    for f in formats:
        h = f.get("height", 0)
        if h:
            heights.add(h)

        acodec = f.get("acodec", "")

        # HDR detection
        if f.get("dynamic_range") in ("HDR10", "HLG", "DV", "HDR"):
            has_hdr = True

        # Dolby detection
        if "ec-3" in acodec or "ac-3" in acodec:
            has_dolby = True

        # Audio format detection
        if acodec and acodec != "none":
            if "mp3" in acodec:
                audio_codecs.add("mp3")
            if "aac" in acodec or "mp4a" in acodec:
                audio_codecs.add("aac")
            if "opus" in acodec:
                audio_codecs.add("opus")
            if "flac" in acodec:
                audio_codecs.add("flac")
            if "vorbis" in acodec:
                audio_codecs.add("vorbis")
            if "wav" in acodec:
                audio_codecs.add("wav")

        # Audio bitrate detection
        abr = f.get("abr", 0)
        if abr and acodec != "none":
            audio_bitrates.add(int(abr))

        if acodec and acodec != "none":
            codec_label = "unknown"
            selector_codec = ""
            if "opus" in acodec:
                codec_label = "opus"
                selector_codec = "opus"
            elif "mp4a" in acodec or "aac" in acodec:
                codec_label = "aac"
                selector_codec = "mp4a"
            elif "mp3" in acodec:
                codec_label = "mp3"
                selector_codec = "mp3"
            elif "flac" in acodec:
                codec_label = "flac"
                selector_codec = "flac"
            elif "vorbis" in acodec:
                codec_label = "vorbis"
                selector_codec = "vorbis"
            elif "ac-3" in acodec:
                codec_label = "ac3"
                selector_codec = "ac-3"
            elif "ec-3" in acodec:
                codec_label = "eac3"
                selector_codec = "ec-3"
            elif "alac" in acodec:
                codec_label = "alac"
                selector_codec = "alac"
            elif "wav" in acodec or "pcm" in acodec:
                codec_label = "wav"
                selector_codec = "pcm"

            audio_streams.append(
                {
                    "format_id": f.get("format_id"),
                    "codec": codec_label,
                    "selector_codec": selector_codec,
                    "abr": int(abr) if abr else 0,
                    "ext": f.get("ext", ""),
                }
            )

    deduped_streams = {}
    for stream in audio_streams:
        key = (
            stream.get("codec"),
            stream.get("abr", 0),
            stream.get("selector_codec"),
        )
        existing = deduped_streams.get(key)
        if existing is None:
            deduped_streams[key] = stream
        elif stream.get("format_id") and not existing.get("format_id"):
            deduped_streams[key] = stream

    sorted_streams = sorted(
        deduped_streams.values(), key=lambda s: s.get("abr", 0), reverse=True
    )

    return {
        "available_qualities": sorted(heights, reverse=True),
        "has_hdr": has_hdr,
        "has_dolby": has_dolby,
        "audio_bitrates": sorted(audio_bitrates, reverse=True),
        "audio_codecs": sorted(audio_codecs),
        "audio_streams": sorted_streams,
    }

def build_quality_labels(analysis):
    """Build user-friendly quality labels based on what's actually available."""
    labels = []
    height_map = {8000: "8K", 4320: "8K", 2160: "4K", 1080: "1080p", 720: "720p", 480: "480p", 360: "360p", 240: "240p", 144: "144p"}
    for h in analysis["available_qualities"]:
        label = height_map.get(h, f"{h}p")
        if h >= 1080 and analysis["has_hdr"]:
            label += " HDR"
        if analysis["has_dolby"]:
            label += " + Dolby"
        labels.append(label)
    if not labels:
        labels.append("Best Available")
    return labels


def build_smart_audio_options(analysis):
    """Build dynamic audio options from source formats plus transcode presets."""
    options = [
        {
            "label": "Smart Best Available (Auto)",
            "audio_format": "mp3",
            "audio_quality": "192",
            "selector": "bestaudio/best",
        }
    ]

    streams = analysis.get("audio_streams", []) if analysis else []
    preferred_output_map = {
        "aac": "aac",
        "mp3": "mp3",
        "opus": "opus",
        "flac": "flac",
        "vorbis": "ogg",
        "alac": "alac",
        "wav": "wav",
        "ac3": "aac",
        "eac3": "aac",
        "unknown": "mp3",
    }

    for stream in streams:
        codec = stream.get("codec", "unknown")
        selector_codec = stream.get("selector_codec", "")
        abr = stream.get("abr", 0)
        format_id = stream.get("format_id")
        abr_label = f"{abr} kbps" if abr else "variable bitrate"
        source_label = f"Source {codec.upper()} {abr_label}"
        if format_id:
            source_label += f" ({format_id})"

        selector = "bestaudio/best"
        if selector_codec:
            selector = f"bestaudio[acodec*={selector_codec}]/bestaudio/best"

        options.append(
            {
                "label": source_label,
                "audio_format": preferred_output_map.get(codec, "mp3"),
                "audio_quality": str(abr) if abr else "192",
                "selector": selector,
            }
        )

    for preset_label, preset in AUDIO_QUALITY_PRESETS.items():
        options.append(
            {
                "label": f"Preset {preset_label}",
                "audio_format": preset.get("format", "mp3"),
                "audio_quality": preset.get("abr", "192"),
                "selector": "bestaudio/best",
            }
        )

    return options

AUDIO_QUALITY_PRESETS = {
    "64 kbps (Voice)": {"abr": "64", "format": "mp3", "description": "Voice only, smallest size"},
    "96 kbps (Low)": {"abr": "96", "format": "mp3", "description": "Podcasts, speech"},
    "128 kbps (Standard)": {"abr": "128", "format": "mp3", "description": "Casual listening"},
    "160 kbps (Good)": {"abr": "160", "format": "mp3", "description": "Good quality music"},
    "192 kbps (High)": {"abr": "192", "format": "mp3", "description": "High quality music"},
    "256 kbps (Very High)": {"abr": "256", "format": "mp3", "description": "Audiophile casual"},
    "320 kbps (Best MP3)": {"abr": "320", "format": "mp3", "description": "Maximum MP3 quality"},
    "Opus (Best Ratio)": {"abr": "160", "format": "opus", "description": "Best quality/size ratio"},
    "Lossless (FLAC)": {"abr": "0", "format": "flac", "description": "Perfect quality, large files"},
    "Lossless (ALAC)": {"abr": "0", "format": "alac", "description": "Apple lossless"},
    "Uncompressed (WAV)": {"abr": "0", "format": "wav", "description": "Raw PCM, huge files"},
}

def get_video_info(url, cookies_file=None, proxy=None):
    if not validate_url(url):
        raise DownloadError(f"Invalid URL: {url}", url=url)
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": False}
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file
    if proxy:
        ydl_opts["proxy"] = proxy
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return VideoInfo(info)
    except Exception as e:
        if "DownloadError" in type(e).__name__:
            raise DownloadError(str(e), url=url) from e
        raise DownloadError(f"Failed to extract info: {e}", url=url) from e

def list_video_formats(formats):
    if not formats:
        return []
    indexed = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") == "none"]
    if not indexed:
        indexed = [f for f in formats if f.get("vcodec") != "none"]
    indexed.sort(key=lambda f: f.get("height") or 0, reverse=True)
    return indexed

def list_audio_formats(formats):
    if not formats:
        return []
    indexed = [f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"]
    if not indexed:
        indexed = [f for f in formats if f.get("acodec") != "none"]
    indexed.sort(key=lambda f: f.get("abr") or 0, reverse=True)
    return indexed

def build_ydl_opts(output_path, format_id=None, only_audio=False, audio_format="mp3", audio_quality="192", audio_selector=None, embed_thumbnail=True, embed_metadata=True, subtitles=None, sponsorblock=None, rate_limit=None, proxy=None, cookies_file=None, progress_hook=None, playlist=False, playlist_config=None, prefer_format="mp4", fragment_retries=10, concurrent_fragments=4, hdr=False, dolby=False, output_template=None):
    os.makedirs(output_path, exist_ok=True)
    postprocessors = []
    if output_template:
        outtmpl = os.path.join(output_path, output_template)
    elif only_audio:
        outtmpl = os.path.join(output_path, "%(title)s.%(ext)s")
    elif playlist:
        outtmpl = os.path.join(output_path, "%(playlist_title)s", "%(title)s.%(ext)s")
    else:
        outtmpl = os.path.join(output_path, "%(title)s.%(ext)s")
    if only_audio:
        postprocessors.append({"key": "FFmpegExtractAudio", "preferredcodec": audio_format, "preferredquality": audio_quality})
    if embed_thumbnail:
        postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})
    if embed_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
    ydl_opts_subs = {}
    if subtitles and subtitles.get("enabled"):
        ydl_opts_subs = {"writesubtitles": True, "writeautomaticsub": subtitles.get("auto_generated", True), "subtitleslangs": subtitles.get("languages", ["en"]), "subtitlesformat": subtitles.get("format", "srt")}
        if subtitles.get("embed"):
            postprocessors.append({"key": "FFmpegEmbedSubtitle"})
    ydl_opts = {
        "outtmpl": outtmpl,
        "progress_hooks": [progress_hook] if progress_hook else [],
        "postprocessors": postprocessors,
        "postprocessor_args": {"ffmpeg": ["-y"]},
        "fragment_retries": fragment_retries,
        "concurrent_fragment_downloads": concurrent_fragments,
        "retries": 10,
        "file_access_retries": 10,
        "extractor_retries": 3,
        "nooverwrites": False,
        "continuedl": True,
        "nopart": True,
        "windowsfilenames": True,
        "retry_sleep_functions": {"file_access": lambda n: min(2 ** n, 30), "http": lambda n: min(2 ** n, 30), "fragment": lambda n: min(2 ** n, 30)},
    }
    if only_audio:
        ydl_opts["format"] = audio_selector or "bestaudio/best"
        ydl_opts["postprocessor_args"]["ffmpeg"].extend(["-b:a", f"{audio_quality}k"])
        ydl_opts["writethumbnail"] = True
    else:
        if format_id:
            ydl_opts["format"] = f"{format_id}+bestaudio/best"
        elif hdr:
            ydl_opts["format"] = "bestvideo[vcodec^=av01][height>=1080]+bestvideo[vcodec^=vp9][height>=1080]+bestaudio/best[ext=m4a]/best"
        elif dolby:
            ydl_opts["format"] = "bestvideo+bestaudio[acodec^=ec-3]/bestvideo+bestaudio[acodec^=ac-3]/bestvideo+bestaudio/best"
        else:
            ydl_opts["format"] = f"bestvideo[ext={prefer_format}]+bestaudio/best[ext=m4a]/best"
        ydl_opts["merge_output_format"] = prefer_format
    if rate_limit:
        ydl_opts["ratelimit"] = rate_limit
    if proxy:
        ydl_opts["proxy"] = proxy
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file
    if sponsorblock and sponsorblock.get("enabled"):
        cats = ",".join(sponsorblock.get("categories", ["sponsor"]))
        ydl_opts["sponsorblock_mark"] = cats
        ydl_opts["sponsorblock_remove"] = cats
    ydl_opts.update(ydl_opts_subs)
    if playlist and playlist_config:
        if playlist_config.get("sleep_interval"):
            ydl_opts["sleep_interval"] = playlist_config["sleep_interval"]
        if playlist_config.get("max_downloads"):
            ydl_opts["playlistend"] = playlist_config["max_downloads"]
        if playlist_config.get("playlist_reverse"):
            ydl_opts["playlist_reverse"] = True
        if playlist_config.get("playlist_random"):
            ydl_opts["playlist_random"] = True
        if playlist_config.get("playlist_start"):
            ydl_opts["playliststart"] = playlist_config["playlist_start"]
    return ydl_opts

@retry(max_attempts=3, base_delay=5.0, backoff="exponential")
def download_single(url, output_path, format_id=None, only_audio=False, config=None, progress_tracker=None, task_id=None, progress_hook=None):
    cfg = config or {}
    hook = progress_hook
    if hook is None and progress_tracker and task_id:
        hook = create_progress_hook(progress_tracker, task_id)
    ydl_opts = build_ydl_opts(
        output_path=output_path, format_id=format_id, only_audio=only_audio,
        audio_format=cfg.get("audio_format", "mp3"), audio_quality=cfg.get("audio_quality", "192"), audio_selector=cfg.get("audio_selector"),
        embed_thumbnail=cfg.get("embed_thumbnail", True), embed_metadata=cfg.get("embed_metadata", True),
        subtitles=cfg.get("subtitles"), sponsorblock=cfg.get("sponsorblock"),
        rate_limit=cfg.get("rate_limit"), proxy=cfg.get("proxy"), cookies_file=cfg.get("cookies_file"),
        progress_hook=hook, prefer_format=cfg.get("prefer_format", "mp4"),
        fragment_retries=cfg.get("fragment_retries", 10), concurrent_fragments=cfg.get("concurrent_fragments", 4),
        hdr=cfg.get("hdr", False), dolby=cfg.get("dolby", False), output_template=cfg.get("output_template"),
    )
    try:
        if platform.system() == "Windows":
            ydl_opts["sleep_interval_subtitles"] = 2
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])
        if platform.system() == "Windows":
            time.sleep(0.5)
        if result != 0:
            raise DownloadError(f"yt-dlp returned error code: {result}", url=url)
        logger.info(f"Download complete: {url}")
        return output_path
    except FileNotFoundError as e:
        if "temp." in str(e) and os.path.exists(output_path):
            logger.info(f"Download complete (postprocessor rename skipped): {url}")
            return output_path
        raise DownloadError(f"Download failed: {e}", url=url) from e
    except Exception as e:
        if "DownloadError" in type(e).__name__:
            raise DownloadError(str(e), url=url) from e
        if "FileNotFoundError" in type(e).__name__ and os.path.exists(output_path):
            logger.info(f"Download complete (postprocessor rename skipped): {url}")
            return output_path
        raise DownloadError(f"Download failed: {e}", url=url) from e

def download_playlist(url, output_path, config=None, progress_tracker=None, format_id=None, only_audio=False):
    cfg = config or {}
    playlist_cfg = cfg.get("playlist", {})
    ydl_opts = build_ydl_opts(
        output_path=output_path, format_id=format_id, only_audio=only_audio,
        audio_format=cfg.get("audio_format", "mp3"), audio_quality=cfg.get("audio_quality", "192"), audio_selector=cfg.get("audio_selector"),
        embed_thumbnail=cfg.get("embed_thumbnail", True), embed_metadata=cfg.get("embed_metadata", True),
        subtitles=cfg.get("subtitles"), sponsorblock=cfg.get("sponsorblock"),
        rate_limit=cfg.get("rate_limit"), proxy=cfg.get("proxy"), cookies_file=cfg.get("cookies_file"),
        playlist=True, playlist_config=playlist_cfg, prefer_format=cfg.get("prefer_format", "mp4"),
        hdr=cfg.get("hdr", False), dolby=cfg.get("dolby", False), output_template=cfg.get("output_template"),
    )
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logger.info(f"Playlist download complete: {url}")
        return [output_path]
    except Exception as e:
        if "DownloadError" in type(e).__name__:
            raise DownloadError(str(e), url=url) from e
        raise DownloadError(f"Playlist download failed: {e}", url=url) from e

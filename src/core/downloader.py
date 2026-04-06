"""Core yt-dlp wrapper with error handling and post-processing."""

import os
import platform
import time
from typing import Any, Callable, cast

import yt_dlp
from src.core.progress import create_progress_hook  # pyright: ignore[reportUnknownVariableType]
from src.core.retry import retry  # pyright: ignore[reportUnknownVariableType]
from src.utils.logger import get_logger  # pyright: ignore[reportUnknownVariableType]
from src.utils.validation import validate_url  # pyright: ignore[reportUnknownVariableType]

FormatDict = dict[str, Any]
ConfigDict = dict[str, Any]
ProgressHook = Callable[[dict[str, Any]], None]


def _retry_sleep(n: int) -> int:
    return min(2**n, 30)


logger: Any = get_logger(__name__)


class DownloadError(Exception):
    def __init__(self, message: str, url: str = "", error_code: int | None = None) -> None:
        super().__init__(message)
        self.url = url
        self.error_code = error_code


class VideoInfo:
    def __init__(self, info: dict[str, Any]) -> None:
        self.raw = info
        self.title: str = str(info.get("title", "Unknown"))
        self.duration: int | float = info.get("duration", 0)
        self.thumbnail: str = str(info.get("thumbnail", ""))
        self.description: str = str(info.get("description", ""))
        self.uploader: str = str(info.get("uploader", ""))
        self.upload_date: str = str(info.get("upload_date", ""))
        self.view_count: int | float = info.get("view_count", 0)
        self.formats: list[FormatDict] = list(info.get("formats") or [])
        self.is_playlist: bool = info.get("_type") == "playlist"
        self.entries: list[Any] = list(info.get("entries") or [])
        self.available = analyze_available_formats(self.formats)

    @property
    def duration_str(self) -> str:
        if not self.duration:
            return "Unknown"
        try:
            total_seconds = int(float(self.duration))
        except (TypeError, ValueError):
            return "Unknown"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def view_count_str(self) -> str:
        if not self.view_count:
            return "Unknown"
        if self.view_count >= 1_000_000:
            return f"{self.view_count / 1_000_000:.1f}M"
        if self.view_count >= 1_000:
            return f"{self.view_count / 1_000:.1f}K"
        return str(int(float(self.view_count)))


def analyze_available_formats(formats: list[FormatDict]) -> dict[str, Any]:
    """Analyze all available formats and return smart labels."""
    heights: set[int] = set()
    has_hdr = False
    has_dolby = False
    audio_bitrates: set[int] = set()
    audio_codecs: set[str] = set()
    audio_streams: list[dict[str, Any]] = []

    for f in formats:
        h = int(f.get("height", 0) or 0)
        if h:
            heights.add(h)

        acodec = str(f.get("acodec", ""))

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
        abr = int(float(f.get("abr", 0) or 0))
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

    deduped_streams: dict[tuple[str, int, str], dict[str, Any]] = {}
    for stream in audio_streams:
        key = (
            str(stream.get("codec") or "unknown"),
            int(stream.get("abr", 0) or 0),
            str(stream.get("selector_codec") or ""),
        )
        existing = deduped_streams.get(key)
        if existing is None:
            deduped_streams[key] = stream
        elif stream.get("format_id") and not existing.get("format_id"):
            deduped_streams[key] = stream

    sorted_streams = sorted(deduped_streams.values(), key=lambda s: s.get("abr", 0), reverse=True)

    return {
        "available_qualities": sorted(heights, reverse=True),
        "has_hdr": has_hdr,
        "has_dolby": has_dolby,
        "audio_bitrates": sorted(audio_bitrates, reverse=True),
        "audio_codecs": sorted(audio_codecs),
        "audio_streams": sorted_streams,
    }


def build_quality_labels(analysis: dict[str, Any]) -> list[str]:
    """Build user-friendly quality labels based on what's actually available."""
    labels: list[str] = []
    height_map = {
        8000: "8K",
        4320: "8K",
        2160: "4K",
        1080: "1080p",
        720: "720p",
        480: "480p",
        360: "360p",
        240: "240p",
        144: "144p",
    }
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


def build_smart_audio_options(analysis: dict[str, Any] | None) -> list[dict[str, str]]:
    """Build dynamic audio options from source formats plus transcode presets."""
    options = [
        {
            "label": "Smart Best Available (Auto)",
            "audio_format": "mp3",
            "audio_quality": "192",
            "selector": "bestaudio/best",
        }
    ]

    streams: list[dict[str, Any]] = analysis.get("audio_streams", []) if analysis else []
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


def get_video_info(
    url: str, cookies_file: str | None = None, cookies_from_browser: str | None = None, proxy: str | None = None
) -> VideoInfo:
    if not validate_url(url):
        raise DownloadError(f"Invalid URL: {url}", url=url)
    ydl_opts: dict[str, Any] = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": False}
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file
    elif cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)
    if proxy:
        ydl_opts["proxy"] = proxy
    try:
        with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
            info = ydl.extract_info(url, download=False)
            return VideoInfo(cast(dict[str, Any], info))
    except Exception as e:
        if "DownloadError" in type(e).__name__:
            raise DownloadError(str(e), url=url) from e
        raise DownloadError(f"Failed to extract info: {e}", url=url) from e


def list_video_formats(formats: list[FormatDict]) -> list[FormatDict]:
    if not formats:
        return []
    indexed = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") == "none"]
    if not indexed:
        indexed = [f for f in formats if f.get("vcodec") != "none"]
    indexed.sort(key=lambda f: f.get("height") or 0, reverse=True)
    return indexed


def list_audio_formats(formats: list[FormatDict]) -> list[FormatDict]:
    if not formats:
        return []
    indexed = [f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"]
    if not indexed:
        indexed = [f for f in formats if f.get("acodec") != "none"]
    indexed.sort(key=lambda f: f.get("abr") or 0, reverse=True)
    return indexed


def build_ydl_opts(
    output_path: str,
    format_id: str | None = None,
    only_audio: bool = False,
    audio_format: str = "mp3",
    audio_quality: str = "192",
    audio_selector: str | None = None,
    embed_thumbnail: bool = True,
    embed_metadata: bool = True,
    subtitles: dict[str, Any] | None = None,
    sponsorblock: dict[str, Any] | None = None,
    rate_limit: str | None = None,
    proxy: str | None = None,
    cookies_file: str | None = None,
    cookies_from_browser: str | None = None,
    progress_hook: ProgressHook | None = None,
    playlist: bool = False,
    playlist_config: dict[str, Any] | None = None,
    prefer_format: str = "mp4",
    fragment_retries: int = 10,
    concurrent_fragments: int = 4,
    hdr: bool = False,
    dolby: bool = False,
    output_template: str | None = None,
) -> dict[str, Any]:
    os.makedirs(output_path, exist_ok=True)
    postprocessors: list[dict[str, Any]] = []
    thumbnail_supported = not (only_audio and str(audio_format).lower() == "opus")
    if output_template:
        outtmpl = os.path.join(output_path, output_template)
    elif only_audio:
        outtmpl = os.path.join(output_path, "%(title)s.%(ext)s")
    elif playlist:
        outtmpl = os.path.join(output_path, "%(playlist_title)s", "%(title)s.%(ext)s")
    else:
        outtmpl = os.path.join(output_path, "%(title)s.%(ext)s")
    if only_audio:
        postprocessors.append(
            {"key": "FFmpegExtractAudio", "preferredcodec": audio_format, "preferredquality": audio_quality}
        )
    if embed_thumbnail and thumbnail_supported:
        postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})
    if embed_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
    ydl_opts_subs: dict[str, Any] = {}
    if subtitles and subtitles.get("enabled"):
        ydl_opts_subs = {
            "writesubtitles": True,
            "writeautomaticsub": subtitles.get("auto_generated", True),
            "subtitleslangs": subtitles.get("languages", ["en"]),
            "subtitlesformat": subtitles.get("format", "srt"),
        }
        if subtitles.get("embed"):
            postprocessors.append({"key": "FFmpegEmbedSubtitle"})
    ydl_opts: dict[str, Any] = {
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
        "retry_sleep_functions": {"file_access": _retry_sleep, "http": _retry_sleep, "fragment": _retry_sleep},
    }
    if only_audio:
        ydl_opts["format"] = audio_selector or "bestaudio/best"
        post_args = cast(dict[str, list[str]], ydl_opts["postprocessor_args"])
        post_args["ffmpeg"].extend(["-b:a", f"{audio_quality}k"])
        ydl_opts["writethumbnail"] = bool(embed_thumbnail and thumbnail_supported)
    else:
        if format_id:
            ydl_opts["format"] = f"{format_id}+bestaudio/best"
        elif hdr:
            ydl_opts["format"] = (
                "bestvideo[vcodec^=av01][height>=1080]+bestvideo[vcodec^=vp9][height>=1080]+bestaudio/best[ext=m4a]/best"
            )
        elif dolby:
            ydl_opts["format"] = (
                "bestvideo+bestaudio[acodec^=ec-3]/bestvideo+bestaudio[acodec^=ac-3]/bestvideo+bestaudio/best"
            )
        else:
            ydl_opts["format"] = f"bestvideo[ext={prefer_format}]+bestaudio/best[ext=m4a]/best"
        ydl_opts["merge_output_format"] = prefer_format
    if rate_limit:
        ydl_opts["ratelimit"] = rate_limit
    if proxy:
        ydl_opts["proxy"] = proxy
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file
    elif cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)
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
def download_single(
    url: str,
    output_path: str,
    format_id: str | None = None,
    only_audio: bool = False,
    config: ConfigDict | None = None,
    progress_tracker: Any | None = None,
    task_id: str | None = None,
    progress_hook: ProgressHook | None = None,
) -> str:
    cfg: ConfigDict = config or {}
    hook = progress_hook
    if hook is None and progress_tracker and task_id:
        hook = cast(ProgressHook, create_progress_hook(progress_tracker, task_id))
    ydl_opts = build_ydl_opts(
        output_path=output_path,
        format_id=format_id,
        only_audio=only_audio,
        audio_format=cfg.get("audio_format", "mp3"),
        audio_quality=cfg.get("audio_quality", "192"),
        audio_selector=cfg.get("audio_selector"),
        embed_thumbnail=cfg.get("embed_thumbnail", True),
        embed_metadata=cfg.get("embed_metadata", True),
        subtitles=cfg.get("subtitles"),
        sponsorblock=cfg.get("sponsorblock"),
        rate_limit=cfg.get("rate_limit"),
        proxy=cfg.get("proxy"),
        cookies_file=cfg.get("cookies_file"),
        cookies_from_browser=cfg.get("cookies_from_browser"),
        progress_hook=hook,
        prefer_format=cfg.get("prefer_format", "mp4"),
        fragment_retries=cfg.get("fragment_retries", 10),
        concurrent_fragments=cfg.get("concurrent_fragments", 4),
        hdr=cfg.get("hdr", False),
        dolby=cfg.get("dolby", False),
        output_template=cfg.get("output_template"),
    )
    try:
        with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
            ydl.download([url])
        if platform.system() == "Windows":
            time.sleep(0.5)
        logger.info(f"Download complete: {url}")
        return output_path
    except FileNotFoundError as e:
        if "temp." in str(e) and os.path.exists(output_path):
            logger.info(f"Download complete (postprocessor rename skipped): {url}")
            return output_path
        raise DownloadError(f"Download failed: {e}", url=url) from e


@retry(max_attempts=3, base_delay=5.0, backoff="exponential")
def download_playlist(
    url: str,
    output_path: str,
    config: ConfigDict | None = None,
    progress_tracker: Any | None = None,
    format_id: str | None = None,
    only_audio: bool = False,
) -> list[str]:
    cfg: ConfigDict = config or {}
    playlist_cfg = cfg.get("playlist", {})
    ydl_opts = build_ydl_opts(
        output_path=output_path,
        format_id=format_id,
        only_audio=only_audio,
        audio_format=cfg.get("audio_format", "mp3"),
        audio_quality=cfg.get("audio_quality", "192"),
        audio_selector=cfg.get("audio_selector"),
        embed_thumbnail=cfg.get("embed_thumbnail", True),
        embed_metadata=cfg.get("embed_metadata", True),
        subtitles=cfg.get("subtitles"),
        sponsorblock=cfg.get("sponsorblock"),
        rate_limit=cfg.get("rate_limit"),
        proxy=cfg.get("proxy"),
        cookies_file=cfg.get("cookies_file"),
        cookies_from_browser=cfg.get("cookies_from_browser"),
        playlist=True,
        playlist_config=playlist_cfg,
        prefer_format=cfg.get("prefer_format", "mp4"),
        hdr=cfg.get("hdr", False),
        dolby=cfg.get("dolby", False),
        output_template=cfg.get("output_template"),
    )
    try:
        with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
            ydl.download([url])
        logger.info(f"Playlist download complete: {url}")
        return [output_path]
    except Exception as e:
        if "DownloadError" in type(e).__name__:
            raise DownloadError(str(e), url=url) from e
        raise DownloadError(f"Playlist download failed: {e}", url=url) from e

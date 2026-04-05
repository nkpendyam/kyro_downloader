"""Multi-platform URL detection and social media content type handling."""

from src.utils.validation import validate_platform
from src.utils.logger import get_logger

logger = get_logger(__name__)

PLATFORM_CONFIG = {
    "youtube.com": {
        "name": "YouTube",
        "icon": "\u25b6\ufe0f",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": True,
        "supports_shorts": True,
        "supports_stories": False,
        "supports_posts": False,
        "supports_live": True,
        "max_resolution": "8K",
        "supports_hdr": True,
        "supports_dolby": True,
        "audio_formats": ["mp3", "flac", "aac", "ogg", "wav", "opus"],
    },
    "youtu.be": {
        "name": "YouTube",
        "icon": "\u25b6\ufe0f",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": True,
        "supports_shorts": True,
        "supports_stories": False,
        "supports_posts": False,
        "supports_live": False,
        "max_resolution": "8K",
        "supports_hdr": True,
        "supports_dolby": True,
        "audio_formats": ["mp3", "flac", "aac", "ogg", "wav", "opus"],
    },
    "vimeo.com": {
        "name": "Vimeo",
        "icon": "\U0001f3ac",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": True,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": False,
        "supports_live": True,
        "max_resolution": "8K",
        "supports_hdr": True,
        "supports_dolby": True,
        "audio_formats": ["mp3", "flac", "aac", "ogg", "wav"],
    },
    "dailymotion.com": {
        "name": "Dailymotion",
        "icon": "\U0001f4fa",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": True,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": False,
        "supports_live": True,
        "max_resolution": "4K",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac", "ogg"],
    },
    "twitter.com": {
        "name": "X (Twitter)",
        "icon": "\U0001d54f",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": True,
        "supports_live": False,
        "max_resolution": "1080p",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac"],
    },
    "x.com": {
        "name": "X (Twitter)",
        "icon": "\U0001d54f",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": True,
        "supports_live": False,
        "max_resolution": "1080p",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac"],
    },
    "twitch.tv": {
        "name": "Twitch",
        "icon": "\U0001f3ae",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": False,
        "supports_live": True,
        "max_resolution": "1080p60",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac", "ogg"],
    },
    "reddit.com": {
        "name": "Reddit",
        "icon": "\U0001f916",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": True,
        "supports_live": False,
        "max_resolution": "1080p",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac"],
    },
    "tiktok.com": {
        "name": "TikTok",
        "icon": "\U0001f3b5",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": True,
        "supports_stories": False,
        "supports_posts": True,
        "supports_live": True,
        "max_resolution": "1080p",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac", "ogg"],
    },
    "instagram.com": {
        "name": "Instagram",
        "icon": "\U0001f4f8",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": True,
        "supports_stories": True,
        "supports_posts": True,
        "supports_live": True,
        "max_resolution": "4K",
        "supports_hdr": True,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac", "ogg"],
    },
    "facebook.com": {
        "name": "Facebook",
        "icon": "\U0001f464",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": True,
        "supports_stories": True,
        "supports_posts": True,
        "supports_live": True,
        "max_resolution": "4K",
        "supports_hdr": True,
        "supports_dolby": True,
        "audio_formats": ["mp3", "aac", "ogg"],
    },
    "threads.net": {
        "name": "Threads",
        "icon": "\U0001f9f5",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": True,
        "supports_live": False,
        "max_resolution": "1080p",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac"],
    },
    "pinterest.com": {
        "name": "Pinterest",
        "icon": "\U0001f4cc",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": True,
        "supports_shorts": True,
        "supports_stories": False,
        "supports_posts": True,
        "supports_live": False,
        "max_resolution": "4K",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac"],
    },
    "snapchat.com": {
        "name": "Snapchat",
        "icon": "\U0001f47b",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": True,
        "supports_stories": True,
        "supports_posts": True,
        "supports_live": False,
        "max_resolution": "1080p",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac"],
    },
    "linkedin.com": {
        "name": "LinkedIn",
        "icon": "\U0001f4bc",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": True,
        "supports_live": True,
        "max_resolution": "1080p",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac"],
    },
    "soundcloud.com": {
        "name": "SoundCloud",
        "icon": "\U0001f3a7",
        "supports_video": False,
        "supports_audio": True,
        "supports_playlist": True,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": False,
        "supports_live": False,
        "max_resolution": "audio",
        "supports_hdr": False,
        "supports_dolby": True,
        "audio_formats": ["mp3", "flac", "aac", "ogg", "wav", "opus"],
    },
    "bandcamp.com": {
        "name": "Bandcamp",
        "icon": "\U0001f3b8",
        "supports_video": False,
        "supports_audio": True,
        "supports_playlist": True,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": False,
        "supports_live": False,
        "max_resolution": "audio",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "flac", "aac", "ogg", "wav"],
    },
    "tumblr.com": {
        "name": "Tumblr",
        "icon": "\U0001f4dd",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": False,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": True,
        "supports_live": False,
        "max_resolution": "1080p",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac"],
    },
    "bilibili.com": {
        "name": "Bilibili",
        "icon": "\U0001f4fa",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": True,
        "supports_shorts": True,
        "supports_stories": False,
        "supports_posts": True,
        "supports_live": True,
        "max_resolution": "8K",
        "supports_hdr": True,
        "supports_dolby": True,
        "audio_formats": ["mp3", "flac", "aac", "ogg", "wav"],
    },
    "peertube.tv": {
        "name": "PeerTube",
        "icon": "\U0001f310",
        "supports_video": True,
        "supports_audio": True,
        "supports_playlist": True,
        "supports_shorts": False,
        "supports_stories": False,
        "supports_posts": False,
        "supports_live": True,
        "max_resolution": "4K",
        "supports_hdr": False,
        "supports_dolby": False,
        "audio_formats": ["mp3", "aac", "ogg"],
    },
}


def get_platform_info(url):
    platform = validate_platform(url)
    if platform and platform in PLATFORM_CONFIG:
        return PLATFORM_CONFIG[platform]
    if platform:
        return {
            "name": platform,
            "icon": "\U0001f310",
            "supports_video": True,
            "supports_audio": True,
            "supports_playlist": True,
            "supports_shorts": False,
            "supports_stories": False,
            "supports_posts": False,
            "supports_live": False,
            "max_resolution": "unknown",
            "supports_hdr": False,
            "supports_dolby": False,
            "audio_formats": ["mp3", "aac"],
        }
    return None


def detect_content_type(url):
    u = url.lower()
    if any(p in u for p in ["/stories/", "/story/", "story_id="]):
        return "story"
    if any(p in u for p in ["/shorts/", "/short/", "/reel/", "/reels/"]):
        return "short"
    if any(p in u for p in ["/post/", "/posts/", "/status/", "/tweet/"]):
        return "post"
    if any(p in u for p in ["/live/", "/stream/"]) or u.endswith("/live"):
        return "live"
    if any(p in u for p in ["playlist?list=", "/playlist/", "?list="]):
        return "playlist"
    if any(p in u for p in ["/track/", "/song/", "soundcloud.com", "bandcamp.com"]):
        return "audio"
    return "video"


def is_playlist_url(url):
    return detect_content_type(url) == "playlist"


def is_story_url(url):
    return detect_content_type(url) == "story"


def normalize_url(url):
    if not url or not isinstance(url, str):
        return url
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    if "youtu.be/" in url:
        video_id = url.split("/")[-1].split("?")[0]
        url = f"https://www.youtube.com/watch?v={video_id}"
    return url


def get_supported_platforms():
    return [{"domain": d, **info} for d, info in PLATFORM_CONFIG.items()]


def get_hdr_formats():
    return ["337", "315", "334", "336", "401"]


def get_dolby_audio_formats():
    return ["258", "257", "256"]


def build_quality_preset(quality, hdr=False, dolby=False):
    qmap = {"8k": 4320, "4k": 2160, "2160p": 2160, "1080p": 1080, "720p": 720, "480p": 480}
    height = qmap.get(str(quality).lower())
    video_selector = f"bestvideo[height<={height}]" if height else "bestvideo"
    if hdr:
        return f"{video_selector}[dynamic_range=HDR10|HLG|DV]+bestaudio/best/{video_selector}+bestaudio/best"
    if dolby:
        return f"{video_selector}+bestaudio[acodec^=ec-3|ac-3]/{video_selector}+bestaudio/best"
    return f"{video_selector}+bestaudio/best"

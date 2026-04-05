"""Default configuration values."""
DEFAULT_CONFIG = {
    "general": {"output_path": "./downloads", "log_level": "INFO", "log_file": "./logs/kyro.log", "notifications": True, "auto_update": True, "check_duplicates": True},
    "download": {"max_retries": 3, "retry_delay": 2.0, "retry_backoff": "exponential", "concurrent_workers": 3, "rate_limit": None, "proxy": None, "cookies_file": None, "cookies_from_browser": None, "timeout": 300, "fragment_retries": 10, "concurrent_fragment_downloads": 4},
    "video": {"default_quality": "best", "prefer_format": "mp4", "merge_output_format": "mp4", "embed_thumbnail": True, "embed_metadata": True, "embed_subtitles": False},
    "audio": {"format": "mp3", "quality": "192", "embed_thumbnail": True, "embed_metadata": True},
    "playlist": {"concurrent_downloads": 3, "sleep_interval": 0, "max_downloads": None, "autonumber_start": 1, "playlist_reverse": False, "playlist_random": False},
    "subtitles": {"enabled": False, "languages": ["en"], "embed": False, "auto_generated": True, "format": "srt"},
    "sponsorblock": {"enabled": False, "categories": ["sponsor", "intro", "outro", "selfpromo"], "api_url": "https://sponsor.ajay.app"},
    "cloud": {"enabled": False, "provider": None, "bucket": None, "region": None, "credentials_file": None},
    "ui": {"theme": "dark", "show_banner": True, "show_thumbnail": True, "show_format_table": True, "progress_bar": "rich"},
    "web": {"host": "127.0.0.1", "port": 8000, "debug": False, "cors_origins": [], "api_token": None},
}

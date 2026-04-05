"""Configuration validation schema using pydantic."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class GeneralConfig(BaseModel):
    output_path: str = "./downloads"
    log_level: str = "INFO"
    log_file: Optional[str] = "./logs/kyro.log"
    notifications: bool = True
    auto_update: bool = True
    check_duplicates: bool = True
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in allowed: raise ValueError(f"log_level must be one of {allowed}")
        return v

class DownloadConfig(BaseModel):
    max_retries: int = Field(default=3, ge=0, le=20)
    retry_delay: float = Field(default=2.0, ge=0.1)
    retry_backoff: str = "exponential"
    concurrent_workers: int = Field(default=3, ge=1, le=10)
    rate_limit: Optional[str] = None
    proxy: Optional[str] = None
    cookies_file: Optional[str] = None
    cookies_from_browser: Optional[str] = None
    timeout: int = Field(default=300, ge=30)
    fragment_retries: int = Field(default=10, ge=0)
    concurrent_fragment_downloads: int = Field(default=4, ge=1)
    @field_validator("retry_backoff")
    @classmethod
    def validate_backoff(cls, v):
        if v not in {"exponential", "linear", "fixed"}: raise ValueError("retry_backoff must be exponential, linear, or fixed")
        return v

class VideoConfig(BaseModel):
    default_quality: str = "best"
    prefer_format: str = "mp4"
    merge_output_format: str = "mp4"
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    embed_subtitles: bool = False

class AudioConfig(BaseModel):
    format: str = "mp3"
    quality: str = "192"
    embed_thumbnail: bool = True
    embed_metadata: bool = True

class PlaylistConfig(BaseModel):
    concurrent_downloads: int = Field(default=3, ge=1, le=10)
    sleep_interval: float = Field(default=0, ge=0)
    max_downloads: Optional[int] = None
    autonumber_start: int = Field(default=1, ge=1)
    playlist_reverse: bool = False
    playlist_random: bool = False

class SubtitleConfig(BaseModel):
    enabled: bool = False
    languages: list[str] = ["en"]
    embed: bool = False
    auto_generated: bool = True
    format: str = "srt"

class SponsorBlockConfig(BaseModel):
    enabled: bool = False
    categories: list[str] = ["sponsor", "intro", "outro", "selfpromo"]
    api_url: str = "https://sponsor.ajay.app"

class CloudConfig(BaseModel):
    enabled: bool = False
    provider: Optional[str] = None
    bucket: Optional[str] = None
    region: Optional[str] = None
    credentials_file: Optional[str] = None

class UIConfig(BaseModel):
    theme: str = "dark"
    show_banner: bool = True
    show_thumbnail: bool = True
    show_format_table: bool = True
    progress_bar: str = "rich"

class WebConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = False
    cors_origins: list[str] = []
    api_token: Optional[str] = None

class AppConfig(BaseModel):
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    download: DownloadConfig = Field(default_factory=DownloadConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    playlist: PlaylistConfig = Field(default_factory=PlaylistConfig)
    subtitles: SubtitleConfig = Field(default_factory=SubtitleConfig)
    sponsorblock: SponsorBlockConfig = Field(default_factory=SponsorBlockConfig)
    cloud: CloudConfig = Field(default_factory=CloudConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    web: WebConfig = Field(default_factory=WebConfig)

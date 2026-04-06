"""REST API routes for Kyro Downloader."""

import concurrent.futures
import threading
import time
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field, field_validator

from src.config.manager import load_config
from src.config.schema import AppConfig
from src.core.download_manager import DownloadManager
from src.core.queue import Priority
from src.core.downloader import get_video_info, list_video_formats
from src.services.presets import PRESET_PROFILES
from src.utils.validation import validate_url, validate_output_path
from src.utils.platform import normalize_url
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
_manager_lock = threading.Lock()
_manager_instance = None
_config_instance = None
_executor_started = threading.Event()
_rate_limit_lock = threading.Lock()
_rate_limit_state: dict[str, list[float]] = {}
_executor: concurrent.futures.ThreadPoolExecutor | None = None

# Sensitive config fields to redact from API responses
_SENSITIVE_FIELDS = {"proxy", "cookies_file", "credentials_file", "token", "api_token", "password", "secret"}


def _redact_config(config_dict):
    """Remove sensitive fields from config before returning via API."""
    redacted = {}
    for section, values in config_dict.items():
        redacted[section] = {}
        for key, value in values.items():
            if key in _SENSITIVE_FIELDS:
                redacted[section][key] = "[REDACTED]"
            else:
                redacted[section][key] = value
    return redacted


def _safe_output_path(path, base_path):
    """Validate output path stays within allowed directory."""
    resolved = Path(path).resolve()
    base = Path(base_path).resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Output path must be within download directory")
    return resolved


def _check_rate_limit(bucket: str, limit: int, window_seconds: int = 60) -> None:
    now = time.time()
    with _rate_limit_lock:
        stale_cutoff = now - window_seconds
        stale_buckets = []
        for bucket_name, entries in _rate_limit_state.items():
            kept = [entry for entry in entries if entry >= stale_cutoff]
            if kept:
                _rate_limit_state[bucket_name] = kept
            else:
                stale_buckets.append(bucket_name)
        for bucket_name in stale_buckets:
            _rate_limit_state.pop(bucket_name, None)

        timestamps = _rate_limit_state.get(bucket, [])
        timestamps = [t for t in timestamps if now - t < window_seconds]
        if len(timestamps) >= limit:
            retry_after = max(1, int(window_seconds - (now - timestamps[0])))
            raise HTTPException(
                status_code=429,
                detail="Too Many Requests",
                headers={"Retry-After": str(retry_after)},
            )
        timestamps.append(now)
        _rate_limit_state[bucket] = timestamps


def get_executor() -> concurrent.futures.ThreadPoolExecutor:
    global _executor
    if _executor is None:
        with _manager_lock:
            if _executor is None:
                _executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="kyro-web")
    return _executor


def shutdown_executor() -> None:
    global _executor
    with _manager_lock:
        if _executor is not None:
            _executor.shutdown(wait=False, cancel_futures=True)
            _executor = None
            _executor_started.clear()


def get_manager():
    global _manager_instance, _config_instance
    if _manager_instance is None:
        with _manager_lock:
            if _manager_instance is None:
                _config_instance = load_config()
                _manager_instance = DownloadManager(_config_instance.model_dump())
    return _manager_instance


def get_config():
    global _config_instance, _manager_instance
    with _manager_lock:
        if _config_instance is None:
            _config_instance = load_config()
            if _manager_instance is None:
                _manager_instance = DownloadManager(_config_instance.model_dump())
    return _config_instance


def _get_configured_api_token():
    cfg = get_config()
    web_cfg = getattr(cfg, "web", None)
    return getattr(web_cfg, "api_token", None) if web_cfg else None


async def require_api_auth(
    authorization: str | None = Header(default=None),
    x_api_token: str | None = Header(default=None, alias="X-API-Token"),
):
    """Require bearer or X-API-Token when web.api_token is configured."""
    configured_token = _get_configured_api_token()
    if not configured_token:
        return
    supplied_token = None
    if authorization and authorization.lower().startswith("bearer "):
        supplied_token = authorization[7:].strip()
    elif x_api_token:
        supplied_token = x_api_token.strip()
    if supplied_token != configured_token:
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Bearer"})


def _ensure_executor_running():
    if not _executor_started.is_set():
        with _manager_lock:
            if not _executor_started.is_set():
                manager = get_manager()
                get_executor().submit(manager.execute)
                _executor_started.set()


class DownloadRequest(BaseModel):
    url: str = Field(max_length=2048)
    output_path: str | None = Field(default=None, max_length=512)
    format_id: str | None = Field(default=None, max_length=64)
    only_audio: bool = False
    quality: str = "best"
    hdr: bool = False
    dolby: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "192"
    audio_selector: str | None = Field(default=None, max_length=128)
    priority: str = "normal"
    subtitles: bool | dict = False
    sponsorblock: bool = False
    preset: str = "none"
    output_template: str | None = Field(default=None, max_length=256)


class BatchRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=100)
    output_path: str | None = Field(default=None, max_length=512)
    only_audio: bool = False
    quality: str = "best"
    hdr: bool = False
    dolby: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "192"
    audio_selector: str | None = Field(default=None, max_length=128)
    subtitles: bool | dict = False
    sponsorblock: bool = False
    output_template: str | None = Field(default=None, max_length=256)
    workers: int = 3

    @field_validator("urls")
    @classmethod
    def _validate_urls(cls, urls: list[str]) -> list[str]:
        normalized_urls: list[str] = []
        for raw_url in urls:
            url = normalize_url(str(raw_url).strip())
            if not validate_url(url):
                raise ValueError(f"Invalid URL in batch request: {raw_url}")
            normalized_urls.append(url)
        return normalized_urls


class PlaylistRequest(BaseModel):
    url: str = Field(max_length=2048)
    output_path: str | None = Field(default=None, max_length=512)
    only_audio: bool = False
    quality: str = "best"
    hdr: bool = False
    dolby: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "192"
    audio_selector: str | None = Field(default=None, max_length=128)
    subtitles: bool | dict = False
    sponsorblock: bool = False
    output_template: str | None = Field(default=None, max_length=256)


def _normalize_quality(value: str) -> str:
    """Normalize quality labels to manager-supported values."""
    normalized = value.strip().lower()
    quality_map = {
        "best": "best",
        "8k": "8k",
        "4320p": "8k",
        "4k": "4k",
        "2160p": "4k",
        "1080p": "1080p",
        "720p": "720p",
        "480p": "480p",
        "360p": "360p",
        "240p": "240p",
        "144p": "144p",
    }
    return quality_map.get(normalized, normalized)


def _resolve_download_profile(req: DownloadRequest) -> dict[str, object]:
    """Resolve effective download fields with optional preset support."""
    subtitles_cfg = _resolve_subtitles_request(req.subtitles)
    output_template = req.output_template
    only_audio = req.only_audio
    audio_format = req.audio_format
    audio_quality = req.audio_quality
    quality = _normalize_quality(req.quality)
    hdr = req.hdr
    dolby = req.dolby

    preset = PRESET_PROFILES.get(req.preset)
    if preset:
        only_audio = bool(preset.get("only_audio", only_audio))
        audio_format = str(preset.get("audio_format", audio_format))
        audio_quality = str(preset.get("audio_quality", audio_quality))
        subtitles_cfg = preset.get("subtitles", subtitles_cfg)
        preset_output_template = preset.get("output_template")
        if preset_output_template is not None:
            output_template = str(preset_output_template)

    return {
        "only_audio": only_audio,
        "audio_format": audio_format,
        "audio_quality": audio_quality,
        "subtitles_cfg": subtitles_cfg,
        "output_template": output_template,
        "quality": quality,
        "hdr": hdr,
        "dolby": dolby,
    }


def _resolve_subtitles_request(subtitles: bool | dict[str, Any]) -> dict[str, Any] | None:
    """Normalize bool/dict subtitle payloads into downloader config."""
    if isinstance(subtitles, dict):
        return subtitles
    if subtitles:
        return {
            "enabled": True,
            "languages": ["en"],
            "embed": False,
            "auto_generated": True,
            "format": "srt",
        }
    return None


class ConfigUpdate(BaseModel):
    section: str = Field(max_length=64)
    key: str = Field(max_length=64)
    value: str = Field(max_length=1024)


@router.post("/download")
async def queue_download(req: DownloadRequest):
    _check_rate_limit("api_download", limit=30)
    url = normalize_url(req.url)
    if not validate_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    manager = get_manager()
    cfg = get_config()
    output_base = cfg.general.output_path
    output = validate_output_path(req.output_path or output_base)
    _safe_output_path(output, output_base)
    priority_map = {
        "low": Priority.LOW,
        "normal": Priority.NORMAL,
        "high": Priority.HIGH,
        "critical": Priority.CRITICAL,
    }
    priority = priority_map.get(req.priority, Priority.NORMAL)
    profile = _resolve_download_profile(req)
    sponsorblock_cfg = {"enabled": True} if req.sponsorblock else None
    item = manager.queue_download(
        url=url,
        output_path=str(output),
        format_id=req.format_id,
        only_audio=bool(profile["only_audio"]),
        priority=priority,
        quality=str(profile["quality"]),
        hdr=bool(profile["hdr"]),
        dolby=bool(profile["dolby"]),
        audio_format=str(profile["audio_format"]),
        audio_quality=str(profile["audio_quality"]),
        audio_selector=req.audio_selector,
        subtitles=profile["subtitles_cfg"],
        sponsorblock=sponsorblock_cfg,
        output_template=profile["output_template"],
    )
    _ensure_executor_running()
    return {
        "task_id": item.task_id,
        "url": item.url,
        "status": item.status.value,
        "message": "Download queued successfully",
    }


@router.post("/batch")
async def batch_download(req: BatchRequest):
    manager = get_manager()
    cfg = get_config()
    output_base = cfg.general.output_path
    output = validate_output_path(req.output_path or output_base)
    _safe_output_path(output, output_base)
    items = []
    subtitles_cfg = _resolve_subtitles_request(req.subtitles)
    sponsorblock_cfg = {"enabled": True} if req.sponsorblock else None
    for url in req.urls:
        item = manager.queue_download(
            url=url,
            output_path=str(output),
            only_audio=req.only_audio,
            quality=_normalize_quality(req.quality),
            hdr=req.hdr,
            dolby=req.dolby,
            audio_format=req.audio_format,
            audio_quality=req.audio_quality,
            audio_selector=req.audio_selector,
            subtitles=subtitles_cfg,
            sponsorblock=sponsorblock_cfg,
            output_template=req.output_template,
        )
        items.append({"task_id": item.task_id, "url": item.url})
    manager.config["concurrent_workers"] = req.workers
    _ensure_executor_running()
    return {"queued": len(items), "items": items}


@router.post("/playlist")
async def download_playlist_req(req: PlaylistRequest):
    url = normalize_url(req.url)
    if not validate_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    manager = get_manager()
    cfg = get_config()
    output_base = cfg.general.output_path
    output = validate_output_path(req.output_path or output_base)
    _safe_output_path(output, output_base)
    subtitles_cfg = _resolve_subtitles_request(req.subtitles)
    sponsorblock_cfg = {"enabled": True} if req.sponsorblock else None
    get_executor().submit(
        manager.download_playlist,
        url=url,
        output_path=str(output),
        format_id=None,
        only_audio=req.only_audio,
        quality=_normalize_quality(req.quality),
        hdr=req.hdr,
        dolby=req.dolby,
        audio_format=req.audio_format,
        audio_quality=req.audio_quality,
        audio_selector=req.audio_selector,
        subtitles=subtitles_cfg,
        sponsorblock=sponsorblock_cfg,
        output_template=req.output_template,
    )
    return {"message": "Playlist download started in background"}


@router.get("/status")
async def get_status():
    return get_manager().get_status()


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    manager = get_manager()
    item = manager.queue.get_item(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    progress = manager.progress.get_task(task_id)
    return {
        "task_id": item.task_id,
        "url": item.url,
        "status": item.status.value,
        "progress": {
            "percentage": progress.percentage if progress else 0,
            "speed": progress.speed if progress else 0,
            "eta": progress.eta if progress else 0,
        }
        if progress
        else None,
    }


@router.get("/queue")
async def get_queue():
    items = get_manager().queue.get_all_items()
    return [{"task_id": i.task_id, "url": i.url, "status": i.status.value, "priority": i.priority.name} for i in items]


@router.post("/queue/{task_id}/pause")
async def pause_task(task_id: str):
    if get_manager().queue.pause(task_id):
        return {"message": "Task paused"}
    raise HTTPException(status_code=404, detail="Task not found or cannot be paused")


@router.post("/queue/{task_id}/resume")
async def resume_task(task_id: str):
    if get_manager().queue.resume(task_id):
        return {"message": "Task resumed"}
    raise HTTPException(status_code=404, detail="Task not found or cannot be resumed")


@router.delete("/queue/{task_id}")
async def cancel_task(task_id: str):
    manager = get_manager()
    if manager.queue.cancel(task_id) or manager.queue.remove(task_id):
        return {"message": "Task cancelled"}
    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/info")
async def get_video_info_endpoint(url: str):
    url = normalize_url(url)
    if not validate_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    info = get_video_info(url)
    formats = list_video_formats(info.formats)
    return {
        "title": info.title,
        "duration": info.duration,
        "duration_str": info.duration_str,
        "uploader": info.uploader,
        "thumbnail": info.thumbnail,
        "is_playlist": info.is_playlist,
        "formats": [
            {
                "format_id": f["format_id"],
                "resolution": f"{f.get('width', '?')}x{f.get('height', '?')}",
                "ext": f.get("ext", "?"),
                "fps": f.get("fps"),
            }
            for f in formats[:20]
        ],
    }


@router.get("/platforms")
async def list_platforms():
    from src.utils.platform import get_supported_platforms

    return get_supported_platforms()


@router.get("/config")
async def get_config_endpoint():
    return _redact_config(get_config().model_dump())


@router.put("/config", dependencies=[Depends(require_api_auth)])
async def update_config(req: ConfigUpdate):
    try:
        _check_rate_limit("api_config_write", limit=10)
        section, key, value = req.section, req.key, req.value
        if value.lower() in ("true", "yes", "1"):
            value = True
        elif value.lower() in ("false", "no", "0"):
            value = False
        else:
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
        with _manager_lock:
            global _config_instance, _manager_instance
            current = _config_instance.model_dump() if _config_instance else load_config().model_dump()
            if section in current and key in current[section]:
                current[section][key] = value
                try:
                    _config_instance = AppConfig.model_validate(current)
                except Exception as e:
                    raise HTTPException(status_code=422, detail=f"Invalid config value: {e}") from e
                _manager_instance = DownloadManager(_config_instance.model_dump())
                return {"message": f"Updated {section}.{key} = {value}"}
        raise HTTPException(status_code=400, detail="Invalid config key")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Config update failed")
        raise HTTPException(status_code=500, detail="Internal server error")

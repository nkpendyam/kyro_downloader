"""REST API routes for Kyro Downloader."""
import threading
import concurrent.futures
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.config.manager import load_config
from src.core.download_manager import DownloadManager
from src.core.queue import Priority
from src.core.downloader import get_video_info, list_video_formats
from src.utils.validation import validate_url, validate_output_path
from src.utils.platform import normalize_url
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
_manager_lock = threading.Lock()
_manager_instance = None
_config_instance = None
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="kyro-web")
_executor_started = threading.Event()

# Sensitive config fields to redact from API responses
_SENSITIVE_FIELDS = {"proxy", "cookies_file", "credentials_file", "token", "password", "secret"}

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
    if not str(resolved).startswith(str(base)):
        raise HTTPException(status_code=403, detail="Output path must be within download directory")
    return resolved

def get_manager():
    global _manager_instance, _config_instance
    if _manager_instance is None:
        with _manager_lock:
            if _manager_instance is None:
                _config_instance = load_config()
                _manager_instance = DownloadManager(_config_instance.model_dump())
    return _manager_instance

def get_config():
    global _config_instance
    if _config_instance is None:
        get_manager()
    return _config_instance

def _ensure_executor_running():
    if not _executor_started.is_set():
        with _manager_lock:
            if not _executor_started.is_set():
                manager = get_manager()
                _executor.submit(manager.execute)
                _executor_started.set()

class DownloadRequest(BaseModel):
    url: str = Field(max_length=2048)
    output_path: Optional[str] = Field(default=None, max_length=512)
    format_id: Optional[str] = Field(default=None, max_length=64)
    only_audio: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "192"
    priority: str = "normal"
    subtitles: bool = False
    sponsorblock: bool = False

class BatchRequest(BaseModel):
    urls: list[str] = Field(max_length=100)
    output_path: Optional[str] = Field(default=None, max_length=512)
    only_audio: bool = False
    workers: int = 3

class PlaylistRequest(BaseModel):
    url: str = Field(max_length=2048)
    output_path: Optional[str] = Field(default=None, max_length=512)

class ConfigUpdate(BaseModel):
    section: str = Field(max_length=64)
    key: str = Field(max_length=64)
    value: str = Field(max_length=1024)

@router.post("/download")
async def queue_download(req: DownloadRequest):
    url = normalize_url(req.url)
    if not validate_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    manager = get_manager()
    cfg = get_config()
    output_base = cfg.general.output_path
    output = validate_output_path(req.output_path or output_base)
    _safe_output_path(output, output_base)
    priority_map = {"low": Priority.LOW, "normal": Priority.NORMAL, "high": Priority.HIGH, "critical": Priority.CRITICAL}
    priority = priority_map.get(req.priority, Priority.NORMAL)
    item = manager.queue_download(url=url, output_path=str(output), format_id=req.format_id, only_audio=req.only_audio, priority=priority)
    _ensure_executor_running()
    return {"task_id": item.task_id, "url": item.url, "status": item.status.value, "message": "Download queued successfully"}

@router.post("/batch")
async def batch_download(req: BatchRequest):
    manager = get_manager()
    cfg = get_config()
    output_base = cfg.general.output_path
    output = validate_output_path(req.output_path or output_base)
    _safe_output_path(output, output_base)
    items = []
    for url in req.urls:
        url = normalize_url(url)
        if validate_url(url):
            item = manager.queue_download(url=url, output_path=str(output), only_audio=req.only_audio)
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
    _executor.submit(manager.download_playlist, url, str(output))
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
        } if progress else None,
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

@router.put("/config")
async def update_config(req: ConfigUpdate):
    try:
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
        global _config_instance
        current = _config_instance.model_dump() if _config_instance else load_config().model_dump()
        if section in current and key in current[section]:
            current[section][key] = value
            from src.config.schema import AppConfig
            _config_instance = AppConfig(**current)
            with _manager_lock:
                global _manager_instance
                _manager_instance = DownloadManager(_config_instance.model_dump())
            return {"message": f"Updated {section}.{key} = {value}"}
        raise HTTPException(status_code=400, detail="Invalid config key")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Config update failed")
        raise HTTPException(status_code=500, detail="Internal server error")

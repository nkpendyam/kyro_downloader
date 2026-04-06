"""Download manager - orchestrates the full download pipeline."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Any, TypedDict

from src.core.downloader import get_video_info, download_single, download_playlist
from src.core.queue import DownloadQueue, Priority
from src.core.concurrent import ConcurrentExecutor
from src.core.progress import create_progress_hook, ProgressTracker
from src.utils.validation import validate_url, validate_output_path
from src.utils.dedup import check_duplicate, generate_unique_filename
from src.utils.ffmpeg import validate_ffmpeg
from src.utils.platform import normalize_url, QUALITY_HEIGHT_MAP
from src.utils.validation import validate_platform
from src.utils.logger import get_logger
from src.utils.notifications import notify_download_complete, notify_download_failed, notify_playlist_complete
from src.services.statistics import StatsTracker

logger = get_logger(__name__)


def _notify_playlist_outcome(title: str, completed_count: int, failed_count: int, is_cancelled: bool) -> None:
    """Notify playlist completion status with accurate counts."""
    suffix = ""
    if is_cancelled:
        suffix = f" (cancelled, {failed_count} failed)" if failed_count else " (cancelled)"
    elif failed_count:
        suffix = f" ({failed_count} failed)"
    notify_playlist_complete(title, f"{completed_count}{suffix}")


class QueueStatusDict(TypedDict):
    queue_size: int
    pending: int
    active: int
    completed: int
    failed: int


class ManagerStatusDict(QueueStatusDict, total=False):
    queue: QueueStatusDict
    progress: dict[str, Any]
    executor_running: bool


@dataclass
class DownloadOptions:
    """Normalized options for a single download request."""

    url: str
    output_path: str | None = None
    format_id: str | None = None
    only_audio: bool = False
    priority: Priority = Priority.NORMAL
    quality: str | None = None
    hdr: bool = False
    dolby: bool = False
    audio_format: str | None = None
    audio_quality: str | None = None
    audio_selector: str | None = None
    subtitles_cfg: dict[str, Any] | None = None
    sponsorblock: dict[str, Any] | None = None
    output_template: str | None = None
    proxy: str | None = None
    cookies_file: str | None = None
    cookies_from_browser: str | None = None


class DownloadManager:
    def __init__(self, config: dict[str, Any] | None = None, plugin_loader: Any | None = None) -> None:
        self.config = config or {}
        explicit_state_path = self.config.get("queue_state_path")
        in_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST"))
        self._queue_persistence_enabled = bool(self.config.get("queue_persistence_enabled", True)) and (
            not in_pytest or explicit_state_path is not None
        )
        default_state_path = Path(self.config.get("output_path", "./downloads")) / ".queue_state.json"
        self._queue_state_path = Path(explicit_state_path) if explicit_state_path else default_state_path
        self.queue = DownloadQueue(on_change=self._save_queue_state)
        self.progress = ProgressTracker()
        self.stats = StatsTracker()
        self._executor: ConcurrentExecutor | None = None
        self._executor_thread: threading.Thread | None = None
        self._current_info = None
        self.plugin_loader = plugin_loader
        self._validate_ffmpeg_on_init()
        self._restore_queue_state()

    def _validate_ffmpeg_on_init(self) -> None:
        try:
            validate_ffmpeg(required=False)
        except RuntimeError:
            logger.warning("FFmpeg not available - audio extraction disabled")

    def _save_queue_state(self) -> None:
        """Persist incomplete queue items to disk for crash/restart recovery."""
        if not self._queue_persistence_enabled:
            return
        try:
            state = self.queue.export_state()
            self._queue_state_path.parent.mkdir(parents=True, exist_ok=True)
            with self._queue_state_path.open("w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=True, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist queue state: {e}")

    def _restore_queue_state(self) -> None:
        """Restore persisted incomplete queue items when available."""
        if not self._queue_persistence_enabled:
            return
        if not self._queue_state_path.exists():
            return
        try:
            with self._queue_state_path.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
            restored = self.queue.import_state(state)
            if restored:
                logger.info(f"Restored {restored} queue item(s) from {self._queue_state_path}")
        except Exception as e:
            logger.warning(f"Failed to restore queue state: {e}")

    def prepare_download(
        self,
        url: str,
        output_path: str | None = None,
        format_id: str | None = None,
        only_audio: bool = False,
        priority: Priority = Priority.NORMAL,
    ) -> tuple[Any, str | None]:
        url = normalize_url(url)
        if not validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
        output = validate_output_path(output_path or self.config.get("output_path", "./downloads"))
        info = get_video_info(
            url,
            cookies_file=self.config.get("cookies_file"),
            cookies_from_browser=self.config.get("cookies_from_browser"),
            proxy=self.config.get("proxy"),
        )
        self._current_info = info
        unique_name = None
        if self.config.get("check_duplicates", True) and not info.is_playlist:
            existing = check_duplicate(str(output), info.title)
            if existing:
                unique_name = generate_unique_filename(str(output), info.title)
                logger.info(f"Duplicate found, using unique filename: {unique_name}")
        return info, unique_name

    def queue_download(
        self,
        url: str | DownloadOptions,
        output_path: str | None = None,
        format_id: str | None = None,
        only_audio: bool = False,
        priority: Priority = Priority.NORMAL,
        quality: str | None = None,
        hdr: bool = False,
        dolby: bool = False,
        audio_format: str | None = None,
        audio_quality: str | None = None,
        audio_selector: str | None = None,
        subtitles: dict[str, Any] | None = None,
        sponsorblock: dict[str, Any] | None = None,
        output_template: str | None = None,
    ) -> Any:
        options = (
            url
            if isinstance(url, DownloadOptions)
            else DownloadOptions(
                url=url,
                output_path=output_path,
                format_id=format_id,
                only_audio=only_audio,
                priority=priority,
                quality=quality,
                hdr=hdr,
                dolby=dolby,
                audio_format=audio_format,
                audio_quality=audio_quality,
                audio_selector=audio_selector,
                subtitles_cfg=subtitles,
                sponsorblock=sponsorblock,
                output_template=output_template,
            )
        )
        normalized_url = normalize_url(options.url)
        output = validate_output_path(options.output_path or self.config.get("output_path", "./downloads"))

        metadata: dict[str, Any] = {
            "quality": options.quality,
            "hdr": options.hdr,
            "dolby": options.dolby,
            "audio_format": options.audio_format,
            "audio_quality": options.audio_quality,
            "audio_selector": options.audio_selector,
        }
        cfg = self._build_download_config()
        if options.subtitles_cfg is not None:
            cfg["subtitles"] = options.subtitles_cfg
        if options.sponsorblock is not None:
            cfg["sponsorblock"] = options.sponsorblock
        if options.output_template:
            cfg["output_template"] = options.output_template
        if options.proxy:
            cfg["proxy"] = options.proxy
        if options.cookies_file:
            cfg["cookies_file"] = options.cookies_file
        if options.cookies_from_browser:
            cfg["cookies_from_browser"] = options.cookies_from_browser

        return self.queue.add(
            url=normalized_url,
            priority=options.priority,
            format_id=options.format_id,
            only_audio=options.only_audio,
            output_path=str(output),
            config=cfg,
            metadata=metadata,
        )

    def download_now(
        self,
        url: str | DownloadOptions,
        output_path: str | None = None,
        format_id: str | None = None,
        only_audio: bool = False,
        priority: Priority = Priority.NORMAL,
        quality: str | None = None,
        hdr: bool = False,
        dolby: bool = False,
        audio_format: str | None = None,
        audio_quality: str | None = None,
        audio_selector: str | None = None,
        subtitles: dict[str, Any] | None = None,
        sponsorblock: dict[str, Any] | None = None,
        output_template: str | None = None,
        progress_hook: Any | None = None,
        config: dict[str, Any] | None = None,
    ) -> list[str]:
        options = (
            url
            if isinstance(url, DownloadOptions)
            else DownloadOptions(
                url=url,
                output_path=output_path,
                format_id=format_id,
                only_audio=only_audio,
                priority=priority,
                quality=quality,
                hdr=hdr,
                dolby=dolby,
                audio_format=audio_format,
                audio_quality=audio_quality,
                audio_selector=audio_selector,
                subtitles_cfg=subtitles,
                sponsorblock=sponsorblock,
                output_template=output_template,
            )
        )
        normalized_url = normalize_url(options.url)
        output = validate_output_path(options.output_path or self.config.get("output_path", "./downloads"))
        cfg = self._build_download_config()
        if config:
            cfg = self._deep_merge(cfg, config)
        cfg["format_id"] = options.format_id
        cfg["only_audio"] = options.only_audio
        cfg["hdr"] = options.hdr
        cfg["dolby"] = options.dolby
        if options.audio_format:
            cfg["audio_format"] = options.audio_format
        if options.audio_quality:
            cfg["audio_quality"] = options.audio_quality
        if options.audio_selector:
            cfg["audio_selector"] = options.audio_selector
        if options.subtitles_cfg is not None:
            cfg["subtitles"] = options.subtitles_cfg
        if options.sponsorblock is not None:
            cfg["sponsorblock"] = options.sponsorblock
        if options.output_template:
            cfg["output_template"] = options.output_template
        if options.proxy:
            cfg["proxy"] = options.proxy
        if options.cookies_file:
            cfg["cookies_file"] = options.cookies_file
        if options.cookies_from_browser:
            cfg["cookies_from_browser"] = options.cookies_from_browser
        if options.subtitles_cfg:
            cfg["subtitles"] = options.subtitles_cfg
        if options.sponsorblock:
            cfg["sponsorblock"] = options.sponsorblock
        if options.output_template:
            cfg["output_template"] = options.output_template
        if options.quality and options.quality != "best" and not options.hdr and not options.dolby:
            target_h = QUALITY_HEIGHT_MAP.get(options.quality)
            if target_h:
                cfg["format"] = f"bestvideo[height<={target_h}]+bestaudio/best[ext=m4a]/best"
        effective_progress_hook = progress_hook or create_progress_hook(self.progress, normalized_url)
        try:
            if self.plugin_loader:
                self.plugin_loader.fire_hook("on_download_start", url=normalized_url, config=cfg)
            result = download_single(
                url=normalized_url,
                output_path=str(output),
                format_id=options.format_id,
                only_audio=options.only_audio,
                config=cfg,
                progress_hook=effective_progress_hook,
            )
            title = self._current_info.title if self._current_info else normalized_url
            if self._notifications_enabled(cfg):
                notify_download_complete(title, str(output))
            if self.plugin_loader:
                self.plugin_loader.fire_hook("on_download_complete", url=normalized_url, output_path=str(output))
            return result
        except Exception as e:
            logger.error(f"Download failed: {e}")
            if self._notifications_enabled(cfg):
                notify_download_failed(normalized_url, str(e))
            if self.plugin_loader:
                self.plugin_loader.fire_hook("on_download_error", url=normalized_url, error=str(e))
            raise

    def queue_batch(
        self,
        urls: list[str],
        output_path: str | None = None,
        format_id: str | None = None,
        only_audio: bool = False,
        priority: Priority = Priority.NORMAL,
        quality: str | None = None,
        hdr: bool = False,
        dolby: bool = False,
        audio_format: str | None = None,
        audio_quality: str | None = None,
        audio_selector: str | None = None,
        subtitles: dict[str, Any] | None = None,
        sponsorblock: dict[str, Any] | None = None,
        output_template: str | None = None,
        proxy: str | None = None,
        cookies_file: str | None = None,
        cookies_from_browser: str | None = None,
    ) -> list[Any]:
        items: list[Any] = []
        for item_url in urls:
            items.append(
                self.queue_download(
                    DownloadOptions(
                        url=item_url,
                        output_path=output_path,
                        format_id=format_id,
                        only_audio=only_audio,
                        priority=priority,
                        quality=quality,
                        hdr=hdr,
                        dolby=dolby,
                        audio_format=audio_format,
                        audio_quality=audio_quality,
                        audio_selector=audio_selector,
                        subtitles_cfg=subtitles,
                        sponsorblock=sponsorblock,
                        output_template=output_template,
                        proxy=proxy,
                        cookies_file=cookies_file,
                        cookies_from_browser=cookies_from_browser,
                    )
                )
            )
        return items

    def execute(self) -> None:
        if self.queue.is_empty:
            self._executor = None
            return
        max_workers = int(self.config.get("concurrent_workers", 3))
        self._executor = ConcurrentExecutor(
            queue=self.queue,
            max_workers=max_workers,
            progress_tracker=self.progress,
            on_item_complete=self._on_item_complete,
        )
        self._executor.start()

    def execute_async(self) -> None:
        if self.queue.is_empty:
            return
        if self._executor and self._executor.is_running:
            return
        max_workers = int(self.config.get("concurrent_workers", 3))
        self._executor = ConcurrentExecutor(
            queue=self.queue,
            max_workers=max_workers,
            progress_tracker=self.progress,
            on_item_complete=self._on_item_complete,
        )
        self._executor.start_async()

    def download_playlist(
        self,
        url: str | DownloadOptions,
        output_path: str | None = None,
        format_id: str | None = None,
        only_audio: bool = False,
        quality: str | None = None,
        hdr: bool = False,
        dolby: bool = False,
        audio_format: str | None = None,
        audio_quality: str | None = None,
        audio_selector: str | None = None,
        subtitles: dict[str, Any] | None = None,
        sponsorblock: dict[str, Any] | None = None,
        output_template: str | None = None,
    ) -> list[str]:
        options = (
            url
            if isinstance(url, DownloadOptions)
            else DownloadOptions(
                url=url,
                output_path=output_path,
                format_id=format_id,
                only_audio=only_audio,
                quality=quality,
                hdr=hdr,
                dolby=dolby,
                audio_format=audio_format,
                audio_quality=audio_quality,
                audio_selector=audio_selector,
                subtitles_cfg=subtitles,
                sponsorblock=sponsorblock,
                output_template=output_template,
            )
        )
        normalized_url = normalize_url(options.url)
        output = validate_output_path(options.output_path or self.config.get("output_path", "./downloads"))
        try:
            info = get_video_info(
                normalized_url,
                cookies_file=self.config.get("cookies_file"),
                cookies_from_browser=self.config.get("cookies_from_browser"),
                proxy=self.config.get("proxy"),
            )
            self._current_info = info
            cfg = self._build_download_config()
            cfg["format_id"] = options.format_id
            cfg["only_audio"] = options.only_audio
            cfg["hdr"] = options.hdr
            cfg["dolby"] = options.dolby
            if options.audio_format:
                cfg["audio_format"] = options.audio_format
            if options.audio_quality:
                cfg["audio_quality"] = options.audio_quality
            if options.audio_selector:
                cfg["audio_selector"] = options.audio_selector
            if options.subtitles_cfg is not None:
                cfg["subtitles"] = options.subtitles_cfg
            if options.sponsorblock is not None:
                cfg["sponsorblock"] = options.sponsorblock
            if options.output_template:
                cfg["output_template"] = options.output_template
            if options.proxy:
                cfg["proxy"] = options.proxy
            if options.cookies_file:
                cfg["cookies_file"] = options.cookies_file
            if options.cookies_from_browser:
                cfg["cookies_from_browser"] = options.cookies_from_browser
            if options.quality and options.quality != "best":
                target_h = QUALITY_HEIGHT_MAP.get(options.quality)
                if target_h:
                    cfg["format"] = f"bestvideo[height<={target_h}]+bestaudio/best[ext=m4a]/best"
            if options.only_audio:
                cfg["audio_format"] = self.config.get("audio_format", "mp3")
                cfg["audio_quality"] = self.config.get("audio_quality", "192")
            results = download_playlist(
                url=normalized_url,
                output_path=str(output),
                config=cfg,
                progress_tracker=self.progress,
                cancel_event=cfg.get("cancel_event"),
            )
            _notify_playlist_outcome(
                title=info.title,
                completed_count=results.completed_count,
                failed_count=len(results.failed_urls),
                is_cancelled=results.is_cancelled,
            )
            return results
        except Exception as e:
            logger.error(f"Playlist download failed: {e}")
            raise

    def stop(self) -> None:
        if self._executor:
            self._executor.stop()
        self._save_queue_state()

    def pause_queue(self, task_id: str) -> bool:
        return self.queue.pause(task_id)

    def resume_queue(self, task_id: str) -> bool:
        return self.queue.resume(task_id)

    def cancel_queue(self, task_id: str) -> bool:
        return self.queue.cancel(task_id)

    def get_queue_status(self) -> QueueStatusDict:
        return {
            "queue_size": self.queue.size,
            "pending": self.queue.pending_count,
            "active": self.queue.active_count,
            "completed": self.queue.completed_count,
            "failed": self.queue.failed_count,
        }

    def get_queue_stats(self) -> ManagerStatusDict:
        queue_status = self.get_queue_status()
        return {
            **queue_status,
            "queue": queue_status,
            "progress": self.progress.get_overall_progress(),
            "executor_running": self._executor.is_running if self._executor else False,
        }

    def get_status(self) -> ManagerStatusDict:
        return self.get_queue_stats()

    def _on_item_complete(self, task_id: str, success: bool, error: str | None = None) -> None:
        if success:
            logger.info(f"Task completed: {task_id}")
            try:
                task_progress = self.progress.get_task(task_id)
                item = self.queue.get_item(task_id)
                if item:
                    platform = validate_platform(item.url) or "unknown"
                    wall_time = task_progress.duration if task_progress else 0
                    self.stats.record_download(
                        success=True,
                        bytes_downloaded=task_progress.downloaded_bytes if task_progress else 0,
                        duration=task_progress.duration if task_progress else 0,
                        format_id=item.format_id or "best",
                        platform=platform,
                        wall_time=wall_time,
                    )
            except Exception as e:
                logger.debug(f"Stats tracking error: {e}")
        else:
            logger.error(f"Task failed: {task_id} - {error}")
            try:
                self.stats.record_download(success=False)
            except Exception:
                pass

    def _build_download_config(self, cancel_event: Any | None = None) -> dict[str, Any]:
        cfg = {
            "audio_format": self.config.get("audio_format", "mp3"),
            "audio_quality": self.config.get("audio_quality", "192"),
            "audio_selector": self.config.get("audio_selector"),
            "embed_thumbnail": self.config.get("embed_thumbnail", True),
            "embed_metadata": self.config.get("embed_metadata", True),
            "subtitles": self.config.get("subtitles"),
            "sponsorblock": self.config.get("sponsorblock"),
            "rate_limit": self.config.get("rate_limit"),
            "proxy": self.config.get("proxy"),
            "cookies_file": self.config.get("cookies_file"),
            "cookies_from_browser": self.config.get("cookies_from_browser"),
            "prefer_format": self.config.get("prefer_format", "mp4"),
            "fragment_retries": self.config.get("fragment_retries", 10),
            "concurrent_fragments": self.config.get("concurrent_fragments", 4),
            "playlist": self.config.get("playlist"),
            "hdr": self.config.get("hdr", False),
            "dolby": self.config.get("dolby", False),
            "output_template": self.config.get("output_template"),
            "notifications": self.config.get("notifications"),
            "no_notify": self.config.get("no_notify", False),
        }
        if cancel_event is not None:
            cfg["cancel_event"] = cancel_event
        return cfg

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge override into base without losing existing keys."""
        merged = dict(base)
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update config in-place without destroying queue/executor state."""
        self.config = self._deep_merge(self.config, new_config)

    def _notifications_enabled(self, cfg: dict[str, Any] | None = None) -> bool:
        source = cfg if isinstance(cfg, dict) else self.config
        if source.get("no_notify") is True:
            return False
        if "notifications" in source:
            return bool(source.get("notifications"))
        general = source.get("general")
        if isinstance(general, dict) and "notifications" in general:
            return bool(general.get("notifications"))
        return True

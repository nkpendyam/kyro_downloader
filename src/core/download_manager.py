"""Download manager - orchestrates the full download pipeline."""

from src.core.downloader import get_video_info, download_single, download_playlist
from src.core.queue import DownloadQueue, Priority
from src.core.concurrent import ConcurrentExecutor
from src.core.progress import ProgressTracker
from src.utils.validation import validate_url, validate_output_path, validate_batch_file
from src.utils.dedup import check_duplicate, generate_unique_filename
from src.utils.ffmpeg import validate_ffmpeg
from src.utils.platform import normalize_url, validate_platform
from src.utils.logger import get_logger
from src.utils.notifications import notify_download_complete, notify_download_failed, notify_playlist_complete
from src.services.statistics import StatsTracker
from src.plugins.loader import PluginLoader

logger = get_logger(__name__)


class DownloadManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.queue = DownloadQueue()
        self.progress = ProgressTracker()
        self.stats = StatsTracker()
        self._executor = None
        self._current_info = None
        self.plugin_loader = PluginLoader()
        self._validate_ffmpeg_on_init()

    def _validate_ffmpeg_on_init(self):
        try:
            validate_ffmpeg(required=False)
        except RuntimeError:
            logger.warning("FFmpeg not available - audio extraction disabled")

    def prepare_download(self, url, output_path=None, format_id=None, only_audio=False, priority=Priority.NORMAL):
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
        url,
        output_path=None,
        format_id=None,
        only_audio=False,
        priority=Priority.NORMAL,
        quality=None,
        hdr=False,
        dolby=False,
        audio_format=None,
        audio_quality=None,
        audio_selector=None,
        subtitles=None,
        sponsorblock=None,
        output_template=None,
    ):
        url = normalize_url(url)
        output = validate_output_path(output_path or self.config.get("output_path", "./downloads"))
        cfg = self._build_download_config()
        cfg["format_id"] = format_id
        cfg["only_audio"] = only_audio
        cfg["hdr"] = hdr
        cfg["dolby"] = dolby
        if audio_format:
            cfg["audio_format"] = audio_format
        if audio_quality:
            cfg["audio_quality"] = audio_quality
        if audio_selector:
            cfg["audio_selector"] = audio_selector
        if subtitles is not None:
            cfg["subtitles"] = subtitles
        if sponsorblock is not None:
            cfg["sponsorblock"] = sponsorblock
        if output_template:
            cfg["output_template"] = output_template
        if quality and quality != "best":
            height_map = {"8k": 4320, "4k": 2160, "1080p": 1080, "720p": 720, "480p": 480}
            target_h = height_map.get(quality)
            if target_h:
                cfg["format"] = f"bestvideo[height<={target_h}]+bestaudio/best[ext=m4a]/best"
        item = self.queue.add(
            url=url, priority=priority, format_id=format_id, only_audio=only_audio, output_path=str(output), config=cfg
        )
        logger.info(f"Queued: {url} (task_id={item.task_id})")
        return item

    def queue_batch(
        self,
        urls,
        output_path=None,
        format_id=None,
        only_audio=False,
        priority=Priority.NORMAL,
        quality=None,
        hdr=False,
        dolby=False,
        audio_format=None,
        audio_quality=None,
        audio_selector=None,
        subtitles=None,
        sponsorblock=None,
        output_template=None,
    ):
        items = []
        for url in urls:
            items.append(
                self.queue_download(
                    url,
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
                    subtitles=subtitles,
                    sponsorblock=sponsorblock,
                    output_template=output_template,
                )
            )
        return items

    def queue_from_file(self, filepath, **kwargs):
        try:
            urls = validate_batch_file(filepath)
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"Failed to read batch file: {e}")
            return []
        logger.info(f"Loaded {len(urls)} URLs from {filepath}")
        return self.queue_batch(urls, **kwargs)

    def execute(self):
        if self.queue.is_empty:
            logger.warning("Queue is empty, nothing to download")
            return
        max_workers = self.config.get("concurrent_workers", 3)
        self._executor = ConcurrentExecutor(
            queue=self.queue,
            max_workers=max_workers,
            progress_tracker=self.progress,
            on_item_complete=self._on_item_complete,
        )
        self._executor.start()

    def execute_async(self):
        if self.queue.is_empty:
            return
        max_workers = self.config.get("concurrent_workers", 3)
        self._executor = ConcurrentExecutor(
            queue=self.queue,
            max_workers=max_workers,
            progress_tracker=self.progress,
            on_item_complete=self._on_item_complete,
        )
        self._executor.start_async()

    def download_now(
        self,
        url,
        output_path=None,
        format_id=None,
        only_audio=False,
        quality=None,
        hdr=False,
        dolby=False,
        audio_format=None,
        audio_quality=None,
        audio_selector=None,
        progress_hook=None,
    ):
        url = normalize_url(url)
        output = validate_output_path(output_path or self.config.get("output_path", "./downloads"))
        cfg = self._build_download_config()
        cfg["format_id"] = format_id
        cfg["only_audio"] = only_audio
        cfg["hdr"] = hdr
        cfg["dolby"] = dolby
        if audio_format:
            cfg["audio_format"] = audio_format
        if audio_quality:
            cfg["audio_quality"] = audio_quality
        if audio_selector:
            cfg["audio_selector"] = audio_selector
        if quality and quality != "best" and not hdr and not dolby:
            height_map = {"8k": 4320, "4k": 2160, "1080p": 1080, "720p": 720, "480p": 480}
            target_h = height_map.get(quality)
            if target_h:
                cfg["format"] = f"bestvideo[height<={target_h}]+bestaudio/best[ext=m4a]/best"
        try:
            self.plugin_loader.fire_hook("on_download_start", url=url, config=cfg)
            result = download_single(
                url=url,
                output_path=str(output),
                format_id=format_id,
                only_audio=only_audio,
                config=cfg,
                progress_hook=progress_hook,
            )
            title = self._current_info.title if self._current_info else url
            if self._notifications_enabled(cfg):
                notify_download_complete(title, str(output))
            self.plugin_loader.fire_hook("on_download_complete", url=url, output_path=str(output))
            return result
        except Exception as e:
            logger.error(f"Download failed: {e}")
            if self._notifications_enabled(cfg):
                notify_download_failed(url, str(e))
            self.plugin_loader.fire_hook("on_download_error", url=url, error=str(e))
            raise

    def download_playlist(
        self,
        url,
        output_path=None,
        format_id=None,
        only_audio=False,
        quality=None,
        hdr=False,
        dolby=False,
        audio_format=None,
        audio_quality=None,
        audio_selector=None,
        subtitles=None,
        sponsorblock=None,
        output_template=None,
    ):
        url = normalize_url(url)
        output = validate_output_path(output_path or self.config.get("output_path", "./downloads"))
        try:
            info = get_video_info(
                url,
                cookies_file=self.config.get("cookies_file"),
                cookies_from_browser=self.config.get("cookies_from_browser"),
                proxy=self.config.get("proxy"),
            )
            self._current_info = info
            playlist_count = len(info.entries) if info.entries else 0
            cfg = self._build_download_config()
            cfg["format_id"] = format_id
            cfg["only_audio"] = only_audio
            cfg["hdr"] = hdr
            cfg["dolby"] = dolby
            if audio_format:
                cfg["audio_format"] = audio_format
            if audio_quality:
                cfg["audio_quality"] = audio_quality
            if audio_selector:
                cfg["audio_selector"] = audio_selector
            if subtitles is not None:
                cfg["subtitles"] = subtitles
            if sponsorblock is not None:
                cfg["sponsorblock"] = sponsorblock
            if output_template:
                cfg["output_template"] = output_template
            if quality and quality != "best":
                height_map = {"8k": 4320, "4k": 2160, "1080p": 1080, "720p": 720, "480p": 480}
                target_h = height_map.get(quality)
                if target_h:
                    cfg["format"] = f"bestvideo[height<={target_h}]+bestaudio/best[ext=m4a]/best"
            if only_audio:
                cfg["audio_format"] = self.config.get("audio_format", "mp3")
                cfg["audio_quality"] = self.config.get("audio_quality", "192")
            results = download_playlist(url=url, output_path=str(output), config=cfg, progress_tracker=self.progress)
            notify_playlist_complete(info.title, playlist_count)
            return results
        except Exception as e:
            logger.error(f"Playlist download failed: {e}")
            raise

    def stop(self):
        if self._executor:
            self._executor.stop()

    def get_status(self):
        return {
            "queue_size": self.queue.size,
            "pending": self.queue.pending_count,
            "active": self.queue.active_count,
            "completed": self.queue.completed_count,
            "failed": self.queue.failed_count,
            "progress": self.progress.get_overall_progress(),
            "executor_running": self._executor.is_running if self._executor else False,
        }

    def _on_item_complete(self, task_id, success, error=None):
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

    def _build_download_config(self):
        return {
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

    def _notifications_enabled(self, cfg=None):
        source = cfg if isinstance(cfg, dict) else self.config
        if source.get("no_notify") is True:
            return False
        if "notifications" in source:
            return bool(source.get("notifications"))
        general = source.get("general")
        if isinstance(general, dict) and "notifications" in general:
            return bool(general.get("notifications"))
        return True

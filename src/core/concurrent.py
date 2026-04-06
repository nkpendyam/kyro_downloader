"""Concurrent download executor with thread pool."""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from src.core.downloader import download_single
from src.core.progress import ProgressTracker
from src.utils.logger import get_logger
from src.utils.notifications import notify_download_complete, notify_download_failed

logger = get_logger(__name__)


class ConcurrentExecutor:
    def __init__(
        self,
        queue: Any,
        max_workers: int = 3,
        progress_tracker: ProgressTracker | None = None,
        on_item_complete: Any | None = None,
    ) -> None:
        self._queue = queue
        self._max_workers = max_workers
        self._progress = progress_tracker or ProgressTracker()
        self._on_complete = on_item_complete
        self._executor = None
        self._futures = {}
        self._running = False
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix="kyro-dl-worker")
        logger.info(f"Executor started with {self._max_workers} workers")
        try:
            futures_to_items = {}
            while not self._stop_event.is_set() and not self._queue.is_empty:
                item = self._queue.get_next()
                if item is None:
                    break
                future = self._executor.submit(self._process_item, item)
                with self._lock:
                    self._futures[item.task_id] = future
                    futures_to_items[future] = item
                if self._stop_event.is_set():
                    break
            for future in as_completed(futures_to_items):
                if self._stop_event.is_set():
                    break
                try:
                    future.result()
                except Exception as e:
                    item = futures_to_items[future]
                    logger.error(f"Worker error for {item.task_id}: {e}")
        finally:
            executor = self._executor
            if executor is not None:
                executor.shutdown(wait=True)
                self._executor = None
            self._running = False
            logger.info("Executor finished processing queue")

    def start_async(self) -> None:
        self._worker_thread = threading.Thread(target=self.start, daemon=True, name="kyro-dl-executor")
        self._worker_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._running = False
        with self._lock:
            for task_id, future in self._futures.items():
                if not future.done() and not future.running():
                    future.cancel()
                    self._queue.cancel(task_id)
                elif future.running():
                    item = self._queue.get_item(task_id)
                    if item:
                        item.cancel()
                        self._queue.cancel(task_id)
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None
        if hasattr(self, "_worker_thread") and self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=10)
        logger.info("Executor stopped")

    def _process_item(self, item: Any) -> None:
        task_id = item.task_id
        try:
            self._progress.add_task(task_id, filename=item.url)
            if item.is_cancelled():
                self._queue.complete(task_id, error="Download cancelled")
                self._progress.complete(task_id, error="Download cancelled")
                if self._on_complete:
                    self._on_complete(task_id, success=False, error="Download cancelled")
                return
            item.config = dict(item.config)
            item.config["cancel_event"] = item.get_cancel_event()
            download_single(
                url=item.url,
                output_path=item.output_path,
                format_id=item.format_id,
                only_audio=item.only_audio,
                config=item.config,
                progress_tracker=self._progress,
                task_id=task_id,
            )
            if not self._stop_event.is_set():
                self._queue.complete(task_id)
                notify_download_complete(item.url, item.output_path)
                if self._on_complete:
                    self._on_complete(task_id, success=True)
                logger.info(f"Download completed: {item.url}")
        except Exception as e:
            error_msg = str(e)
            self._queue.complete(task_id, error=error_msg)
            self._progress.complete(task_id, error=error_msg)
            notify_download_failed(item.url, error_msg)
            if self._on_complete:
                self._on_complete(task_id, success=False, error=error_msg)
            logger.error(f"Download failed: {item.url} - {error_msg}")

    def get_progress(self) -> dict[str, Any]:
        return self._progress.get_overall_progress()

    def get_task_progress(self, task_id: str) -> dict[str, Any] | None:
        task = self._progress.get_task(task_id)
        if task:
            return {
                "filename": task.filename,
                "percentage": task.percentage,
                "speed": task.speed,
                "eta": task.eta,
                "status": task.status,
            }
        return None

    def submit(self, item: Any) -> None:
        """Submit a queue item for processing."""
        if not self._executor:
            return
        future = self._executor.submit(self._process_item, item)
        with self._lock:
            self._futures[item.task_id] = future

    def get_status(self) -> dict[str, Any]:
        """Return executor runtime status snapshot."""
        return {
            "running": self._running,
            "active_downloads": self.active_downloads,
            "max_workers": self._max_workers,
        }

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def active_downloads(self) -> int:
        with self._lock:
            return sum(1 for f in self._futures.values() if f.running())

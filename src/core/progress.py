"""Progress tracking for downloads."""

import asyncio
import threading
import time
from dataclasses import dataclass
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)
_dropped_broadcasts = 0
_MAX_DROPPED_COUNTER = 10000


def get_dropped_broadcasts() -> int:
    """Return and reset the dropped broadcasts counter."""
    global _dropped_broadcasts
    count = _dropped_broadcasts
    _dropped_broadcasts = 0
    return count


try:
    from src.ui.web import websocket as websocket_module
except ImportError:  # pragma: no cover - fallback for minimal installs

    class _WebsocketFallback:
        @staticmethod
        async def broadcast_progress(_task_id: str, _progress_data: dict[str, float | str]) -> None:
            return

        @staticmethod
        def get_event_loop():
            return None

    websocket_module = _WebsocketFallback()


@dataclass
class ProgressInfo:
    filename: str = ""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0
    eta: float = 0.0
    percentage: float = 0.0
    status: str = "pending"
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def is_complete(self) -> bool:
        return self.status in ("finished", "completed", "error")

    @property
    def duration(self) -> float:
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        if self.started_at:
            return time.time() - self.started_at
        return 0.0


class ProgressTracker:
    def __init__(self, max_tasks: int = 5000) -> None:
        self._tasks: dict[str, ProgressInfo] = {}
        self._task_order: list[str] = []
        self._callbacks: list[Any] = []
        self._max_tasks = max(1, int(max_tasks))
        self._lock = threading.Lock()

    def _prune_tasks_locked(self) -> None:
        while len(self._tasks) > self._max_tasks:
            remove_task_id = None
            for task_id in self._task_order:
                task = self._tasks.get(task_id)
                if task and task.is_complete:
                    remove_task_id = task_id
                    break
            if remove_task_id is None and self._task_order:
                remove_task_id = self._task_order[0]
            if remove_task_id is None:
                break
            self._tasks.pop(remove_task_id, None)
            try:
                self._task_order.remove(remove_task_id)
            except ValueError:
                pass

    def add_task(self, task_id: str, filename: str = "", total_bytes: int = 0) -> None:
        with self._lock:
            self._tasks[task_id] = ProgressInfo(
                filename=filename,
                total_bytes=total_bytes,
                started_at=time.time(),
                status="downloading",
            )
            if task_id in self._task_order:
                self._task_order.remove(task_id)
            self._task_order.append(task_id)
            self._prune_tasks_locked()

    def update(self, task_id: str, **kwargs: Any) -> None:
        callbacks_to_call: list[Any] = []
        broadcast_data: dict[str, float | str] | None = None
        task: ProgressInfo | None = None
        with self._lock:
            if task_id not in self._tasks:
                return
            task = self._tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            if task.downloaded_bytes > 0 and task.total_bytes > 0:
                task.percentage = (task.downloaded_bytes / task.total_bytes) * 100
            if task.downloaded_bytes > 0 and task.started_at > 0:
                elapsed = time.time() - task.started_at
                if elapsed > 0:
                    task.speed = task.downloaded_bytes / elapsed
                    remaining = task.total_bytes - task.downloaded_bytes
                    task.eta = remaining / task.speed if task.speed > 0 else 0
            callbacks_to_call = list(self._callbacks)
            broadcast_data = {
                "percentage": task.percentage,
                "speed": task.speed,
                "eta": task.eta,
                "status": task.status,
                "filename": task.filename,
            }
        for callback in callbacks_to_call:
            try:
                callback(task_id, task)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
        if broadcast_data:
            try:
                loop = websocket_module.get_event_loop()
                if not loop or not loop.is_running():
                    global _dropped_broadcasts
                    _dropped_broadcasts = (_dropped_broadcasts + 1) % _MAX_DROPPED_COUNTER
                    if _dropped_broadcasts % 100 == 1:
                        logger.debug("Dropping progress broadcast: no active websocket event loop")
                    return
                asyncio.run_coroutine_threadsafe(websocket_module.broadcast_progress(task_id, broadcast_data), loop)
            except Exception as e:
                logger.debug(f"WebSocket broadcast failed: {e}")

    def complete(self, task_id: str, error: str | None = None) -> None:
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.completed_at = time.time()
                task.status = "error" if error else "completed"
                if error:
                    logger.error(f"Task {task_id} failed: {error}")
                self._prune_tasks_locked()

    def get_task(self, task_id: str) -> ProgressInfo | None:
        with self._lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> dict[str, ProgressInfo]:
        with self._lock:
            return dict(self._tasks)

    def add_callback(self, callback: Any) -> None:
        self._callbacks.append(callback)

    def remove_callback(self, callback: Any) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_overall_progress(self) -> dict[str, int | float]:
        with self._lock:
            tasks = list(self._tasks.values())
        if not tasks:
            return {"percentage": 0, "total": 0, "completed": 0, "active": 0}
        total_bytes = sum(t.total_bytes for t in tasks)
        downloaded_bytes = sum(t.downloaded_bytes for t in tasks)
        completed = sum(1 for t in tasks if t.status == "completed")
        active = sum(1 for t in tasks if t.status == "downloading")
        return {
            "percentage": (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0,
            "total_bytes": total_bytes,
            "downloaded_bytes": downloaded_bytes,
            "total_tasks": len(tasks),
            "completed": completed,
            "active": active,
            "failed": sum(1 for t in tasks if t.status == "error"),
        }


def create_progress_hook(tracker: ProgressTracker, task_id: str):
    def hook(d: dict[str, Any]) -> None:
        if d["status"] == "downloading":
            tracker.update(
                task_id,
                downloaded_bytes=d.get("downloaded_bytes", 0),
                total_bytes=d.get("total_bytes") or d.get("total_bytes_estimate", 0),
                speed=d.get("speed", 0),
                eta=d.get("eta", 0),
                status="downloading",
            )
        elif d["status"] == "finished":
            tracker.complete(task_id)
        elif d["status"] == "error":
            tracker.complete(task_id, error=d.get("error", "Unknown error"))

    return hook

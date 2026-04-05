"""Progress tracking for downloads."""
import time
import threading
from dataclasses import dataclass
from src.utils.logger import get_logger
logger = get_logger(__name__)

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
    def is_complete(self): return self.status in ("finished", "completed", "error")
    @property
    def duration(self):
        if self.completed_at and self.started_at: return self.completed_at - self.started_at
        if self.started_at: return time.time() - self.started_at
        return 0.0

class ProgressTracker:
    def __init__(self):
        self._tasks = {}
        self._callbacks = []
        self._lock = threading.Lock()

    def add_task(self, task_id, filename="", total_bytes=0):
        with self._lock:
            self._tasks[task_id] = ProgressInfo(filename=filename, total_bytes=total_bytes, started_at=time.time(), status="downloading")

    def update(self, task_id, **kwargs):
        callbacks_to_call = []
        broadcast_data = None
        with self._lock:
            if task_id not in self._tasks: return
            task = self._tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key): setattr(task, key, value)
            if task.downloaded_bytes > 0 and task.total_bytes > 0:
                task.percentage = (task.downloaded_bytes / task.total_bytes) * 100
            if task.downloaded_bytes > 0 and task.started_at > 0:
                elapsed = time.time() - task.started_at
                if elapsed > 0:
                    task.speed = task.downloaded_bytes / elapsed
                    remaining = task.total_bytes - task.downloaded_bytes
                    task.eta = remaining / task.speed if task.speed > 0 else 0
            callbacks_to_call = list(self._callbacks)
            broadcast_data = {"percentage": task.percentage, "speed": task.speed, "eta": task.eta, "status": task.status, "filename": task.filename}
        for callback in callbacks_to_call:
            try: callback(task_id, task)
            except Exception as e: logger.warning(f"Progress callback error: {e}")
        if broadcast_data:
            try:
                from src.ui.web.websocket import broadcast_progress
                import asyncio
                try: loop = asyncio.get_running_loop()
                except RuntimeError: return
                asyncio.run_coroutine_threadsafe(broadcast_progress(task_id, broadcast_data), loop)
            except Exception as e:
                logger.debug(f"WebSocket broadcast failed: {e}")

    def complete(self, task_id, error=None):
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.completed_at = time.time()
                task.status = "error" if error else "completed"
                if error: logger.error(f"Task {task_id} failed: {error}")

    def get_task(self, task_id):
        return self._tasks.get(task_id)

    def get_all_tasks(self):
        return dict(self._tasks)

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def remove_callback(self, callback):
        if callback in self._callbacks: self._callbacks.remove(callback)

    def get_overall_progress(self):
        tasks = list(self._tasks.values())
        if not tasks: return {"percentage": 0, "total": 0, "completed": 0, "active": 0}
        total_bytes = sum(t.total_bytes for t in tasks)
        downloaded_bytes = sum(t.downloaded_bytes for t in tasks)
        completed = sum(1 for t in tasks if t.status == "completed")
        active = sum(1 for t in tasks if t.status == "downloading")
        return {"percentage": (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0, "total_bytes": total_bytes, "downloaded_bytes": downloaded_bytes, "total_tasks": len(tasks), "completed": completed, "active": active, "failed": sum(1 for t in tasks if t.status == "error")}

def create_progress_hook(tracker, task_id):
    def hook(d):
        if d["status"] == "downloading":
            tracker.update(task_id, downloaded_bytes=d.get("downloaded_bytes", 0), total_bytes=d.get("total_bytes") or d.get("total_bytes_estimate", 0), speed=d.get("speed", 0), eta=d.get("eta", 0), status="downloading")
        elif d["status"] == "finished":
            tracker.complete(task_id)
        elif d["status"] == "error":
            tracker.complete(task_id, error=d.get("error", "Unknown error"))
    return hook

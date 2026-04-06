"""Download queue with pause, resume, reorder, and priority support."""

import uuid
import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QueueStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class QueueItem:
    url: str
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: QueueStatus = QueueStatus.PENDING
    priority: Priority = Priority.NORMAL
    format_id: str | None = None
    only_audio: bool = False
    output_path: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: time.time())
    started_at: float = 0.0
    completed_at: float = 0.0
    error_message: str | None = None
    retries: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    _cancel_event: threading.Event = field(default_factory=threading.Event, repr=False, compare=False)

    def __lt__(self, other: "QueueItem") -> bool:
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at

    def cancel(self) -> bool:
        """Cancel this item and set cancellation event."""
        if self.status in (QueueStatus.COMPLETED, QueueStatus.CANCELLED):
            return False
        self.status = QueueStatus.CANCELLED
        self._cancel_event.set()
        return True

    def pause(self) -> bool:
        """Pause this item and set cancellation event."""
        if self.status not in (QueueStatus.PENDING, QueueStatus.DOWNLOADING):
            return False
        self.status = QueueStatus.PAUSED
        self._cancel_event.set()
        return True

    def resume(self) -> bool:
        """Resume this item and clear cancellation event."""
        if self.status != QueueStatus.PAUSED:
            return False
        self.status = QueueStatus.PENDING
        self._cancel_event.clear()
        return True

    def get_status(self) -> QueueStatus:
        """Return current queue status for this item."""
        return self.status

    def is_cancelled(self) -> bool:
        """Return whether cancellation was requested."""
        return self._cancel_event.is_set()

    def get_cancel_event(self) -> threading.Event:
        """Expose cancellation event for cooperative cancellation."""
        return self._cancel_event


class DownloadQueue:
    def __init__(self, max_size=1000):
        self._items = []
        self._lock = threading.Lock()
        self._max_size = max_size
        self._history = []

    def add(
        self,
        url,
        priority=Priority.NORMAL,
        format_id=None,
        only_audio=False,
        output_path="",
        config=None,
        metadata=None,
    ):
        with self._lock:
            if len(self._items) >= self._max_size:
                raise ValueError(f"Queue is full (max {self._max_size})")
            item = QueueItem(
                url=url,
                priority=priority,
                format_id=format_id,
                only_audio=only_audio,
                output_path=output_path,
                config=config or {},
                metadata=metadata or {},
            )
            self._items.append(item)
            self._items.sort()
            logger.info(f"Added to queue: {url} (priority={priority.name})")
            return item

    def add_batch(self, urls, **kwargs):
        results = []
        with self._lock:
            for url in urls:
                if len(self._items) >= self._max_size:
                    break
                item = QueueItem(
                    url=url,
                    priority=kwargs.get("priority", Priority.NORMAL),
                    format_id=kwargs.get("format_id"),
                    only_audio=kwargs.get("only_audio", False),
                    output_path=kwargs.get("output_path", ""),
                    config=kwargs.get("config", {}),
                    metadata=kwargs.get("metadata", {}),
                )
                self._items.append(item)
                self._items.sort()
                results.append(item)
                logger.info(f"Added to queue: {url} (priority={item.priority.name})")
        return results

    def get_next(self):
        with self._lock:
            for item in self._items:
                if item.status == QueueStatus.PENDING:
                    item.status = QueueStatus.DOWNLOADING
                    item.started_at = time.time()
                    return item
            return None

    def pause(self, task_id):
        with self._lock:
            for item in self._items:
                if item.task_id == task_id and item.status in (QueueStatus.PENDING, QueueStatus.DOWNLOADING):
                    item.pause()
                    logger.info(f"Paused: {task_id}")
                    return True
        return False

    def resume(self, task_id):
        with self._lock:
            for item in self._items:
                if item.task_id == task_id and item.status == QueueStatus.PAUSED:
                    item.resume()
                    logger.info(f"Resumed: {task_id}")
                    return True
        return False

    def cancel(self, task_id):
        with self._lock:
            for item in self._items:
                if item.task_id == task_id and item.status not in (QueueStatus.COMPLETED, QueueStatus.CANCELLED):
                    item.cancel()
                    logger.info(f"Cancelled: {task_id}")
                    return True
        return False

    def remove(self, task_id):
        with self._lock:
            for i, item in enumerate(self._items):
                if item.task_id == task_id:
                    self._items.pop(i)
                    return True
        return False

    def reorder(self, task_id, new_position):
        with self._lock:
            for i, item in enumerate(self._items):
                if item.task_id == task_id:
                    self._items.pop(i)
                    new_pos = max(0, min(int(new_position), len(self._items)))
                    self._items.insert(new_pos, item)
                    return True
        return False

    def complete(self, task_id, error=None):
        with self._lock:
            for item in self._items:
                if item.task_id == task_id:
                    item.completed_at = time.time()
                    if error:
                        item.status = QueueStatus.FAILED
                        item.error_message = error
                    else:
                        item.status = QueueStatus.COMPLETED
                    self._history.append(item)
                    break

    def get_item(self, task_id):
        with self._lock:
            for item in self._items:
                if item.task_id == task_id:
                    return item
            for item in self._history:
                if item.task_id == task_id:
                    return item
        return None

    def get_all_items(self):
        with self._lock:
            return list(self._items)

    def get_history(self):
        with self._lock:
            return list(self._history)

    def clear_completed(self):
        with self._lock:
            before = len(self._items)
            self._items = [
                i
                for i in self._items
                if i.status not in (QueueStatus.COMPLETED, QueueStatus.FAILED, QueueStatus.CANCELLED)
            ]
            return before - len(self._items)

    def clear_all(self):
        with self._lock:
            self._items.clear()
            self._history.clear()

    @property
    def pending_count(self):
        with self._lock:
            return sum(1 for i in self._items if i.status == QueueStatus.PENDING)

    @property
    def active_count(self):
        with self._lock:
            return sum(1 for i in self._items if i.status == QueueStatus.DOWNLOADING)

    @property
    def completed_count(self):
        with self._lock:
            return sum(1 for i in self._history if i.status == QueueStatus.COMPLETED)

    @property
    def failed_count(self):
        with self._lock:
            return sum(1 for i in self._history if i.status == QueueStatus.FAILED)

    @property
    def size(self):
        with self._lock:
            return len(self._items)

    @property
    def is_empty(self):
        with self._lock:
            return len(self._items) == 0

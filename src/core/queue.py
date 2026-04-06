"""Download queue with pause, resume, reorder, and priority support."""

import uuid
import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

_PERSIST_CONFIG_EXCLUDE = {
    "proxy",
    "cookies_file",
    "cookies_from_browser",
    "token",
    "api_token",
    "password",
    "secret",
    "credentials_file",
}


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
    """Represents a single item in the download queue."""

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
    _paused_event: threading.Event = field(default_factory=threading.Event, repr=False, compare=False)

    def __lt__(self, other: "QueueItem") -> bool:
        """Order by priority (higher first), then by creation time (earlier first)."""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at

    def __eq__(self, other: object) -> bool:
        """Equality based on task_id."""
        if not isinstance(other, QueueItem):
            return NotImplemented
        return self.task_id == other.task_id

    def __hash__(self) -> int:
        """Hash based on task_id."""
        return hash(self.task_id)

    def cancel(self) -> bool:
        """Cancel this item and set cancellation event."""
        if self.status in (QueueStatus.COMPLETED, QueueStatus.CANCELLED):
            return False
        self.status = QueueStatus.CANCELLED
        self._cancel_event.set()
        return True

    def pause(self) -> bool:
        """Pause this item without triggering cancellation."""
        if self.status not in (QueueStatus.PENDING, QueueStatus.DOWNLOADING):
            return False
        self.status = QueueStatus.PAUSED
        self._paused_event.set()
        return True

    def resume(self) -> bool:
        """Resume this item and clear pause signal."""
        if self.status != QueueStatus.PAUSED:
            return False
        self.status = QueueStatus.PENDING
        self._paused_event.clear()
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

    def is_paused(self) -> bool:
        """Return whether this item is currently paused."""
        return self._paused_event.is_set()

    def get_paused_event(self) -> threading.Event:
        """Expose pause event for cooperative pause handling."""
        return self._paused_event

    def to_persisted_dict(self) -> dict[str, Any]:
        """Serialize queue item into a persistence-safe mapping."""
        persisted_config = {key: value for key, value in self.config.items() if key not in _PERSIST_CONFIG_EXCLUDE}
        status = self.status
        if status == QueueStatus.DOWNLOADING:
            status = QueueStatus.PENDING
        return {
            "task_id": self.task_id,
            "url": self.url,
            "status": status.value,
            "priority": self.priority.name,
            "format_id": self.format_id,
            "only_audio": self.only_audio,
            "output_path": self.output_path,
            "config": persisted_config,
            "created_at": self.created_at,
            "retries": self.retries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_persisted_dict(cls, data: dict[str, Any]) -> "QueueItem":
        """Create queue item from persisted mapping."""
        priority_name = str(data.get("priority", "NORMAL"))
        try:
            priority = Priority[priority_name]
        except KeyError:
            priority = Priority.NORMAL
        item = cls(
            task_id=str(data.get("task_id") or str(uuid.uuid4())),
            url=str(data.get("url", "")),
            priority=priority,
            format_id=data.get("format_id"),
            only_audio=bool(data.get("only_audio", False)),
            output_path=str(data.get("output_path", "")),
            config=dict(data.get("config") or {}),
            created_at=float(data.get("created_at", time.time())),
            retries=int(data.get("retries", 0)),
            metadata=dict(data.get("metadata") or {}),
        )
        status_value = str(data.get("status", QueueStatus.PENDING.value))
        try:
            item.status = QueueStatus(status_value)
        except ValueError:
            item.status = QueueStatus.PENDING
        if item.status == QueueStatus.PAUSED:
            item._paused_event.set()
        return item


class DownloadQueue:
    """Thread-safe download queue with priority, pause, resume, and persistence support."""

    def __init__(self, max_size: int = 1000, on_change: Any | None = None, max_history: int = 5000) -> None:
        self._items: list[QueueItem] = []
        self._lock = threading.RLock()
        self._max_size = max_size
        self._history: list[QueueItem] = []
        self._max_history = max(1, int(max_history))
        self._completed_total = 0
        self._failed_total = 0
        self._on_change = on_change

    def _trim_history_locked(self) -> None:
        excess = len(self._history) - self._max_history
        if excess > 0:
            del self._history[:excess]

    def _notify_change(self) -> None:
        if self._on_change is None:
            return
        try:
            self._on_change()
        except Exception as e:
            logger.debug(f"Queue change callback failed: {e}")

    def add(
        self,
        url: str,
        priority: Priority = Priority.NORMAL,
        format_id: str | None = None,
        only_audio: bool = False,
        output_path: str = "",
        config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> QueueItem:
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
            self._notify_change()
            return item

    def add_batch(self, urls: list[str], **kwargs: Any) -> list[QueueItem]:
        results: list[QueueItem] = []
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
            if results:
                self._notify_change()
        return results

    def get_next(self) -> QueueItem | None:
        with self._lock:
            for item in self._items:
                if item.status == QueueStatus.PENDING:
                    item.status = QueueStatus.DOWNLOADING
                    item.started_at = time.time()
                    return item
            return None

    def pause(self, task_id: str) -> bool:
        with self._lock:
            for item in self._items:
                if item.task_id == task_id and item.status in (QueueStatus.PENDING, QueueStatus.DOWNLOADING):
                    item.pause()
                    logger.info(f"Paused: {task_id}")
                    self._notify_change()
                    return True
        return False

    def resume(self, task_id: str) -> bool:
        with self._lock:
            for item in self._items:
                if item.task_id == task_id and item.status == QueueStatus.PAUSED:
                    item.resume()
                    logger.info(f"Resumed: {task_id}")
                    self._notify_change()
                    return True
        return False

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            for item in self._items:
                if item.task_id == task_id and item.status not in (QueueStatus.COMPLETED, QueueStatus.CANCELLED):
                    item.cancel()
                    logger.info(f"Cancelled: {task_id}")
                    self._notify_change()
                    return True
        return False

    def remove(self, task_id: str) -> bool:
        with self._lock:
            for i, item in enumerate(self._items):
                if item.task_id == task_id:
                    self._items.pop(i)
                    self._notify_change()
                    return True
        return False

    def reorder(self, task_id: str, new_position: int) -> bool:
        with self._lock:
            for i, item in enumerate(self._items):
                if item.task_id == task_id:
                    self._items.pop(i)
                    new_pos = max(0, min(int(new_position), len(self._items)))
                    self._items.insert(new_pos, item)
                    self._notify_change()
                    return True
        return False

    def complete(self, task_id: str, error: str | None = None) -> None:
        with self._lock:
            for item in self._items:
                if item.task_id == task_id:
                    if item.status in (QueueStatus.COMPLETED, QueueStatus.FAILED):
                        return
                    item.completed_at = time.time()
                    if error:
                        item.status = QueueStatus.FAILED
                        item.error_message = error
                        self._failed_total += 1
                    else:
                        item.status = QueueStatus.COMPLETED
                        self._completed_total += 1
                    self._history.append(item)
                    self._trim_history_locked()
                    self._notify_change()
                    break

    def get_item(self, task_id: str) -> QueueItem | None:
        with self._lock:
            for item in self._items:
                if item.task_id == task_id:
                    return item
            for item in self._history:
                if item.task_id == task_id:
                    return item
        return None

    def get_all_items(self) -> list[QueueItem]:
        with self._lock:
            return list(self._items)

    def get_history(self) -> list[QueueItem]:
        with self._lock:
            return list(self._history)

    def clear_completed(self) -> int:
        with self._lock:
            before = len(self._items)
            self._items = [
                i
                for i in self._items
                if i.status not in (QueueStatus.COMPLETED, QueueStatus.FAILED, QueueStatus.CANCELLED)
            ]
            if before != len(self._items):
                self._notify_change()
            return before - len(self._items)

    def clear_all(self) -> None:
        with self._lock:
            self._items.clear()
            self._history.clear()
            self._completed_total = 0
            self._failed_total = 0
            self._notify_change()

    def export_state(self) -> dict[str, Any]:
        """Export queue persistence snapshot for incomplete tasks."""
        with self._lock:
            items = []
            for item in self._items:
                if item.status in (QueueStatus.PENDING, QueueStatus.PAUSED, QueueStatus.DOWNLOADING):
                    items.append(item.to_persisted_dict())
            return {"version": 1, "items": items}

    def import_state(self, data: dict[str, Any]) -> int:
        """Import queue state snapshot and return number of restored items."""
        raw_items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(raw_items, list):
            return 0
        existing_ids: set[str] = set()
        with self._lock:
            existing_ids = {item.task_id for item in self._items}
            existing_ids.update(item.task_id for item in self._history)
        restored_count = 0
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            task_id = str(raw_item.get("task_id", ""))
            if task_id in existing_ids:
                continue
            item = QueueItem.from_persisted_dict(raw_item)
            if item.status not in (QueueStatus.PENDING, QueueStatus.PAUSED):
                item.status = QueueStatus.PENDING
            with self._lock:
                self._items.append(item)
            existing_ids.add(task_id)
            restored_count += 1
        if restored_count > 0:
            with self._lock:
                self._items.sort()
            self._notify_change()
        return restored_count

    @property
    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for i in self._items if i.status == QueueStatus.PENDING)

    @property
    def active_count(self) -> int:
        with self._lock:
            return sum(1 for i in self._items if i.status == QueueStatus.DOWNLOADING)

    @property
    def completed_count(self) -> int:
        with self._lock:
            return self._completed_total

    @property
    def failed_count(self) -> int:
        with self._lock:
            return self._failed_total

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._items)

    @property
    def is_empty(self) -> bool:
        with self._lock:
            return len(self._items) == 0

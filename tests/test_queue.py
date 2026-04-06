"""Tests for download queue module."""

from src.core.queue import DownloadQueue, Priority, QueueItem


class TestQueueItem:
    def test_item_creation(self):
        item = QueueItem(url="https://example.com", priority=Priority.NORMAL)
        assert item.url == "https://example.com"
        assert item.priority == Priority.NORMAL
        assert item.status.value == "pending"
        assert item.task_id is not None

    def test_high_priority_item(self):
        item = QueueItem(url="https://example.com", priority=Priority.HIGH)
        assert item.priority == Priority.HIGH

    def test_item_with_config(self):
        config = {"audio_format": "mp3"}
        item = QueueItem(url="https://example.com", config=config)
        assert item.config == config


class TestDownloadQueue:
    def test_add_item(self):
        queue = DownloadQueue()
        item = queue.add(url="https://example.com")
        assert queue.size == 1
        assert item.url == "https://example.com"

    def test_get_next_returns_highest_priority(self):
        queue = DownloadQueue()
        queue.add(url="https://low.com", priority=Priority.LOW)
        high = queue.add(url="https://high.com", priority=Priority.HIGH)
        queue.add(url="https://normal.com", priority=Priority.NORMAL)

        next_item = queue.get_next()
        assert next_item.task_id == high.task_id

    def test_is_empty(self):
        queue = DownloadQueue()
        assert queue.is_empty is True
        queue.add(url="https://example.com")
        assert queue.is_empty is False

    def test_complete_item(self):
        queue = DownloadQueue()
        item = queue.add(url="https://example.com")
        queue.get_next()
        queue.complete(item.task_id)
        assert queue.completed_count == 1

    def test_cancel_item(self):
        queue = DownloadQueue()
        item = queue.add(url="https://example.com")
        queue.cancel(item.task_id)
        assert item.status.value == "cancelled"
        assert item._cancel_event.is_set() is True

    def test_pause_resume_uses_pause_event(self):
        queue = DownloadQueue()
        item = queue.add(url="https://example.com")
        assert queue.pause(item.task_id) is True
        assert item._paused_event.is_set() is True
        assert item._cancel_event.is_set() is False
        assert queue.resume(item.task_id) is True
        assert item._paused_event.is_set() is False

    def test_pending_count(self):
        queue = DownloadQueue()
        queue.add(url="https://one.com")
        queue.add(url="https://two.com")
        assert queue.pending_count == 2

    def test_active_count(self):
        queue = DownloadQueue()
        queue.add(url="https://example.com")
        queue.get_next()
        assert queue.active_count == 1

    def test_get_all_items(self):
        queue = DownloadQueue()
        queue.add(url="https://one.com")
        queue.add(url="https://two.com")
        items = queue.get_all_items()
        assert len(items) == 2

    def test_clear_completed(self):
        queue = DownloadQueue()
        item = queue.add(url="https://example.com")
        queue.get_next()
        queue.complete(item.task_id)
        assert queue.completed_count == 1
        queue.clear_completed()
        assert queue.size == 0

    def test_get_item_by_id(self):
        queue = DownloadQueue()
        item = queue.add(url="https://example.com")
        found = queue.get_item(item.task_id)
        assert found is not None
        assert found.task_id == item.task_id

    def test_get_nonexistent_item(self):
        queue = DownloadQueue()
        found = queue.get_item("nonexistent")
        assert found is None

    def test_export_state_contains_only_incomplete_items(self):
        queue = DownloadQueue()
        queue.add(url="https://pending.com")
        active = queue.add(url="https://active.com")
        queue.get_next()
        queue.complete(active.task_id)
        state = queue.export_state()
        urls = {item["url"] for item in state["items"]}
        assert "https://pending.com" in urls
        assert "https://active.com" not in urls

    def test_import_state_restores_pause_and_priority(self):
        queue = DownloadQueue()
        data = {
            "version": 1,
            "items": [
                {
                    "task_id": "task-1",
                    "url": "https://example.com/one",
                    "status": "paused",
                    "priority": "HIGH",
                    "format_id": None,
                    "only_audio": False,
                    "output_path": "downloads",
                    "config": {"audio_format": "mp3"},
                    "created_at": 1.0,
                    "retries": 0,
                    "metadata": {},
                }
            ],
        }
        restored = queue.import_state(data)
        assert restored == 1
        item = queue.get_item("task-1")
        assert item is not None
        assert item.status.value == "paused"
        assert item.priority == Priority.HIGH

    def test_history_is_bounded_while_totals_remain_accurate(self):
        queue = DownloadQueue(max_history=2)
        items = [queue.add(url=f"https://example.com/{i}") for i in range(4)]
        for item in items:
            queue.get_next()
            queue.complete(item.task_id)

        history = queue.get_history()
        assert len(history) == 2
        assert queue.completed_count == 4

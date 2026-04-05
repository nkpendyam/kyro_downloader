"""Tests for concurrent module."""
from unittest.mock import MagicMock
from src.core.concurrent import ConcurrentExecutor
from src.core.queue import DownloadQueue


class TestConcurrentExecutor:
    def test_init(self):
        queue = DownloadQueue()
        executor = ConcurrentExecutor(queue=queue, max_workers=2)
        assert executor._max_workers == 2
        assert not executor.is_running

    def test_start_empty_queue(self):
        queue = DownloadQueue()
        executor = ConcurrentExecutor(queue=queue, max_workers=2)
        executor.start()
        assert not executor.is_running

    def test_start_already_running(self):
        queue = DownloadQueue()
        executor = ConcurrentExecutor(queue=queue, max_workers=2)
        executor._running = True
        executor.start()  # Should return immediately

    def test_stop(self):
        queue = DownloadQueue()
        executor = ConcurrentExecutor(queue=queue, max_workers=2)
        executor.stop()
        assert not executor.is_running

    def test_on_item_complete_callback(self):
        queue = DownloadQueue()
        callback = MagicMock()
        executor = ConcurrentExecutor(queue=queue, max_workers=2, on_item_complete=callback)
        executor._on_complete("task1", True)
        callback.assert_called_once()

    def test_on_item_complete_error_callback(self):
        queue = DownloadQueue()
        callback = MagicMock()
        executor = ConcurrentExecutor(queue=queue, max_workers=2, on_item_complete=callback)
        executor._on_complete("task1", False, error="error msg")
        callback.assert_called_once()

    def test_get_progress(self):
        queue = DownloadQueue()
        executor = ConcurrentExecutor(queue=queue, max_workers=2)
        progress = executor.get_progress()
        assert "percentage" in progress

    def test_get_task_progress(self):
        queue = DownloadQueue()
        executor = ConcurrentExecutor(queue=queue, max_workers=2)
        result = executor.get_task_progress("nonexistent")
        assert result is None

    def test_active_downloads(self):
        queue = DownloadQueue()
        executor = ConcurrentExecutor(queue=queue, max_workers=2)
        assert executor.active_downloads == 0

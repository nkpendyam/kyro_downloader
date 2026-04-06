"""Tests for concurrent module."""

import threading
import time
from unittest.mock import MagicMock

from src.core import concurrent as concurrent_module
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

    def test_cancel_in_progress_item_stops_worker(self, monkeypatch):
        queue = DownloadQueue()
        executor = ConcurrentExecutor(queue=queue, max_workers=1)
        callback = MagicMock()
        executor._on_complete = callback

        item = queue.add(url="https://example.com/long", output_path="./downloads")
        item = queue.get_next()
        assert item is not None

        def _fake_download_single(**kwargs):
            cancel_event = kwargs["config"].get("cancel_event")
            for _ in range(50):
                if cancel_event and cancel_event.is_set():
                    raise Exception("Download cancelled")
                time.sleep(0.01)
            return []

        monkeypatch.setattr(concurrent_module, "download_single", _fake_download_single)

        worker = threading.Thread(target=executor._process_item, args=(item,))
        worker.start()
        time.sleep(0.05)
        queue.cancel(item.task_id)
        worker.join(timeout=3)

        assert worker.is_alive() is False
        assert item._cancel_event.is_set() is True
        assert callback.called is True

    def test_stop_mid_execution_is_idempotent(self, monkeypatch):
        queue = DownloadQueue()
        executor = ConcurrentExecutor(queue=queue, max_workers=2)

        for idx in range(3):
            queue.add(url=f"https://example.com/video-{idx}", output_path="./downloads")

        def _slow_download_single(**kwargs):
            cancel_event = kwargs["config"].get("cancel_event")
            for _ in range(100):
                if cancel_event and cancel_event.is_set():
                    raise Exception("Download cancelled")
                time.sleep(0.01)
            return []

        monkeypatch.setattr(concurrent_module, "download_single", _slow_download_single)

        executor.start_async()
        time.sleep(0.05)
        executor.stop()
        executor.stop()

        assert executor.is_running is False
        assert executor._worker_thread is not None
        assert executor._worker_thread.is_alive() is False

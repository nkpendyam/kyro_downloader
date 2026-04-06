"""Load/stress tests for concurrent downloads.

Marked with @pytest.mark.stress for optional skipping in CI.
"""

from __future__ import annotations

import threading
import time

import pytest

pytestmark = pytest.mark.stress

from src.core.queue import DownloadQueue, QueueItem
from src.core.concurrent import ConcurrentExecutor
from src.core.progress import ProgressTracker
from typing import Any


class TestConcurrentQueueStress:
    def test_rapid_queue_additions_no_items_lost(self):
        queue = DownloadQueue(max_size=1000)
        results = []
        lock = threading.Lock()

        def add_batch(start: int, count: int) -> None:
            local_results = []
            for i in range(count):
                item = queue.add(url=f"https://example.com/video-{start + i}")
                local_results.append(item.task_id)
            with lock:
                results.extend(local_results)

        threads = []
        batch_size = 20
        num_threads = 5
        for t in range(num_threads):
            thread = threading.Thread(target=add_batch, args=(t * batch_size, batch_size))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=10)

        assert queue.size == num_threads * batch_size
        assert len(results) == num_threads * batch_size

    def test_queue_with_50_items_all_processed(self):
        queue = DownloadQueue(max_size=200)
        for i in range(50):
            queue.add(url=f"https://example.com/video-{i}")

        assert queue.size == 50
        processed = 0
        while True:
            item = queue.get_next()
            if item is None:
                break
            queue.complete(item.task_id)
            processed += 1

        assert processed == 50
        assert queue.size == 50
        assert queue.completed_count == 50

    def test_concurrent_pause_resume_cancel_operations(self):
        queue = DownloadQueue(max_size=200)
        items = []
        for i in range(20):
            items.append(queue.add(url=f"https://example.com/video-{i}"))

        errors = []

        def do_operations(item_list: list[QueueItem]) -> None:
            try:
                for item in item_list:
                    queue.pause(item.task_id)
                    queue.resume(item.task_id)
                    queue.cancel(item.task_id)
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=do_operations, args=(items,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=10)

        assert len(errors) == 0

    def test_memory_usage_no_unbounded_growth(self):
        queue = DownloadQueue(max_size=10000)
        for i in range(1000):
            queue.add(url=f"https://example.com/video-{i}")
            if i % 100 == 0:
                item = queue.get_next()
                if item:
                    queue.complete(item.task_id)

        queue.clear_completed()
        assert queue.size > 0
        assert queue.size < 1000


class TestConcurrentExecutorStress:
    def test_executor_handles_concurrent_items(self, monkeypatch):
        queue = DownloadQueue(max_size=50)
        progress = ProgressTracker()
        completed_count = [0]
        lock = threading.Lock()

        def fake_download(**kw):
            return ["/fake/file.mp4"]

        monkeypatch.setattr("src.core.downloader.download_single", fake_download)
        monkeypatch.setattr("src.core.concurrent.download_single", fake_download)

        def on_complete(task_id: str, **kw: Any) -> None:
            with lock:
                if kw.get("success", False):
                    completed_count[0] += 1

        executor = ConcurrentExecutor(
            queue=queue,
            max_workers=3,
            progress_tracker=progress,
            on_item_complete=on_complete,
        )

        for i in range(10):
            queue.add(url=f"https://example.com/video-{i}")

        executor.start_async()
        time.sleep(1)
        executor.stop()

        assert completed_count[0] == 10

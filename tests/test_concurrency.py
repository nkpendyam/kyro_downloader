"""Additional concurrency and stress tests for queue + executor."""

from __future__ import annotations

import threading
import time

from src.core.concurrent import ConcurrentExecutor
from src.core.progress import ProgressTracker
from src.core.queue import DownloadQueue, Priority


def test_queue_add_is_thread_safe_under_concurrency() -> None:
    queue = DownloadQueue(max_size=500)

    def _producer(prefix: str) -> None:
        for idx in range(40):
            queue.add(url=f"https://example.com/{prefix}/{idx}", priority=Priority.NORMAL)

    workers = [threading.Thread(target=_producer, args=(f"w{i}",)) for i in range(5)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    assert queue.size == 200


def test_concurrent_cancel_while_processing(monkeypatch) -> None:
    queue = DownloadQueue()
    item = queue.add(url="https://example.com/video", output_path="downloads")
    progress = ProgressTracker()

    def _slow_download(*_args, **kwargs):
        cancel_event = kwargs["config"]["cancel_event"]
        while not cancel_event.is_set():
            time.sleep(0.01)
        raise RuntimeError("cancelled")

    monkeypatch.setattr("src.core.concurrent.download_single", _slow_download)

    executor = ConcurrentExecutor(queue=queue, max_workers=1, progress_tracker=progress)
    executor.start_async()
    time.sleep(0.05)
    queue.cancel(item.task_id)
    executor.stop()

    updated = queue.get_item(item.task_id)
    assert updated is not None
    assert updated.status.value in {"cancelled", "failed"}


def test_pause_resume_under_load_preserves_items() -> None:
    queue = DownloadQueue()
    items = [queue.add(url=f"https://example.com/{i}") for i in range(30)]

    for item in items[:10]:
        assert queue.pause(item.task_id) is True
    for item in items[:10]:
        assert queue.resume(item.task_id) is True

    all_items = queue.get_all_items()
    assert len(all_items) == 30
    assert len({item.task_id for item in all_items}) == 30

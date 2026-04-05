"""Tests for progress module."""
import asyncio
from unittest.mock import MagicMock
from src.core.progress import ProgressTracker, create_progress_hook, ProgressInfo


class TestProgressTracker:
    def test_init(self):
        pt = ProgressTracker()
        assert pt._tasks == {}

    def test_add_task(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        task = pt.get_task("task1")
        assert task.filename == "test.mp4"
        assert task.total_bytes == 1000
        assert task.status == "downloading"

    def test_update_task(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        pt.update("task1", downloaded_bytes=500, speed=1000000, eta=10)
        task = pt.get_task("task1")
        assert task.downloaded_bytes == 500
        assert task.percentage == 50.0

    def test_complete_task(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        pt.complete("task1")
        task = pt.get_task("task1")
        assert task.status == "completed"

    def test_complete_task_error(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        pt.complete("task1", error="test error")
        task = pt.get_task("task1")
        assert task.status == "error"

    def test_get_task(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        task = pt.get_task("task1")
        assert task is not None

    def test_get_nonexistent_task(self):
        pt = ProgressTracker()
        task = pt.get_task("nonexistent")
        assert task is None

    def test_get_overall_progress_empty(self):
        pt = ProgressTracker()
        progress = pt.get_overall_progress()
        assert progress["percentage"] == 0
        assert progress["total"] == 0

    def test_get_overall_progress_with_tasks(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="a.mp4", total_bytes=1000)
        pt.add_task("task2", filename="b.mp4", total_bytes=1000)
        pt.update("task1", downloaded_bytes=500, speed=0, eta=0)
        pt.update("task2", downloaded_bytes=250, speed=0, eta=0)
        progress = pt.get_overall_progress()
        assert progress["total_bytes"] == 2000
        assert progress["downloaded_bytes"] == 750

    def test_get_all_tasks(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="a.mp4", total_bytes=1000)
        pt.add_task("task2", filename="b.mp4", total_bytes=1000)
        tasks = pt.get_all_tasks()
        assert len(tasks) == 2

    def test_add_callback(self):
        pt = ProgressTracker()
        callback = MagicMock()
        pt.add_callback(callback)
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        pt.update("task1", downloaded_bytes=500, speed=0, eta=0)
        callback.assert_called_once()

    def test_remove_callback(self):
        pt = ProgressTracker()
        callback = MagicMock()
        pt.add_callback(callback)
        pt.remove_callback(callback)
        assert callback not in pt._callbacks

    def test_update_schedules_websocket_broadcast_with_active_loop(self, monkeypatch):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)

        class _Loop:
            def is_running(self):
                return True

        async def _broadcast(_task_id, _progress):
            return None

        called = {"scheduled": False}

        def _run_coroutine_threadsafe(coro, loop):
            called["scheduled"] = True
            called["loop"] = loop
            coro.close()

        import src.ui.web.websocket as ws

        monkeypatch.setattr(ws, "get_event_loop", lambda: _Loop())
        monkeypatch.setattr(ws, "broadcast_progress", _broadcast)
        monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", _run_coroutine_threadsafe)

        pt.update("task1", downloaded_bytes=500, speed=1000, eta=1)

        assert called["scheduled"] is True
        assert called["loop"].is_running() is True

    def test_update_skips_websocket_broadcast_without_active_loop(self, monkeypatch):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)

        def _fail_if_called(_coro, _loop):
            raise AssertionError("run_coroutine_threadsafe should not be called without active loop")

        import src.ui.web.websocket as ws

        monkeypatch.setattr(ws, "get_event_loop", lambda: None)
        monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", _fail_if_called)

        pt.update("task1", downloaded_bytes=500, speed=1000, eta=1)


class TestProgressHook:
    def test_create_progress_hook(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        hook = create_progress_hook(pt, "task1")
        assert callable(hook)

    def test_progress_hook_downloading(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        hook = create_progress_hook(pt, "task1")
        hook({"status": "downloading", "downloaded_bytes": 500, "speed": 1000000, "eta": 10})
        task = pt.get_task("task1")
        assert task.downloaded_bytes == 500

    def test_progress_hook_finished(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        hook = create_progress_hook(pt, "task1")
        hook({"status": "finished"})
        task = pt.get_task("task1")
        assert task.status == "completed"

    def test_progress_hook_error(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        hook = create_progress_hook(pt, "task1")
        hook({"status": "error", "error": "test error"})
        task = pt.get_task("task1")
        assert task.status == "error"

    def test_progress_hook_unknown_status(self):
        pt = ProgressTracker()
        pt.add_task("task1", filename="test.mp4", total_bytes=1000)
        hook = create_progress_hook(pt, "task1")
        hook({"status": "unknown"})
        task = pt.get_task("task1")
        assert task.status == "downloading"


class TestProgressInfo:
    def test_is_complete(self):
        info = ProgressInfo(status="completed")
        assert info.is_complete is True

    def test_is_not_complete(self):
        info = ProgressInfo(status="downloading")
        assert info.is_complete is False

    def test_duration_completed(self):
        info = ProgressInfo(started_at=100.0, completed_at=110.0)
        assert info.duration == 10.0

    def test_duration_in_progress(self):
        import time
        info = ProgressInfo(started_at=time.time() - 5)
        assert 4 <= info.duration <= 6

    def test_duration_not_started(self):
        info = ProgressInfo()
        assert info.duration == 0.0

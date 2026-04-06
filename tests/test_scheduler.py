"""Tests for download scheduling service."""

import os
import time
from datetime import datetime, timezone, timedelta
from src.services.scheduler import DownloadScheduler


def test_scheduler_init(temp_dir):
    schedule_file = os.path.join(temp_dir, "schedule.json")
    scheduler = DownloadScheduler(schedule_file)
    assert len(scheduler.list_schedules()) == 0


def test_add_schedule(temp_dir):
    schedule_file = os.path.join(temp_dir, "schedule.json")
    scheduler = DownloadScheduler(schedule_file)
    future_time = "2099-01-01T00:00:00"
    schedule = scheduler.add_schedule("https://youtube.com/watch?v=test", future_time)
    assert schedule["url"] == "https://youtube.com/watch?v=test"
    assert schedule["status"] == "pending"
    assert len(scheduler.list_schedules()) == 1


def test_remove_schedule(temp_dir):
    schedule_file = os.path.join(temp_dir, "schedule.json")
    scheduler = DownloadScheduler(schedule_file)
    schedule = scheduler.add_schedule("https://youtube.com/watch?v=test", "2099-01-01T00:00:00")
    scheduler.remove_schedule(schedule["id"])
    assert len(scheduler.list_schedules()) == 0


def test_run_due_schedules_executes_callback(temp_dir):
    schedule_file = os.path.join(temp_dir, "schedule.json")
    scheduler = DownloadScheduler(schedule_file)
    schedule = scheduler.add_schedule("https://youtube.com/watch?v=test", "2000-01-01T00:00:00")

    called = []

    def _callback(item):
        called.append(item["id"])

    executed = scheduler.run_due_schedules(_callback)

    assert executed == 1
    assert called == [schedule["id"]]


def test_scheduler_health_false_when_stopped(temp_dir):
    schedule_file = os.path.join(temp_dir, "schedule.json")
    scheduler = DownloadScheduler(schedule_file)
    assert scheduler.is_healthy() is False


def test_scheduler_health_true_when_running(temp_dir):
    schedule_file = os.path.join(temp_dir, "schedule.json")
    scheduler = DownloadScheduler(schedule_file)
    scheduler.start_scheduler()
    try:
        time.sleep(0.05)
        assert scheduler.is_healthy() is True
    finally:
        scheduler.stop_scheduler()


def test_scheduler_handles_timezone_aware_comparison_in_run_loop(temp_dir):
    schedule_file = os.path.join(temp_dir, "schedule.json")
    tz = timezone(timedelta(hours=5, minutes=30))
    scheduler = DownloadScheduler(schedule_file, tz=tz)
    scheduler.add_schedule("https://example.com/video", datetime.now(tz).isoformat())

    scheduler._running = True
    scheduler._heartbeat_interval_seconds = 0.01

    original_sleep = time.sleep

    def _stop_after_one(_seconds):
        scheduler._running = False

    try:
        time.sleep = _stop_after_one  # type: ignore[assignment]
        scheduler._run_loop(callback=lambda _item: None)
    finally:
        time.sleep = original_sleep  # type: ignore[assignment]

    assert scheduler._last_heartbeat > 0

"""Tests for download scheduling service."""
import os
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

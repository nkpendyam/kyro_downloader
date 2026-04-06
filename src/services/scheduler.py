"""Download scheduling service."""

from typing import Any

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from datetime import timezone

try:
    from dateutil.relativedelta import relativedelta  # type: ignore[import-not-found]

    _HAS_DATEUTIL = True
except ImportError:
    _HAS_DATEUTIL = False
    relativedelta = None  # type: ignore[misc,assignment]

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DownloadScheduler:
    def __init__(self, schedule_file: str | None = None, tz: timezone = timezone.utc) -> None:
        self._tz = tz
        if not schedule_file:
            schedule_dir = Path.home() / ".config" / "kyro"
            schedule_dir.mkdir(parents=True, exist_ok=True)
            schedule_file = str(schedule_dir / "schedule.json")
        self._schedule_file = Path(schedule_file)
        self._schedules = self._load()
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._heartbeat_interval_seconds = 1.0
        self._last_heartbeat = time.time()

    def _load(self) -> list[dict[str, Any]]:
        if self._schedule_file.exists():
            try:
                with open(self._schedule_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load schedule file: {e}")
        return []

    def _save(self) -> None:
        try:
            with self._lock:
                schedules = list(self._schedules)
            self._schedule_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._schedule_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(schedules, f, indent=2)
            tmp.replace(self._schedule_file)
        except IOError as e:
            logger.error(f"Failed to save schedule file: {e}")

    def add_schedule(
        self,
        url: str,
        scheduled_time: str,
        output_path: str | None = None,
        only_audio: bool = False,
        format_id: str | None = None,
        repeat: str = "none",
    ) -> dict[str, Any]:
        with self._lock:
            next_index = len(self._schedules)
        schedule = {
            "id": f"schedule_{int(time.time())}_{next_index}",
            "url": url,
            "scheduled_time": scheduled_time,
            "output_path": output_path,
            "only_audio": only_audio,
            "format_id": format_id,
            "repeat": repeat,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "next_run": scheduled_time,
        }
        with self._lock:
            self._schedules.append(schedule)
        self._save()
        logger.info(f"Schedule added: {url} at {scheduled_time}")
        return schedule

    def remove_schedule(self, schedule_id: str) -> None:
        with self._lock:
            self._schedules = [s for s in self._schedules if s["id"] != schedule_id]
        self._save()

    def list_schedules(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(schedule) for schedule in self._schedules]

    def get_due_schedules(self) -> list[dict[str, Any]]:
        now = datetime.now(self._tz)
        due = []
        with self._lock:
            schedules = [dict(schedule) for schedule in self._schedules]
        for s in schedules:
            if s["status"] != "pending":
                continue
            try:
                scheduled_time = s.get("next_run") or s["scheduled_time"]
                scheduled = datetime.fromisoformat(scheduled_time)
                if scheduled.tzinfo is None:
                    scheduled = scheduled.replace(tzinfo=self._tz)
                if scheduled <= now:
                    due.append(s)
            except (ValueError, TypeError):
                continue
        return due

    def mark_completed(self, schedule_id: str) -> None:
        should_save = False
        with self._lock:
            for s in self._schedules:
                if s["id"] == schedule_id:
                    s["status"] = "completed"
                    s["last_run"] = datetime.now(self._tz).isoformat()
                    if s["repeat"] != "none":
                        s["status"] = "pending"
                        s["next_run"] = self._calculate_next_run(s["scheduled_time"], s["repeat"])
                    should_save = True
                    break
        if should_save:
            self._save()

    def _calculate_next_run(self, base_time: str, repeat: str) -> str:
        base = datetime.fromisoformat(base_time)
        if base.tzinfo is None:
            base = base.replace(tzinfo=self._tz)
        if repeat == "daily":
            return (base + timedelta(days=1)).isoformat()
        elif repeat == "weekly":
            return (base + timedelta(weeks=1)).isoformat()
        elif repeat == "monthly":
            if _HAS_DATEUTIL and relativedelta is not None:
                return (base + relativedelta(months=1)).isoformat()
            # Fallback: approximate 30 days when dateutil is missing
            return (base + timedelta(days=30)).isoformat()
        return base_time

    def run_due_schedules(self, callback: Any | None = None) -> int:
        """Run all due schedules once and return execution count."""
        due = self.get_due_schedules()
        for schedule in due:
            logger.info(f"Executing scheduled download: {schedule['url']}")
            if callback:
                callback(schedule)
            self.mark_completed(schedule["id"])
        return len(due)

    def start_scheduler(self, callback: Any | None = None) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._running = True
        self._last_heartbeat = time.time()
        self._thread = threading.Thread(target=self._run_loop, args=(callback,), daemon=True)
        self._thread.start()
        logger.info("Scheduler started")

    def stop_scheduler(self) -> None:
        self._running = False
        logger.info("Scheduler stopped")

    def is_healthy(self) -> bool:
        if not self._running or self._thread is None or not self._thread.is_alive():
            return False
        age_seconds = time.time() - self._last_heartbeat
        return age_seconds <= (2 * self._heartbeat_interval_seconds)

    def ensure_running(self, callback: Any | None = None) -> None:
        if self._thread is None or not self._thread.is_alive():
            logger.warning("Scheduler thread not alive, restarting")
            self.start_scheduler(callback)

    def _run_loop(self, callback: Any | None = None) -> None:
        while self._running:
            self._last_heartbeat = time.time()
            self.run_due_schedules(callback)
            now = datetime.now(self._tz)
            upcoming = []
            with self._lock:
                schedules = [dict(schedule) for schedule in self._schedules]
            for schedule in schedules:
                if schedule.get("status") != "pending":
                    continue
                try:
                    target = datetime.fromisoformat(schedule.get("next_run") or schedule["scheduled_time"])
                except (ValueError, TypeError):
                    continue
                if target.tzinfo is None:
                    target = target.replace(tzinfo=self._tz)
                if target > now:
                    upcoming.append((target - now).total_seconds())
            if upcoming:
                sleep_seconds = max(1.0, min(upcoming))
            else:
                sleep_seconds = 300.0
            self._heartbeat_interval_seconds = max(1.0, sleep_seconds)
            time.sleep(sleep_seconds)

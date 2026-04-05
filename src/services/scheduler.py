"""Download scheduling service."""
from typing import Any

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from src.utils.logger import get_logger
logger = get_logger(__name__)

class DownloadScheduler:
    def __init__(self, schedule_file: str | None = None) -> None:
        if not schedule_file:
            schedule_dir = Path.home() / ".config" / "kyro"
            schedule_dir.mkdir(parents=True, exist_ok=True)
            schedule_file = str(schedule_dir / "schedule.json")
        self._schedule_file = Path(schedule_file)
        self._schedules = self._load()
        self._running = False
        self._thread: threading.Thread | None = None

    def _load(self) -> list[dict[str, Any]]:
        if self._schedule_file.exists():
            try:
                with open(self._schedule_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load schedule file: {e}")
        return []

    def _save(self) -> None:
        try:
            self._schedule_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._schedule_file.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(self._schedules, f, indent=2)
            tmp.replace(self._schedule_file)
        except IOError as e:
            logger.error(f"Failed to save schedule file: {e}")

    def add_schedule(self, url: str, scheduled_time: str, output_path: str | None = None, only_audio: bool = False, format_id: str | None = None, repeat: str = "none") -> dict[str, Any]:
        schedule = {
            "id": f"schedule_{int(time.time())}_{len(self._schedules)}",
            "url": url, "scheduled_time": scheduled_time, "output_path": output_path,
            "only_audio": only_audio, "format_id": format_id, "repeat": repeat,
            "status": "pending", "created_at": datetime.now().isoformat(),
            "last_run": None, "next_run": scheduled_time
        }
        self._schedules.append(schedule)
        self._save()
        logger.info(f"Schedule added: {url} at {scheduled_time}")
        return schedule

    def remove_schedule(self, schedule_id: str) -> None:
        self._schedules = [s for s in self._schedules if s["id"] != schedule_id]
        self._save()

    def list_schedules(self) -> list[dict[str, Any]]:
        return self._schedules

    def get_due_schedules(self) -> list[dict[str, Any]]:
        now = datetime.now()
        due = []
        for s in self._schedules:
            if s["status"] != "pending":
                continue
            try:
                scheduled_time = s.get("next_run") or s["scheduled_time"]
                scheduled = datetime.fromisoformat(scheduled_time)
                if scheduled <= now:
                    due.append(s)
            except (ValueError, TypeError):
                continue
        return due

    def mark_completed(self, schedule_id: str) -> None:
        for s in self._schedules:
            if s["id"] == schedule_id:
                s["status"] = "completed"
                s["last_run"] = datetime.now().isoformat()
                if s["repeat"] != "none":
                    s["status"] = "pending"
                    s["next_run"] = self._calculate_next_run(s["scheduled_time"], s["repeat"])
                self._save()
                break

    def _calculate_next_run(self, base_time: str, repeat: str) -> str:
        base = datetime.fromisoformat(base_time)
        if repeat == "daily": return (base + timedelta(days=1)).isoformat()
        elif repeat == "weekly": return (base + timedelta(weeks=1)).isoformat()
        elif repeat == "monthly": return (base + timedelta(days=30)).isoformat()
        return base_time

    def start_scheduler(self, callback: Any | None = None) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, args=(callback,), daemon=True)
        self._thread.start()

    def stop_scheduler(self) -> None:
        self._running = False

    def _run_loop(self, callback: Any | None = None) -> None:
        while self._running:
            due = self.get_due_schedules()
            for schedule in due:
                logger.info(f"Executing scheduled download: {schedule['url']}")
                if callback: callback(schedule)
                self.mark_completed(schedule["id"])
            time.sleep(60)

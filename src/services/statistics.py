"""Download statistics and analytics service."""

import atexit
import threading
import weakref
from typing import Any

import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from src.utils.logger import get_logger

logger = get_logger(__name__)

_atexit_registered = False
_registered_trackers: weakref.WeakSet["StatsTracker"] = weakref.WeakSet()


def _flush_all_trackers() -> None:
    for tracker in list(_registered_trackers):
        try:
            tracker.force_save()
        except Exception:
            pass


@dataclass
class DownloadStats:
    total_downloads: int = 0
    total_bytes: int = 0
    total_duration_seconds: float = 0.0
    successful: int = 0
    failed: int = 0
    retries_total: int = 0
    formats_used: dict = field(default_factory=dict)
    platforms_used: dict = field(default_factory=dict)
    average_speed_mbps: float = 0.0
    peak_speed_mbps: float = 0.0
    total_time_seconds: float = 0.0
    first_download: str = ""
    last_download: str = ""

    @property
    def success_rate(self) -> float:
        if self.total_downloads == 0:
            return 0.0
        return (self.successful / self.total_downloads) * 100

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024**3)

    @property
    def avg_speed_mbps(self) -> float:
        if self.total_time_seconds == 0:
            return 0.0
        return (self.total_bytes * 8) / (self.total_time_seconds * 1_000_000)


class StatsTracker:
    def __init__(self, stats_file: str | None = None) -> None:
        if not stats_file:
            stats_dir = Path.home() / ".config" / "kyro"
            stats_dir.mkdir(parents=True, exist_ok=True)
            stats_file = str(stats_dir / "stats.json")
        self._stats_file = Path(stats_file)
        self._stats = self._load()
        self._lock = threading.RLock()
        self._dirty = False
        self._pending_records = 0
        self._flush_interval_seconds = 2.0
        self._save_every_records = 10
        self._last_saved_at = time.time()
        global _atexit_registered
        if not _atexit_registered:
            atexit.register(_flush_all_trackers)
            _atexit_registered = True
        _registered_trackers.add(self)

    def _load(self) -> DownloadStats:
        if self._stats_file.exists():
            try:
                with open(self._stats_file, "r", encoding="utf-8") as f:
                    return DownloadStats(**json.load(f))
            except (json.JSONDecodeError, TypeError, IOError) as e:
                logger.warning(f"Failed to load stats: {e}")
        return DownloadStats()

    def _save(self) -> None:
        try:
            self._stats_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._stats_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(asdict(self._stats), f, indent=2)
            tmp.replace(self._stats_file)
            self._dirty = False
            self._pending_records = 0
            self._last_saved_at = time.time()
        except IOError as e:
            logger.error(f"Failed to save stats: {e}")

    def _maybe_save(self) -> None:
        now = time.time()
        if self._pending_records >= self._save_every_records:
            self._save()
            return
        if now - self._last_saved_at >= self._flush_interval_seconds:
            self._save()

    def force_save(self) -> None:
        """Persist buffered stats immediately if there are pending changes."""
        with self._lock:
            if self._dirty:
                self._save()

    def record_download(
        self,
        success: bool,
        bytes_downloaded: int = 0,
        duration: float = 0.0,
        format_id: str = "",
        platform: str = "",
        retries: int = 0,
        speed_mbps: float = 0.0,
        wall_time: float = 0.0,
    ) -> None:
        with self._lock:
            self._stats.total_downloads += 1
            self._stats.total_time_seconds += wall_time if wall_time > 0 else duration
            if success:
                self._stats.successful += 1
                self._stats.total_bytes += bytes_downloaded
                if format_id:
                    self._stats.formats_used[format_id] = self._stats.formats_used.get(format_id, 0) + 1
                if platform:
                    self._stats.platforms_used[platform] = self._stats.platforms_used.get(platform, 0) + 1
                if speed_mbps > self._stats.peak_speed_mbps:
                    self._stats.peak_speed_mbps = speed_mbps
            else:
                self._stats.failed += 1
            self._stats.retries_total += retries
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            if not self._stats.first_download:
                self._stats.first_download = now
            self._stats.last_download = now
            self._dirty = True
            self._pending_records += 1
            self._maybe_save()

    def get_stats(self) -> DownloadStats:
        with self._lock:
            return self._stats

    def get_summary(self) -> dict[str, Any]:
        with self._lock:
            s = self._stats
            return {
                "total_downloads": s.total_downloads,
                "successful": s.successful,
                "failed": s.failed,
                "success_rate": f"{s.success_rate:.1f}%",
                "total_data": f"{s.total_gb:.2f} GB",
                "avg_speed": f"{s.avg_speed_mbps:.1f} Mbps",
                "peak_speed": f"{s.peak_speed_mbps:.1f} Mbps",
                "total_time": f"{s.total_time_seconds / 3600:.1f} hours",
                "total_retries": s.retries_total,
                "first_download": s.first_download,
                "last_download": s.last_download,
                "top_formats": dict(sorted(s.formats_used.items(), key=lambda x: x[1], reverse=True)[:5]),
                "top_platforms": dict(sorted(s.platforms_used.items(), key=lambda x: x[1], reverse=True)[:5]),
            }

    def reset(self) -> None:
        with self._lock:
            self._stats = DownloadStats()
            self._dirty = True
            self._pending_records = 1
            self._save()
        logger.info("Statistics reset")

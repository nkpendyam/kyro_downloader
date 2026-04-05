"""Download archive service - track already downloaded videos."""
from typing import Any

import json
from pathlib import Path
from datetime import datetime
from src.utils.logger import get_logger
logger = get_logger(__name__)

class DownloadArchive:
    def __init__(self, archive_file: str | None = None) -> None:
        if not archive_file:
            archive_dir = Path.home() / ".config" / "kyro"
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_file = str(archive_dir / "archive.json")
        self._archive_file = Path(archive_file)
        self._entries = self._load()

    def _load(self) -> dict[str, Any]:
        if self._archive_file.exists():
            try:
                with open(self._archive_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load archive: {e}")
        return {}

    def _save(self) -> None:
        try:
            self._archive_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._archive_file.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(self._entries, f, indent=2)
            tmp.replace(self._archive_file)
        except IOError as e:
            logger.error(f"Failed to save archive: {e}")

    def add(self, video_id: str, title: str, url: str, filepath: str | Path, size: int = 0, duration: int = 0, platform: str = "") -> None:
        self._entries[video_id] = {
            "title": title, "url": url, "filepath": str(filepath),
            "size": size, "duration": duration, "platform": platform,
            "downloaded_at": datetime.now().isoformat()
        }
        self._save()
        logger.info(f"Archive: Added {title}")

    def contains(self, video_id: str) -> bool:
        return video_id in self._entries

    def get(self, video_id: str) -> dict[str, Any] | None:
        return self._entries.get(video_id)

    def remove(self, video_id: str) -> None:
        if video_id in self._entries:
            del self._entries[video_id]
            self._save()
            logger.info(f"Archive: Removed {video_id}")

    def list_all(self, limit: int = 100) -> list[tuple[str, dict[str, Any]]]:
        items = sorted(self._entries.items(), key=lambda x: x[1].get("downloaded_at", ""), reverse=True)
        return items[:limit]

    def get_stats(self) -> dict[str, Any]:
        total_size = sum(e.get("size", 0) for e in self._entries.values())
        total_duration = sum(e.get("duration", 0) for e in self._entries.values())
        platforms = {}
        for e in self._entries.values():
            p = e.get("platform", "unknown")
            platforms[p] = platforms.get(p, 0) + 1
        return {"total_downloads": len(self._entries), "total_size_gb": total_size / (1024**3), "total_duration_hours": total_duration / 3600, "platforms": platforms}

    def clear(self) -> None:
        self._entries = {}
        self._save()
        logger.info("Archive cleared")

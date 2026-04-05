"""History viewer component for Desktop GUI."""
import json
from pathlib import Path
from datetime import datetime


class HistoryViewer:
    def __init__(self, state_dir=".kyro_state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.history_file = self.state_dir / "history.json"
        self._history = []
        self._load_history()

    def _load_history(self):
        try:
            if self.history_file.exists():
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                self._history = data.get("history", [])
        except Exception:
            self._history = []

    def _save_history(self):
        try:
            with open(self.history_file, "w") as f:
                json.dump({"history": self._history}, f, indent=2)
        except Exception:
            pass

    def add_entry(self, task_id, url, title, status, file_path=None, file_size=None, error=None):
        entry = {
            "task_id": task_id,
            "url": url,
            "title": title or "Unknown",
            "status": status,
            "file_path": file_path,
            "file_size": file_size,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }
        self._history.insert(0, entry)
        if len(self._history) > 1000:
            self._history = self._history[:1000]
        self._save_history()

    def get_history(self, limit=50, offset=0):
        return self._history[offset:offset + limit]

    def search_history(self, query, limit=50):
        query = query.lower()
        return [
            entry for entry in self._history
            if query in entry.get("url", "").lower()
            or query in entry.get("title", "").lower()
            or query in entry.get("task_id", "").lower()
        ][:limit]

    def filter_by_status(self, status, limit=50):
        return [
            entry for entry in self._history
            if entry.get("status") == status
        ][:limit]

    def filter_by_date_range(self, start_date, end_date, limit=50):
        result = []
        for entry in self._history:
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                if start_date <= ts <= end_date:
                    result.append(entry)
            except (ValueError, KeyError):
                continue
            if len(result) >= limit:
                break
        return result

    def get_entry(self, task_id):
        for entry in self._history:
            if entry.get("task_id") == task_id:
                return entry
        return None

    def delete_entry(self, task_id):
        self._history = [e for e in self._history if e.get("task_id") != task_id]
        self._save_history()

    def clear_history(self):
        self._history = []
        self._save_history()

    def get_stats(self):
        total = len(self._history)
        completed = sum(1 for e in self._history if e.get("status") == "completed")
        failed = sum(1 for e in self._history if e.get("status") == "failed")
        total_size = sum(e.get("file_size", 0) or 0 for e in self._history if e.get("status") == "completed")
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_size_gb": total_size / (1024 * 1024 * 1024),
        }

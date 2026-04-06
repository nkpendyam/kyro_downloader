"""Tags manager component for Desktop GUI."""

import json
from pathlib import Path

TAG_COLORS = {
    "music": "#e91e63",
    "video": "#2196f3",
    "playlist": "#ff9800",
    "tutorial": "#4caf50",
    "entertainment": "#3f51b5",
    "education": "#00bcd4",
    "news": "#f44336",
    "podcast": "#9c27b0",
    "default": "#9e9e9e",
}


class TagsManager:
    def __init__(self, state_dir: str = ".kyro_state") -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.tags_file = self.state_dir / "tags.json"
        self._tags: dict[str, str] = {}
        self._all_tags: set[str] = set()
        self._load_tags()

    def _load_tags(self) -> None:
        try:
            if self.tags_file.exists():
                with open(self.tags_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._tags = data.get("tags", {})
                self._all_tags = set(data.get("all_tags", []))
        except Exception:
            self._tags = {}
            self._all_tags = set()

    def _save_tags(self) -> None:
        try:
            tmp = self.tags_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"tags": self._tags, "all_tags": list(self._all_tags)}, f, indent=2)
            tmp.replace(self.tags_file)
        except Exception:
            pass

    def add_tags(self, task_id: str, tags_str: str) -> None:
        if not tags_str:
            return
        for tag in tags_str.split(","):
            tag = tag.strip().lower()
            if tag:
                self._all_tags.add(tag)
        self._tags[task_id] = tags_str
        self._save_tags()

    def get_tags(self, task_id: str) -> str:
        return self._tags.get(task_id, "")

    def remove_tag_from_task(self, task_id: str, tag_to_remove: str) -> None:
        tags_str = self._tags.get(task_id, "")
        if not tags_str:
            return
        tags = [t.strip().lower() for t in tags_str.split(",")]
        if tag_to_remove.lower() in tags:
            tags.remove(tag_to_remove.lower())
            new_tags_str = ", ".join(tags)
            if new_tags_str:
                self._tags[task_id] = new_tags_str
            else:
                del self._tags[task_id]
            self._save_tags()

    def get_all_tags(self) -> list[str]:
        return sorted(self._all_tags)

    def get_tag_color(self, tag: str) -> str:
        tag = tag.strip().lower()
        return TAG_COLORS.get(tag, TAG_COLORS["default"])

    def get_tasks_by_tag(self, tag: str) -> list[str]:
        tag = tag.strip().lower()
        result: list[str] = []
        for task_id, tags_str in self._tags.items():
            if tag in [t.strip().lower() for t in tags_str.split(",")]:
                result.append(task_id)
        return result

    def delete_tag_globally(self, tag: str) -> None:
        tag = tag.strip().lower()
        if tag in self._all_tags:
            self._all_tags.discard(tag)
        tasks_to_remove = []
        for task_id, tags_str in self._tags.items():
            tags = [t.strip().lower() for t in tags_str.split(",")]
            if tag in tags:
                tags.remove(tag)
                if tags:
                    self._tags[task_id] = ", ".join(tags)
                else:
                    tasks_to_remove.append(task_id)
        for task_id in tasks_to_remove:
            del self._tags[task_id]
        self._save_tags()

    def get_tag_stats(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for tag in self._all_tags:
            stats[tag] = len(self.get_tasks_by_tag(tag))
        return stats

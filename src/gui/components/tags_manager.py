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
    def __init__(self, state_dir=".kyro_state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.tags_file = self.state_dir / "tags.json"
        self._tags = {}
        self._all_tags = set()
        self._load_tags()

    def _load_tags(self):
        try:
            if self.tags_file.exists():
                with open(self.tags_file, "r") as f:
                    data = json.load(f)
                self._tags = data.get("tags", {})
                self._all_tags = set(data.get("all_tags", []))
        except Exception:
            self._tags = {}
            self._all_tags = set()

    def _save_tags(self):
        try:
            with open(self.tags_file, "w") as f:
                json.dump({"tags": self._tags, "all_tags": list(self._all_tags)}, f, indent=2)
        except Exception:
            pass

    def add_tags(self, task_id, tags_str):
        if not tags_str:
            return
        for tag in tags_str.split(","):
            tag = tag.strip().lower()
            if tag:
                self._all_tags.add(tag)
        self._tags[task_id] = tags_str
        self._save_tags()

    def get_tags(self, task_id):
        return self._tags.get(task_id, "")

    def remove_tag_from_task(self, task_id, tag_to_remove):
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

    def get_all_tags(self):
        return sorted(self._all_tags)

    def get_tag_color(self, tag):
        tag = tag.strip().lower()
        return TAG_COLORS.get(tag, TAG_COLORS["default"])

    def get_tasks_by_tag(self, tag):
        tag = tag.strip().lower()
        result = []
        for task_id, tags_str in self._tags.items():
            if tag in [t.strip().lower() for t in tags_str.split(",")]:
                result.append(task_id)
        return result

    def delete_tag_globally(self, tag):
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

    def get_tag_stats(self):
        stats = {}
        for tag in self._all_tags:
            stats[tag] = len(self.get_tasks_by_tag(tag))
        return stats

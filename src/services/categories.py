"""Category manager - organize downloads by category."""

from typing import Any

import copy
import json
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

CATEGORIES_FILE = Path.home() / ".config" / "kyro" / "categories.json"

DEFAULT_CATEGORIES = {
    "Music": {"patterns": ["music", "song", "audio", "track", "album"], "folder": "Music"},
    "Education": {"patterns": ["tutorial", "course", "lecture", "learn", "teach"], "folder": "Education"},
    "Entertainment": {"patterns": ["comedy", "funny", "entertainment", "show"], "folder": "Entertainment"},
    "Gaming": {"patterns": ["gaming", "gameplay", "walkthrough"], "folder": "Gaming"},
    "News": {"patterns": ["news", "report", "breaking"], "folder": "News"},
    "Sports": {"patterns": ["sport", "match", "game", "highlight"], "folder": "Sports"},
    "Technology": {"patterns": ["tech", "review", "unboxing", "how-to"], "folder": "Technology"},
    "Other": {"patterns": [], "folder": "Other"},
}


class CategoryManager:
    def __init__(self) -> None:
        self._file = CATEGORIES_FILE
        self._categories = self._load()

    def _load(self) -> dict[str, Any]:
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return copy.deepcopy(DEFAULT_CATEGORIES)

    def _save(self) -> None:
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._categories, f, indent=2)
            tmp.replace(self._file)
        except OSError as e:
            logger.warning(f"Failed to save categories: {e}")

    def categorize(self, title: str, description: str = "") -> str:
        text = f"{title} {description}".lower()
        for name, cat in self._categories.items():
            for pattern in cat.get("patterns", []):
                if pattern.lower() in text:
                    return name
        return "Other"

    def get_folder(self, category: str) -> str:
        return self._categories.get(category, {}).get("folder", "Other")

    def list_categories(self) -> list[str]:
        return list(self._categories.keys())

    def add_category(self, name: str, patterns: list[str], folder: str) -> None:
        self._categories[name] = {"patterns": patterns, "folder": folder}
        self._save()

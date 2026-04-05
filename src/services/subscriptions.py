"""Channel subscription manager - auto-check for new videos."""
from typing import Any

import json
from pathlib import Path
from datetime import datetime
from src.utils.logger import get_logger
logger = get_logger(__name__)

SUBSCRIPTIONS_FILE = Path.home() / ".config" / "kyro" / "subscriptions.json"

class SubscriptionManager:
    def __init__(self) -> None:
        self._file = SUBSCRIPTIONS_FILE
        self._subscriptions = self._load()

    def _load(self) -> list[dict[str, Any]]:
        if self._file.exists():
            try:
                with open(self._file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load subscriptions: {e}")
        return []

    def _save(self) -> None:
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._file.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(self._subscriptions, f, indent=2)
            tmp.replace(self._file)
        except OSError as e:
            logger.warning(f"Failed to save subscriptions: {e}")

    def subscribe(self, channel_url: str, auto_download: bool = False, quality: str = "best", output_path: str | None = None) -> dict[str, Any]:
        sub = {
            "url": channel_url,
            "auto_download": auto_download,
            "quality": quality,
            "output_path": output_path,
            "last_check": None,
            "last_video": None,
            "created": datetime.now().isoformat(),
        }
        self._subscriptions.append(sub)
        self._save()
        logger.info(f"Subscribed to: {channel_url}")
        return sub

    def unsubscribe(self, channel_url: str) -> None:
        self._subscriptions = [s for s in self._subscriptions if s["url"] != channel_url]
        self._save()

    def list_subscriptions(self) -> list[dict[str, Any]]:
        return self._subscriptions

    def update_last_check(self, channel_url: str, last_video: str | None = None) -> None:
        for sub in self._subscriptions:
            if sub["url"] == channel_url:
                sub["last_check"] = datetime.now().isoformat()
                if last_video:
                    sub["last_video"] = last_video
                self._save()
                break

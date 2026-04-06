"""Preset profile storage and lookup service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_PRESETS: dict[str, dict[str, Any]] = {
    "YouTube 1080p": {
        "id": "yt1080p",
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "only_audio": False,
        "mode": "video",
        "icon": "📺",
    },
    "YouTube 720p": {
        "id": "yt720p",
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "only_audio": False,
        "mode": "video",
        "icon": "📺",
    },
    "YouTube 480p": {
        "id": "yt480p",
        "format": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "only_audio": False,
        "mode": "video",
        "icon": "📺",
    },
    "Audio MP3": {
        "id": "mp3",
        "format": None,
        "only_audio": True,
        "mode": "mp3",
        "audio_format": "mp3",
        "icon": "🎵",
    },
    "Audio FLAC": {
        "id": "flac",
        "format": None,
        "only_audio": True,
        "mode": "mp3",
        "audio_format": "flac",
        "icon": "🎵",
    },
    "Audio AAC": {
        "id": "aac",
        "format": None,
        "only_audio": True,
        "mode": "mp3",
        "audio_format": "aac",
        "icon": "🎵",
    },
    "Voice Optimized": {
        "id": "voice_optimized",
        "format": None,
        "only_audio": True,
        "mode": "mp3",
        "audio_format": "opus",
        "audio_quality": "96",
        "subtitles": {
            "enabled": True,
            "languages": ["en"],
            "embed": False,
            "auto_generated": True,
            "format": "vtt",
        },
        "output_template": "%(uploader)s/%(upload_date)s_%(title)s.%(ext)s",
        "icon": "🎙️",
    },
    "Music Lossless": {
        "id": "music_lossless",
        "format": None,
        "only_audio": True,
        "mode": "mp3",
        "audio_format": "flac",
        "audio_quality": "0",
        "subtitles": {
            "enabled": False,
            "languages": ["en"],
            "embed": False,
            "auto_generated": False,
            "format": "srt",
        },
        "output_template": "%(uploader)s/%(title)s [%(id)s].%(ext)s",
        "icon": "🎼",
    },
    "Podcast Fast": {
        "id": "podcast_fast",
        "format": None,
        "only_audio": True,
        "mode": "mp3",
        "audio_format": "mp3",
        "audio_quality": "96",
        "subtitles": {
            "enabled": True,
            "languages": ["en"],
            "embed": False,
            "auto_generated": True,
            "format": "vtt",
        },
        "output_template": "%(upload_date)s/%(title)s.%(ext)s",
        "icon": "🎧",
    },
    "Playlist": {
        "id": "playlist",
        "format": None,
        "only_audio": False,
        "mode": "playlist",
        "icon": "📋",
    },
    "Batch File": {
        "id": "batch",
        "format": None,
        "only_audio": False,
        "mode": "batch",
        "icon": "📁",
    },
}


PRESET_PROFILES: dict[str, dict[str, Any]] = {
    "voice-optimized": {
        "audio_format": "opus",
        "audio_quality": "96",
        "audio_selector_preference": "opus",
        "subtitles": {
            "enabled": True,
            "languages": ["en"],
            "embed": False,
            "auto_generated": True,
            "format": "vtt",
        },
        "output_template": "%(uploader)s/%(upload_date)s_%(title)s.%(ext)s",
        "only_audio": True,
    },
    "music-lossless": {
        "audio_format": "flac",
        "audio_quality": "0",
        "audio_selector_preference": "flac",
        "subtitles": {
            "enabled": False,
            "languages": ["en"],
            "embed": False,
            "auto_generated": False,
            "format": "srt",
        },
        "output_template": "%(uploader)s/%(title)s [%(id)s].%(ext)s",
        "only_audio": True,
    },
    "podcast-fast": {
        "audio_format": "mp3",
        "audio_quality": "96",
        "audio_selector_preference": "any",
        "subtitles": {
            "enabled": True,
            "languages": ["en"],
            "embed": False,
            "auto_generated": True,
            "format": "vtt",
        },
        "output_template": "%(upload_date)s/%(title)s.%(ext)s",
        "only_audio": True,
    },
}


def apply_preset_config(config: dict[str, Any], preset_name: str | None) -> dict[str, Any] | None:
    """Apply a shared preset profile into a runtime config dictionary."""
    if not preset_name or preset_name == "none":
        return None

    preset = PRESET_PROFILES.get(preset_name)
    if not preset:
        return None

    config["audio_format"] = str(preset["audio_format"])
    config["audio_quality"] = str(preset["audio_quality"])
    config["subtitles"] = dict(preset["subtitles"])
    config["output_template"] = str(preset["output_template"])
    config["audio_selector_preference"] = str(preset.get("audio_selector_preference", "any"))
    return preset


class PresetsManager:
    """Persist and expose user-editable download presets."""

    def __init__(self, state_dir: str | None = None) -> None:
        """Initialize presets manager with absolute state directory."""
        if state_dir is None:
            state_dir = str(Path.home() / ".kyro" / "presets")
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.presets_file = self.state_dir / "presets.json"
        self._presets: dict[str, dict[str, Any]] = {}
        self._load_presets()

    def _load_presets(self) -> None:
        try:
            if self.presets_file.exists():
                with self.presets_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self._presets = data.get("presets", DEFAULT_PRESETS.copy())
            else:
                self._presets = DEFAULT_PRESETS.copy()
                self._save_presets()
        except Exception:
            self._presets = DEFAULT_PRESETS.copy()

    def _save_presets(self) -> None:
        try:
            with self.presets_file.open("w", encoding="utf-8") as f:
                json.dump({"presets": self._presets}, f, indent=2)
        except Exception:
            pass

    def get_all_presets(self) -> dict[str, dict[str, Any]]:
        """Return a copy of all presets."""
        return self._presets.copy()

    def get_preset(self, name: str) -> dict[str, Any] | None:
        """Return preset configuration by display name."""
        return self._presets.get(name)

    def get_preset_by_id(self, preset_id: str) -> tuple[str | None, dict[str, Any] | None]:
        """Resolve a preset by stable id."""
        for name, preset in self._presets.items():
            if preset.get("id") == preset_id:
                return name, preset
        return None, None

    def add_preset(self, name: str, preset_config: dict[str, Any]) -> None:
        """Create a new preset and persist it."""
        if "id" not in preset_config:
            preset_config["id"] = name.lower().replace(" ", "_")
        self._presets[name] = preset_config
        self._save_presets()

    def remove_preset(self, name: str) -> bool:
        """Remove a user preset while keeping built-ins intact."""
        if name in self._presets and name not in DEFAULT_PRESETS:
            del self._presets[name]
            self._save_presets()
            return True
        return False

    def update_preset(self, name: str, new_config: dict[str, Any]) -> None:
        """Update an existing preset and persist the change."""
        if name in self._presets:
            self._presets[name].update(new_config)
            self._save_presets()

    def reset_to_defaults(self) -> None:
        """Restore built-in presets."""
        self._presets = DEFAULT_PRESETS.copy()
        self._save_presets()

    def export_presets(self, filepath: str) -> bool:
        """Export all presets to a JSON file."""
        try:
            with Path(filepath).open("w", encoding="utf-8") as f:
                json.dump({"presets": self._presets}, f, indent=2)
            return True
        except Exception:
            return False

    def import_presets(self, filepath: str) -> int:
        """Import presets from a JSON file and return imported count."""
        try:
            with Path(filepath).open("r", encoding="utf-8") as f:
                data = json.load(f)
            imported = data.get("presets", {})
            self._presets.update(imported)
            self._save_presets()
            return len(imported)
        except Exception:
            return 0

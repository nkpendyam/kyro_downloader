"""Presets manager component for Desktop GUI."""
import json
from pathlib import Path

DEFAULT_PRESETS = {
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

class PresetsManager:
    def __init__(self, state_dir=".kyro_state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.presets_file = self.state_dir / "presets.json"
        self._presets = {}
        self._load_presets()

    def _load_presets(self):
        try:
            if self.presets_file.exists():
                with open(self.presets_file, "r") as f:
                    data = json.load(f)
                self._presets = data.get("presets", DEFAULT_PRESETS.copy())
            else:
                self._presets = DEFAULT_PRESETS.copy()
                self._save_presets()
        except Exception:
            self._presets = DEFAULT_PRESETS.copy()

    def _save_presets(self):
        try:
            with open(self.presets_file, "w") as f:
                json.dump({"presets": self._presets}, f, indent=2)
        except Exception:
            pass

    def get_all_presets(self):
        return self._presets.copy()

    def get_preset(self, name):
        return self._presets.get(name)

    def get_preset_by_id(self, preset_id):
        for name, preset in self._presets.items():
            if preset.get("id") == preset_id:
                return name, preset
        return None, None

    def add_preset(self, name, preset_config):
        if "id" not in preset_config:
            preset_config["id"] = name.lower().replace(" ", "_")
        self._presets[name] = preset_config
        self._save_presets()

    def remove_preset(self, name):
        if name in self._presets and name not in DEFAULT_PRESETS:
            del self._presets[name]
            self._save_presets()
            return True
        return False

    def update_preset(self, name, new_config):
        if name in self._presets:
            self._presets[name].update(new_config)
            self._save_presets()

    def reset_to_defaults(self):
        self._presets = DEFAULT_PRESETS.copy()
        self._save_presets()

    def export_presets(self, filepath):
        try:
            with open(filepath, "w") as f:
                json.dump({"presets": self._presets}, f, indent=2)
            return True
        except Exception:
            return False

    def import_presets(self, filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            imported = data.get("presets", {})
            self._presets.update(imported)
            self._save_presets()
            return len(imported)
        except Exception:
            return 0

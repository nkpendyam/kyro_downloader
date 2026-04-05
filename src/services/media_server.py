"""Media server integration for Plex and Jellyfin."""
import json
import requests
from pathlib import Path
from typing import Any, Optional, List, Dict
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MediaServerConfig:
    def __init__(self, server_type: str, url: str, token: str, library_name: str = "Downloads") -> None:
        self.server_type = server_type.lower()
        self.url = url.rstrip("/")
        self.token = token
        self.library_name = library_name

    def to_dict(self) -> dict[str, str]:
        return {
            "server_type": self.server_type,
            "url": self.url,
            "token": self.token,
            "library_name": self.library_name,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MediaServerConfig":
        return cls(
            server_type=d.get("server_type", "plex"),
            url=d.get("url", ""),
            token=d.get("token", ""),
            library_name=d.get("library_name", "Downloads"),
        )


class MediaServerClient:
    SUPPORTED_TYPES = ["plex", "jellyfin"]

    def __init__(self, config: Optional[MediaServerConfig] = None) -> None:
        self.config = config
        self._state_file = Path.home() / ".config" / "kyro" / "media_server.json"
        self._configs: List[MediaServerConfig] = []
        self._loaded = set()
        self._load_configs()
        if config:
            config_key = f"{config.server_type}:{config.url}"
            if config_key not in self._loaded:
                self._configs.append(config)
                self._loaded.add(config_key)

    def _load_configs(self) -> None:
        try:
            if self._state_file.exists():
                with open(self._state_file, "r") as f:
                    data = json.load(f)
                self._configs = [MediaServerConfig.from_dict(c) for c in data.get("servers", [])]
                self._loaded = {f"{cfg.server_type}:{cfg.url}" for cfg in self._configs}
        except Exception as e:
            logger.warning(f"Failed to load media server configs: {e}")

    def _save_configs(self) -> None:
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_file, "w") as f:
                json.dump({"servers": [c.to_dict() for c in self._configs]}, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save media server configs: {e}")

    def add_server(self, config: MediaServerConfig) -> None:
        config_key = f"{config.server_type}:{config.url}"
        if config_key in self._loaded:
            return
        self._configs.append(config)
        self._loaded.add(config_key)
        self._save_configs()

    def remove_server(self, index: int) -> bool:
        if 0 <= index < len(self._configs):
            removed = self._configs.pop(index)
            self._loaded.discard(f"{removed.server_type}:{removed.url}")
            self._save_configs()
            return True
        return False

    def get_servers(self) -> List[MediaServerConfig]:
        return list(self._configs)

    def test_connection(self, config: Optional[MediaServerConfig] = None) -> bool:
        cfg = config or self.config
        if not cfg:
            return False
        try:
            if cfg.server_type == "plex":
                return self._test_plex(cfg)
            elif cfg.server_type == "jellyfin":
                return self._test_jellyfin(cfg)
            return False
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False

    def _test_plex(self, config: MediaServerConfig) -> bool:
        headers = {"X-Plex-Token": config.token, "Accept": "application/json"}
        r = requests.get(f"{config.url}/", headers=headers, timeout=10)
        return r.status_code == 200

    def _test_jellyfin(self, config: MediaServerConfig) -> bool:
        headers = {"X-Emby-Token": config.token}
        r = requests.get(f"{config.url}/System/Info/Public", headers=headers, timeout=10)
        return r.status_code == 200

    def scan_library(self, config: Optional[MediaServerConfig] = None) -> bool:
        cfg = config or self.config
        if not cfg:
            return False
        try:
            if cfg.server_type == "plex":
                return self._scan_plex(cfg)
            elif cfg.server_type == "jellyfin":
                return self._scan_jellyfin(cfg)
            return False
        except Exception as e:
            logger.error(f"Library scan failed: {e}")
            return False

    def _scan_plex(self, config: MediaServerConfig) -> bool:
        headers = {"X-Plex-Token": config.token}
        r = requests.get(f"{config.url}/library/sections", headers=headers, timeout=10)
        if r.status_code != 200:
            return False
        sections = r.json().get("MediaContainer", {}).get("Directory", [])
        for section in sections:
            if section.get("title") == config.library_name:
                key = section.get("key")
                scan_url = f"{config.url}/library/sections/{key}/refresh"
                r = requests.get(scan_url, headers=headers, timeout=10)
                return r.status_code == 200
        logger.warning(f"Library '{config.library_name}' not found")
        return False

    def _scan_jellyfin(self, config: MediaServerConfig) -> bool:
        headers = {"X-Emby-Token": config.token}
        r = requests.get(f"{config.url}/Library/VirtualFolders", headers=headers, timeout=10)
        if r.status_code != 200:
            return False
        folders = r.json()
        for folder in folders:
            if folder.get("Name") == config.library_name:
                refresh_url = f"{config.url}/Library/Refresh"
                r = requests.post(refresh_url, headers=headers, timeout=10)
                return r.status_code in (200, 204)
        logger.warning(f"Library '{config.library_name}' not found")
        return False

    def notify_new_media(self, file_path: str, config: Optional[MediaServerConfig] = None) -> bool:
        cfg = config or self.config
        if not cfg:
            return False
        try:
            if cfg.server_type == "plex":
                return self._notify_plex(cfg)
            elif cfg.server_type == "jellyfin":
                return self._notify_jellyfin(cfg)
            return False
        except Exception as e:
            logger.error(f"Media notification failed: {e}")
            return False

    def _notify_plex(self, config: MediaServerConfig) -> bool:
        return self._scan_plex(config)

    def _notify_jellyfin(self, config: MediaServerConfig) -> bool:
        return self._scan_jellyfin(config)

    def get_server_info(self, config: Optional[MediaServerConfig] = None) -> Optional[Dict[str, Any]]:
        cfg = config or self.config
        if not cfg:
            return None
        try:
            if cfg.server_type == "plex":
                return self._get_plex_info(cfg)
            elif cfg.server_type == "jellyfin":
                return self._get_jellyfin_info(cfg)
            return None
        except Exception as e:
            logger.warning(f"Failed to get server info: {e}")
            return None

    def _get_plex_info(self, config: MediaServerConfig) -> Dict[str, Any]:
        headers = {"X-Plex-Token": config.token, "Accept": "application/json"}
        r = requests.get(f"{config.url}/", headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json().get("MediaContainer", {})
        return {
            "type": "plex",
            "version": data.get("version", "unknown"),
            "friendly_name": data.get("friendlyName", "Plex Server"),
            "platform": data.get("platform", "unknown"),
        }

    def _get_jellyfin_info(self, config: MediaServerConfig) -> Dict[str, Any]:
        r = requests.get(f"{config.url}/System/Info/Public", timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "type": "jellyfin",
            "version": data.get("Version", "unknown"),
            "friendly_name": data.get("ServerName", "Jellyfin Server"),
            "platform": data.get("OperatingSystem", "unknown"),
        }

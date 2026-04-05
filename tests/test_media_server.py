"""Tests for media server integration service."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.media_server import MediaServerClient, MediaServerConfig


def test_media_server_config_roundtrip():
    cfg = MediaServerConfig("plex", "https://plex.local/", "token-1", "Downloads")
    restored = MediaServerConfig.from_dict(cfg.to_dict())

    assert restored.server_type == "plex"
    assert restored.url == "https://plex.local"
    assert restored.token == "token-1"
    assert restored.library_name == "Downloads"


def test_media_server_client_add_and_remove(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    client = MediaServerClient()
    cfg = MediaServerConfig("jellyfin", "https://jf.local", "token")
    client.add_server(cfg)

    servers = client.get_servers()
    assert len(servers) == 1
    assert servers[0].server_type == "jellyfin"

    assert client.remove_server(0) is True
    assert client.get_servers() == []


def test_media_server_test_connection_dispatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    cfg = MediaServerConfig("plex", "https://plex.local", "token")
    client = MediaServerClient(cfg)

    def _test_plex(_cfg: MediaServerConfig) -> bool:
        return True

    monkeypatch.setattr(client, "_test_plex", _test_plex)
    assert client.test_connection() is True


def test_media_server_scan_library_dispatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    cfg = MediaServerConfig("jellyfin", "https://jf.local", "token")
    client = MediaServerClient(cfg)

    def _scan_jellyfin(_cfg: MediaServerConfig) -> bool:
        return True

    monkeypatch.setattr(client, "_scan_jellyfin", _scan_jellyfin)
    assert client.scan_library() is True


def test_media_server_get_info_dispatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    cfg = MediaServerConfig("plex", "https://plex.local", "token")
    client = MediaServerClient(cfg)

    def _get_plex_info(_cfg: MediaServerConfig) -> dict[str, str]:
        return {"type": "plex", "version": "1.0"}

    monkeypatch.setattr(client, "_get_plex_info", _get_plex_info)
    info = client.get_server_info()
    assert info == {"type": "plex", "version": "1.0"}


def test_media_server_add_server_deduplicates_entries(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    cfg = MediaServerConfig("plex", "https://plex.local", "token")
    client = MediaServerClient(cfg)
    client.add_server(cfg)

    servers = client.get_servers()
    assert len(servers) == 1

"""Behavior tests for web route request forwarding."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("fastapi", reason="Web UI optional dependency")

from fastapi.testclient import TestClient

from src.ui.web.server import create_app
from src.ui.web import routes as web_routes


class _FakeManager:
    """Minimal manager stub for route forwarding checks."""

    def __init__(self) -> None:
        self.queue_calls: list[dict[str, Any]] = []
        self.config: dict[str, Any] = {}

    def queue_download(self, **kwargs: Any) -> Any:
        self.queue_calls.append(kwargs)
        return SimpleNamespace(task_id="t-1", url=kwargs["url"], status=SimpleNamespace(value="pending"))


def test_download_route_forwards_advanced_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """/api/download should forward quality/audio/subtitle/sponsorblock/template settings."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(general=SimpleNamespace(output_path="downloads"))

    monkeypatch.setattr(web_routes, "_manager_instance", fake_manager)
    monkeypatch.setattr(web_routes, "_config_instance", fake_config)
    monkeypatch.setattr(web_routes, "_ensure_executor_running", lambda: None)

    app = create_app()
    client = TestClient(app)

    payload: dict[str, Any] = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "only_audio": True,
        "quality": "720p",
        "hdr": False,
        "dolby": True,
        "audio_format": "opus",
        "audio_quality": "160",
        "audio_selector": "251",
        "subtitles": {
            "enabled": True,
            "languages": ["en", "es"],
            "embed": False,
            "auto_generated": True,
            "format": "vtt",
        },
        "sponsorblock": True,
        "output_template": "%(uploader)s/%(title)s.%(ext)s",
    }

    response = client.post("/api/download", json=payload)
    assert response.status_code == 200

    call = fake_manager.queue_calls[-1]
    assert call["quality"] == "720p"
    assert call["audio_format"] == "opus"
    assert call["audio_quality"] == "160"
    assert call["audio_selector"] == "251"
    assert call["subtitles"]["languages"] == ["en", "es"]
    assert call["sponsorblock"]["enabled"] is True
    assert call["output_template"] == "%(uploader)s/%(title)s.%(ext)s"


def test_batch_route_forwards_audio_and_subtitles(monkeypatch: pytest.MonkeyPatch) -> None:
    """/api/batch should preserve audio/subtitle settings for each queued URL."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(general=SimpleNamespace(output_path="downloads"))

    monkeypatch.setattr(web_routes, "_manager_instance", fake_manager)
    monkeypatch.setattr(web_routes, "_config_instance", fake_config)
    monkeypatch.setattr(web_routes, "_ensure_executor_running", lambda: None)

    app = create_app()
    client = TestClient(app)

    payload: dict[str, Any] = {
        "urls": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=BaW_jenozKc",
        ],
        "only_audio": True,
        "audio_format": "aac",
        "audio_quality": "128",
        "subtitles": True,
        "workers": 2,
    }

    response = client.post("/api/batch", json=payload)
    assert response.status_code == 200
    assert len(fake_manager.queue_calls) == 2
    assert all(call["audio_format"] == "aac" for call in fake_manager.queue_calls)
    assert all(call["audio_quality"] == "128" for call in fake_manager.queue_calls)
    assert all(call["subtitles"]["enabled"] is True for call in fake_manager.queue_calls)

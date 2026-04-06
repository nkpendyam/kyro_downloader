"""Behavior tests for web route request forwarding."""

from __future__ import annotations

import threading
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

    def get_status(self) -> dict[str, Any]:
        return {
            "queue_size": 0,
            "pending": 0,
            "active": 0,
            "completed": 0,
            "failed": 0,
            "progress": 0,
            "executor_running": False,
        }

    def execute(self) -> None:
        """No-op for web route tests."""
        pass

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update config in-place without destroying state."""
        self.config.update(new_config)


def test_get_manager_wires_plugin_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_config = SimpleNamespace(model_dump=lambda: {}, general=SimpleNamespace(output_path="downloads"))

    class _FakeDownloadManager:
        def __init__(self, _config: dict[str, Any], plugin_loader: Any = None) -> None:
            self.plugin_loader = plugin_loader

    monkeypatch.setattr(web_routes, "load_config", lambda: fake_config)
    monkeypatch.setattr(web_routes, "DownloadManager", _FakeDownloadManager)

    state = {
        "manager_lock": threading.Lock(),
        "manager_instance": None,
        "config_instance": None,
        "executor_started": threading.Event(),
        "rate_limit_lock": threading.Lock(),
        "rate_limit_state": {},
        "rate_limit_max_buckets": 10000,
        "executor": None,
    }

    manager = web_routes.get_manager(state)
    assert manager.plugin_loader is not None


def _make_web_state(fake_manager: Any, fake_config: Any) -> dict[str, Any]:
    """Create a web_state dict for testing."""
    state = {
        "manager_lock": threading.Lock(),
        "manager_instance": fake_manager,
        "config_instance": fake_config,
        "executor_started": threading.Event(),
        "rate_limit_lock": threading.Lock(),
        "rate_limit_state": {},
        "rate_limit_max_buckets": 10000,
        "executor": None,
    }
    state["executor_started"].set()
    return state


def test_download_route_forwards_advanced_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """/api/download should forward quality/audio/subtitle/sponsorblock/template settings."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(general=SimpleNamespace(output_path="downloads"))
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
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
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
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


def test_api_auth_rejects_missing_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """When web.api_token is configured, /api routes should require auth."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(
        general=SimpleNamespace(output_path="downloads"),
        web=SimpleNamespace(api_token="secret-token"),
    )
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.get("/api/status")
    assert response.status_code == 401


def test_api_auth_allows_valid_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid bearer token should allow access to protected /api routes."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(
        general=SimpleNamespace(output_path="downloads"),
        web=SimpleNamespace(api_token="secret-token"),
    )
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.get("/api/status", headers={"Authorization": "Bearer secret-token"})
    assert response.status_code == 200


def test_config_update_rejects_missing_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """PUT /api/config should require auth when web.api_token is configured."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(
        general=SimpleNamespace(output_path="downloads"),
        web=SimpleNamespace(api_token="secret-token"),
    )
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.put(
        "/api/config",
        json={"section": "general", "key": "output_path", "value": "downloads"},
    )
    assert response.status_code == 401


def test_download_route_applies_voice_optimized_preset(monkeypatch: pytest.MonkeyPatch) -> None:
    """/api/download should translate preset into audio/subtitle/output settings."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(general=SimpleNamespace(output_path="downloads"))
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.post(
        "/api/download",
        json={
            "url": "https://example.com/video",
            "preset": "voice-optimized",
            "priority": "normal",
        },
    )

    assert response.status_code == 200
    queued = fake_manager.queue_calls[0]
    assert queued["only_audio"] is True
    assert queued["audio_format"] == "opus"
    assert queued["audio_quality"] == "96"
    assert queued["subtitles"]["enabled"] is True
    assert queued["output_template"] == "%(uploader)s/%(upload_date)s_%(title)s.%(ext)s"


def test_download_route_normalizes_quality_and_forwards_hdr_dolby(monkeypatch: pytest.MonkeyPatch) -> None:
    """/api/download should pass normalized quality with hdr/dolby flags."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(general=SimpleNamespace(output_path="downloads"))
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.post(
        "/api/download",
        json={
            "url": "https://example.com/video",
            "quality": "4k",
            "hdr": True,
            "dolby": True,
        },
    )

    assert response.status_code == 200
    queued = fake_manager.queue_calls[0]
    assert queued["quality"] == "4k"
    assert queued["hdr"] is True
    assert queued["dolby"] is True


def test_download_route_rejects_output_path_outside_download_dir(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """/api/download should reject output paths outside configured download directory."""
    fake_manager = _FakeManager()
    base_dir = tmp_path / "downloads"
    base_dir.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()

    fake_config = SimpleNamespace(general=SimpleNamespace(output_path=str(base_dir)))
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.post(
        "/api/download",
        json={
            "url": "https://example.com/video",
            "output_path": str(outside_dir),
        },
    )

    assert response.status_code == 403
    assert fake_manager.queue_calls == []


def test_download_route_returns_429_when_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    """/api/download should return 429 when limiter blocks request."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(general=SimpleNamespace(output_path="downloads"))
    web_state = _make_web_state(fake_manager, fake_config)

    def _raise_rate(*_args: Any, **_kwargs: Any) -> None:
        from fastapi import HTTPException

        raise HTTPException(status_code=429, detail="Too Many Requests", headers={"Retry-After": "30"})

    monkeypatch.setattr(web_routes, "_check_rate_limit", _raise_rate)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.post("/api/download", json={"url": "https://example.com/video"})
    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "30"


def test_config_update_returns_429_when_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    """PUT /api/config should surface limiter response with Retry-After."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(
        general=SimpleNamespace(output_path="downloads"),
        web=SimpleNamespace(api_token="secret-token"),
    )
    web_state = _make_web_state(fake_manager, fake_config)

    def _raise_rate(*_args: Any, **_kwargs: Any) -> None:
        from fastapi import HTTPException

        raise HTTPException(status_code=429, detail="Too Many Requests", headers={"Retry-After": "15"})

    monkeypatch.setattr(web_routes, "_check_rate_limit", _raise_rate)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.put(
        "/api/config",
        json={"section": "general", "key": "output_path", "value": "downloads"},
        headers={"Authorization": "Bearer secret-token"},
    )
    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "15"


def test_v1_status_route_is_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """/api/v1/status should resolve to the primary versioned API."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(general=SimpleNamespace(output_path="downloads"))
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.get("/api/v1/status")
    assert response.status_code == 200


def test_legacy_api_route_includes_deprecation_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Legacy /api/* responses should include deprecation migration headers."""
    fake_manager = _FakeManager()
    fake_config = SimpleNamespace(general=SimpleNamespace(output_path="downloads"))
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.headers.get("Deprecation") == "true"
    assert response.headers.get("Link") == '</api/v1>; rel="successor-version"'


def test_rate_limit_counts_rejected_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rejected requests must also be counted in limiter state."""
    state = _make_web_state(_FakeManager(), SimpleNamespace(general=SimpleNamespace(output_path="downloads")))
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as first:
        web_routes._check_rate_limit("test_bucket", limit=0, state=state)
    assert first.value.status_code == 429
    assert len(state["rate_limit_state"]["test_bucket"]) == 1

    with pytest.raises(HTTPException) as second:
        web_routes._check_rate_limit("test_bucket", limit=0, state=state)
    assert second.value.status_code == 429
    assert len(state["rate_limit_state"]["test_bucket"]) == 2


def test_rate_limit_state_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Limiter bucket state should stay bounded under unique-bucket traffic."""
    state = _make_web_state(_FakeManager(), SimpleNamespace(general=SimpleNamespace(output_path="downloads")))
    state["rate_limit_max_buckets"] = 3

    for index in range(6):
        web_routes._check_rate_limit(f"bucket-{index}", limit=10, state=state)

    assert len(state["rate_limit_state"]) <= 3


def test_routes_fail_gracefully_without_web_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Routes should return 503 when web_state is not initialized."""
    app = create_app()
    app.state.web_state = None
    client = TestClient(app)

    response = client.get("/api/status")
    assert response.status_code == 503


def test_config_update_preserves_queued_items(monkeypatch: pytest.MonkeyPatch) -> None:
    """PUT /api/config should update config without destroying the manager and losing queued items."""
    from src.config.schema import AppConfig

    fake_manager = _FakeManager()
    fake_manager.queue = SimpleNamespace(items=["queued-item-1", "queued-item-2"])
    fake_config = AppConfig(web={"api_token": "secret-token"})
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    initial_queue_items = fake_manager.queue.items.copy()

    response = client.put(
        "/api/config",
        json={"section": "general", "key": "output_path", "value": "new-downloads"},
        headers={"Authorization": "Bearer secret-token"},
    )
    assert response.status_code == 200

    assert fake_manager.queue.items == initial_queue_items
    assert web_state["manager_instance"] is fake_manager


def test_config_update_restricted_key_requires_admin_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Restricted keys must reject non-admin token updates."""
    from src.config.schema import AppConfig

    fake_manager = _FakeManager()
    fake_manager.config["web_admin_token"] = "admin-token"
    fake_config = AppConfig(web={"api_token": "secret-token"})
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.put(
        "/api/config",
        json={"section": "web", "key": "api_token", "value": "new-token"},
        headers={"Authorization": "Bearer secret-token"},
    )
    assert response.status_code == 403


def test_config_update_restricted_key_allows_admin_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Restricted keys should allow update when admin token matches."""
    from src.config.schema import AppConfig

    fake_manager = _FakeManager()
    fake_config = AppConfig(web={"api_token": "secret-token"})
    web_state = _make_web_state(fake_manager, fake_config)

    app = create_app()
    app.state.web_state = web_state
    client = TestClient(app)

    response = client.put(
        "/api/config",
        json={"section": "web", "key": "api_token", "value": "new-token"},
        headers={"Authorization": "Bearer secret-token"},
    )
    assert response.status_code == 200

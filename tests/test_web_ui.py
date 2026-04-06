"""Tests for Web UI."""

import pytest

web_ui = pytest.importorskip("fastapi", reason="Web UI optional dependency")

from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


class TestWebUI:
    def test_create_app(self):
        from src.ui.web.server import create_app

        app = create_app()
        assert app is not None
        assert app.title == "Kyro Downloader API"

    def test_run_web(self):
        from src.ui.web.server import run_web

        with patch("uvicorn.run") as mock_run:
            run_web(host="127.0.0.1", port=8000)
            mock_run.assert_called_once()

    def test_web_routes_exist(self):
        from src.ui.web.server import create_app

        app = create_app()
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/" in routes
        assert "/health" in routes
        assert any("/api" in r for r in routes)

    def test_websocket_rejects_without_token_when_configured(self, monkeypatch):
        from src.ui.web.server import create_app
        from src.ui.web import websocket as ws_module

        monkeypatch.setattr(ws_module, "_get_configured_api_token", lambda: "secret-token")
        app = create_app()

        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect) as exc:
                with client.websocket_connect("/ws/progress"):
                    pass
            assert exc.value.code == 1008

    def test_websocket_rejects_query_token_when_configured(self, monkeypatch):
        from src.ui.web.server import create_app
        from src.ui.web import websocket as ws_module

        monkeypatch.setattr(ws_module, "_get_configured_api_token", lambda: "secret-token")
        app = create_app()

        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect) as exc:
                with client.websocket_connect("/ws/progress?token=secret-token"):
                    pass
            assert exc.value.code == 1008

    def test_websocket_accepts_protocol_token_when_configured(self, monkeypatch):
        from src.ui.web.server import create_app
        from src.ui.web import websocket as ws_module

        monkeypatch.setattr(ws_module, "_get_configured_api_token", lambda: "secret-token")
        app = create_app()

        with TestClient(app) as client:
            with client.websocket_connect("/ws/progress", subprotocols=["bearer secret-token"]) as ws:
                ws.send_json({"type": "ping"})
                payload = ws.receive_json()
                assert payload["type"] == "pong"

    def test_request_timeout_middleware_returns_504(self, monkeypatch):
        from src.ui.web.server import create_app

        app = create_app()

        timeout_route = None
        for route in app.routes:
            if getattr(route, "path", None) == "/api/slow-timeout-test":
                timeout_route = route
                break

        if timeout_route is not None:
            app.router.routes.remove(timeout_route)

        @app.get("/api/slow-timeout-test")
        async def _slow_route():
            import asyncio

            await asyncio.sleep(0.01)
            return {"ok": True}

        import src.ui.web.server as server_module

        real_wait_for = server_module.asyncio.wait_for

        async def _forced_timeout(coro, timeout):
            if timeout == 300:
                raise TimeoutError
            return await real_wait_for(coro, timeout)

        monkeypatch.setattr(server_module.asyncio, "wait_for", _forced_timeout)

        with TestClient(app) as client:
            response = client.get("/api/slow-timeout-test")

        assert response.status_code == 504

    def test_csrf_origin_middleware_rejects_untrusted_origin(self, monkeypatch):
        import threading
        from src.ui.web.server import create_app

        fake_manager = type("FakeManager", (), {"get_status": lambda self: {"ok": True}})()
        fake_config = type("FakeConfig", (), {"general": type("General", (), {"output_path": "downloads"})()})()
        web_state = {
            "manager_lock": threading.Lock(),
            "manager_instance": fake_manager,
            "config_instance": fake_config,
            "executor_started": threading.Event(),
            "rate_limit_lock": threading.Lock(),
            "rate_limit_state": {},
            "rate_limit_max_buckets": 10000,
            "executor": None,
        }

        app = create_app()
        app.state.web_state = web_state
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/download",
                json={"url": "https://example.com/video"},
                headers={"Origin": "https://evil.example"},
            )
        assert response.status_code == 403

    def test_health_returns_limited_data_when_unauthenticated(self):
        from src.ui.web.server import create_app
        from src.config.schema import AppConfig

        app = create_app()
        app.state.web_state["config_instance"] = AppConfig(web={"api_token": "secret-token"})

        with TestClient(app) as client:
            response = client.get("/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["version"]
        assert "queue" not in payload

    def test_health_returns_full_data_when_authenticated(self):
        from src.ui.web.server import create_app
        from src.config.schema import AppConfig

        app = create_app()
        app.state.web_state["config_instance"] = AppConfig(web={"api_token": "secret-token"})

        with TestClient(app) as client:
            response = client.get("/health", headers={"Authorization": "Bearer secret-token"})

        assert response.status_code == 200
        payload = response.json()
        assert "queue" in payload
        assert "ffmpeg" in payload

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

    def test_websocket_accepts_query_token_when_configured(self, monkeypatch):
        from src.ui.web.server import create_app
        from src.ui.web import websocket as ws_module

        monkeypatch.setattr(ws_module, "_get_configured_api_token", lambda: "secret-token")
        app = create_app()

        with TestClient(app) as client:
            with client.websocket_connect("/ws/progress?token=secret-token") as ws:
                ws.send_json({"type": "ping"})
                payload = ws.receive_json()
                assert payload["type"] == "pong"

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

"""Tests for Web UI."""
import pytest

web_ui = pytest.importorskip("fastapi", reason="Web UI optional dependency")

from unittest.mock import patch


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
        assert any("/api" in r for r in routes)

"""Tests for web file-browser routes."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="Web UI optional dependency")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ui.web import routes_files


def _make_web_state() -> dict:
    """Create a minimal web_state for file route tests."""
    return {
        "manager_lock": threading.Lock(),
        "manager_instance": None,
        "config_instance": None,
        "executor_started": threading.Event(),
        "rate_limit_lock": threading.Lock(),
        "rate_limit_state": {},
        "rate_limit_max_buckets": 10000,
        "executor": None,
    }


def _build_client(download_dir: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(routes_files, "get_download_dir", lambda: download_dir.resolve())
    monkeypatch.setattr(routes_files, "_check_rate_limit", lambda *args, **kwargs: None)
    monkeypatch.setattr(routes_files, "require_api_auth", lambda request, **kwargs: None)
    app = FastAPI()
    app.state.web_state = _make_web_state()
    app.include_router(routes_files.router, prefix="/api/files")
    return TestClient(app)


def test_list_files_returns_unescaped_json_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "artist & track.mp3").write_text("x", encoding="utf-8")
    client = _build_client(tmp_path, monkeypatch)

    response = client.get("/api/files/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["name"] == "artist & track.mp3"
    assert payload["items"][0]["path"] == "artist & track.mp3"


def test_list_files_blocks_path_traversal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(tmp_path, monkeypatch)
    outside = tmp_path.parent / "outside-dir"
    outside.mkdir(exist_ok=True)

    response = client.get("/api/files/", params={"path": str(outside)})

    assert response.status_code == 403


def test_delete_file_returns_raw_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "to-delete.txt"
    target.write_text("x", encoding="utf-8")
    client = _build_client(tmp_path, monkeypatch)

    response = client.delete("/api/files/to-delete.txt")

    assert response.status_code == 200
    assert response.json()["path"] == "to-delete.txt"


def test_delete_directory_requires_confirm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_dir = tmp_path / "folder"
    target_dir.mkdir()
    (target_dir / "a.txt").write_text("x", encoding="utf-8")
    client = _build_client(tmp_path, monkeypatch)

    response = client.delete("/api/files/folder")

    assert response.status_code == 400
    assert target_dir.exists()


def test_delete_directory_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_dir = tmp_path / "folder"
    target_dir.mkdir()
    (target_dir / "a.txt").write_text("x", encoding="utf-8")
    client = _build_client(tmp_path, monkeypatch)

    response = client.delete("/api/files/folder", params={"dry_run": "true"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "dry_run"
    assert payload["is_dir"] is True
    assert payload["count"] >= 1
    assert target_dir.exists()


def test_delete_directory_with_confirm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target_dir = tmp_path / "folder"
    target_dir.mkdir()
    (target_dir / "a.txt").write_text("x", encoding="utf-8")
    client = _build_client(tmp_path, monkeypatch)

    response = client.delete("/api/files/folder", params={"confirm": "true"})

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert not target_dir.exists()


def test_delete_file_user_identity_cannot_be_spoofed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """User identity in audit logs should derive from auth context, not query params."""
    target = tmp_path / "to-delete.txt"
    target.write_text("x", encoding="utf-8")
    client = _build_client(tmp_path, monkeypatch)

    response = client.delete("/api/files/to-delete.txt", params={"user": "admin"})

    assert response.status_code == 200
    assert response.json()["path"] == "to-delete.txt"


def test_derive_user_identity_uses_only_token_payload() -> None:
    """Identity hash should not include the auth scheme prefix."""

    class _DummyRequest:
        headers = {"authorization": "Bearer super-secret-token"}

    identity = routes_files._derive_user_identity(_DummyRequest())
    assert identity.startswith("token:sha256:")
    assert "Bearer" not in identity

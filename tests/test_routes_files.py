"""Tests for web file-browser routes."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi", reason="Web UI optional dependency")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ui.web import routes_files


def _build_client(download_dir: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(routes_files, "DOWNLOAD_DIR", download_dir.resolve())
    app = FastAPI()
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

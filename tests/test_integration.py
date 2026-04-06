"""End-to-end style integration test using mocked yt-dlp."""

from __future__ import annotations

from pathlib import Path

from src.core.download_manager import DownloadManager
from src.services.archive import DownloadArchive


def test_full_pipeline_url_to_download_and_archive(monkeypatch, tmp_path) -> None:
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    class _Info:
        title = "Integration Video"
        is_playlist = False

    def _fake_get_video_info(_url: str, **_kwargs):
        return _Info()

    progress_events: list[dict[str, float | str]] = []

    def _fake_download_single(url: str, output_path: str, **kwargs):
        hook = kwargs.get("progress_hook")
        if hook:
            payload = {"status": "downloading", "_percent_str": "100%", "_speed_str": "1MiB/s"}
            progress_events.append(payload)
            hook(payload)
        file_path = Path(output_path) / "integration.mp4"
        file_path.write_text(f"downloaded:{url}", encoding="utf-8")
        return [str(file_path)]

    monkeypatch.setattr("src.core.download_manager.get_video_info", _fake_get_video_info)
    monkeypatch.setattr("src.core.download_manager.download_single", _fake_download_single)

    manager = DownloadManager({"output_path": str(output_dir)})
    info, _ = manager.prepare_download("https://example.com/video", str(output_dir))
    assert info.title == "Integration Video"

    item = manager.queue_download("https://example.com/video", output_path=str(output_dir))
    assert item.url == "https://example.com/video"

    downloaded_paths = manager.download_now("https://example.com/video", output_path=str(output_dir))
    assert downloaded_paths
    assert Path(downloaded_paths[0]).exists()
    assert manager.queue.get_item(item.task_id) is not None

    archive = DownloadArchive(str(tmp_path / "archive.json"))
    archive.add("integration-id", info.title, "https://example.com/video", downloaded_paths[0], size=1)
    assert archive.contains("integration-id") is True

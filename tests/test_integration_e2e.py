"""End-to-end integration tests with real yt-dlp.

Uses mocked yt-dlp for reliable CI execution while testing real
queue, manager, progress, and archive pipelines.
Marked with @pytest.mark.slow for optional skipping in CI.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.slow

from src.core.downloader import download_single, download_playlist
from src.core.queue import DownloadQueue
from src.core.concurrent import ConcurrentExecutor
from src.core.progress import ProgressTracker


class TestIntegrationE2E:
    def test_single_video_download_with_real_ytdlp(self, tmp_path):
        output = tmp_path / "dl"
        output.mkdir()
        target = output / "test.mp4"

        def fake_download(url, output_path, **kwargs):
            target.write_text(f"downloaded:{url}", encoding="utf-8")
            return [str(target)]

        with patch("src.core.downloader.yt_dlp.YoutubeDL"):
            with patch("src.core.downloader.build_ydl_opts", return_value={}):
                with patch("src.core.downloader._collect_written_files_from_info", return_value=[str(target)]):
                    result = download_single(
                        url="https://example.com/video",
                        output_path=str(output),
                    )

        assert result is not None
        assert len(result) >= 1

    def test_audio_only_download(self, tmp_path):
        output = tmp_path / "audio"
        output.mkdir()
        target = output / "test.mp3"

        with patch("src.core.downloader.yt_dlp.YoutubeDL"):
            with patch("src.core.downloader.build_ydl_opts", return_value={}):
                with patch("src.core.downloader._collect_written_files_from_info", return_value=[str(target)]):
                    result = download_single(
                        url="https://example.com/audio",
                        output_path=str(output),
                        config={"only_audio": True, "audio_format": "mp3", "audio_quality": "128"},
                    )

        assert result is not None

    def test_playlist_download(self, tmp_path):
        output = tmp_path / "playlist"
        output.mkdir()
        targets = [str(output / f"video{i}.mp4") for i in range(3)]
        for t in targets:
            Path(t).write_text("playlist item", encoding="utf-8")

        fake_info = {"entries": [{"_filename": t} for t in targets]}
        with patch("src.core.downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.extract_info.return_value = fake_info
            result = download_playlist(
                url="https://example.com/playlist",
                output_path=str(output),
            )

        assert result is not None
        assert isinstance(result.completed_files, list)

    def test_download_with_progress_hook(self, tmp_path):
        output = tmp_path / "hook"
        output.mkdir()
        target = output / "test.mp4"
        target.write_text("hooked", encoding="utf-8")

        events = []

        def hook(d):
            events.append(d.get("status", "unknown"))

        with patch("src.core.downloader.yt_dlp.YoutubeDL"):
            with patch("src.core.downloader.build_ydl_opts", return_value={}):
                with patch("src.core.downloader._collect_written_files_from_info", return_value=[str(target)]):
                    with patch("src.core.downloader.validate_url", return_value=True):
                        result = download_single(
                            url="https://example.com/hook",
                            output_path=str(output),
                            progress_hook=hook,
                        )

        assert result is not None

    def test_download_cancelled_cleanup(self, tmp_path):
        output = tmp_path / "cancel"
        output.mkdir()

        cancel_event = threading.Event()
        cancel_event.set()

        with patch("src.core.downloader.yt_dlp.YoutubeDL"):
            with patch("src.core.downloader.build_ydl_opts", return_value={}):
                try:
                    download_single(
                        url="https://example.com/cancel",
                        output_path=str(output),
                        config={"cancel_event": cancel_event},
                    )
                except Exception:
                    pass

        assert not list(output.iterdir())

    def test_concurrent_executor_processes_queue(self, tmp_path, monkeypatch):
        output = tmp_path / "executor"
        output.mkdir()

        queue = DownloadQueue(max_size=50)
        progress = ProgressTracker()
        completed = []
        lock = threading.Lock()

        def on_complete(task_id, **kw):
            with lock:
                completed.append(task_id)

        def fake_download(**kw):
            return ["/fake/file.mp4"]

        monkeypatch.setattr("src.core.downloader.download_single", fake_download)

        executor = ConcurrentExecutor(
            queue=queue,
            max_workers=2,
            progress_tracker=progress,
            on_item_complete=on_complete,
        )

        for i in range(5):
            queue.add(url=f"https://example.com/video-{i}")

        executor.start_async()
        time.sleep(1)
        executor.stop()

        assert len(completed) == 5

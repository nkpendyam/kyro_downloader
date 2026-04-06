"""Tests for download_manager module."""

from unittest.mock import patch, MagicMock
from src.core.download_manager import DownloadManager


class TestDownloadManager:
    def test_init(self):
        dm = DownloadManager()
        assert dm.queue is not None
        assert dm.progress is not None
        assert dm.stats is not None

    def test_init_with_config(self):
        config = {"output_path": "/tmp", "concurrent_workers": 5}
        dm = DownloadManager(config)
        assert dm.config["output_path"] == "/tmp"

    def test_prepare_download_validates_url(self):
        dm = DownloadManager()
        try:
            dm.prepare_download("not-a-url")
        except ValueError as e:
            assert "Invalid URL" in str(e)

    def test_queue_download(self):
        dm = DownloadManager()
        with patch.object(dm, "prepare_download", return_value=MagicMock(title="Test")):
            item = dm.queue_download("https://youtube.com/watch?v=abc", output_path="/tmp")
            assert item.url == "https://youtube.com/watch?v=abc"

    def test_queue_batch(self):
        dm = DownloadManager()
        with patch.object(dm, "queue_download") as mock:
            mock.return_value = MagicMock()
            dm.queue_batch(["https://a.com", "https://b.com"])
            assert mock.call_count == 2

    def test_execute_empty_queue(self):
        dm = DownloadManager()
        dm.execute()  # Should not crash
        assert dm._executor is None

    def test_get_status(self):
        dm = DownloadManager()
        status = dm.get_status()
        assert "queue_size" in status
        assert "pending" in status
        assert "active" in status
        assert "completed" in status
        assert "failed" in status

    def test_stop(self):
        dm = DownloadManager()
        dm._executor = MagicMock()
        dm.stop()
        dm._executor.stop.assert_called_once()

    def test_download_now_forwards_progress_hook(self):
        dm = DownloadManager()

        def hook(_data):
            return None

        with patch("src.core.download_manager.validate_output_path", return_value="/tmp"):
            with patch("src.core.download_manager.download_single", return_value="/tmp") as mock_download:
                with patch.object(dm.plugin_loader, "fire_hook"):
                    with patch("src.core.download_manager.notify_download_complete"):
                        dm.download_now(
                            "https://youtube.com/watch?v=abc123",
                            output_path="/tmp",
                            progress_hook=hook,
                        )

        assert mock_download.call_args.kwargs["progress_hook"] is hook

    def test_queue_control_methods(self):
        dm = DownloadManager()
        item = dm.queue.add("https://youtube.com/watch?v=abc")

        assert dm.pause_queue(item.task_id) is True
        assert dm.resume_queue(item.task_id) is True
        assert dm.cancel_queue(item.task_id) is True

    def test_queue_status_and_stats_methods(self):
        dm = DownloadManager()
        status = dm.get_queue_status()
        stats = dm.get_queue_stats()

        assert "queue_size" in status
        assert "queue" in stats
        assert "progress" in stats

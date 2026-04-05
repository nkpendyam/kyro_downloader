"""Tests for ytdlp_updater module."""
from unittest.mock import patch, MagicMock
from src.utils.ytdlp_updater import check_for_update, update_ytdlp, get_current_version, get_latest_version


class TestYtdlpUpdater:
    @patch("importlib.metadata.version")
    def test_get_current_version(self, mock_version):
        mock_version.return_value = "2024.1.1"
        version = get_current_version()
        assert version == "2024.1.1"

    @patch("importlib.metadata.version")
    def test_get_current_version_error(self, mock_version):
        mock_version.side_effect = Exception("not found")
        version = get_current_version()
        assert version is None

    @patch("requests.get")
    def test_get_latest_version(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"info": {"version": "2024.2.1"}}
        mock_get.return_value = mock_resp
        version = get_latest_version()
        assert version == "2024.2.1"

    @patch("requests.get")
    def test_get_latest_version_error(self, mock_get):
        mock_get.side_effect = Exception("network error")
        version = get_latest_version()
        assert version is None

    @patch("src.utils.ytdlp_updater.get_current_version")
    @patch("src.utils.ytdlp_updater.get_latest_version")
    def test_check_for_update_available(self, mock_latest, mock_current):
        mock_current.return_value = "2024.1.1"
        mock_latest.return_value = "2024.2.1"
        result = check_for_update()
        assert result["update_available"] is True

    @patch("src.utils.ytdlp_updater.get_current_version")
    @patch("src.utils.ytdlp_updater.get_latest_version")
    def test_check_for_update_not_available(self, mock_latest, mock_current):
        mock_current.return_value = "2024.2.1"
        mock_latest.return_value = "2024.2.1"
        result = check_for_update()
        assert result["update_available"] is False

    @patch("src.utils.ytdlp_updater.get_current_version")
    @patch("src.utils.ytdlp_updater.get_latest_version")
    def test_check_for_update_missing_version(self, mock_latest, mock_current):
        mock_current.return_value = None
        mock_latest.return_value = "2024.2.1"
        result = check_for_update()
        assert result["update_available"] is False

    @patch("subprocess.run")
    def test_update_ytdlp_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = update_ytdlp()
        assert result is True

    @patch("subprocess.run")
    def test_update_ytdlp_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        result = update_ytdlp()
        assert result is False

    @patch("subprocess.run")
    def test_update_ytdlp_timeout(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 120)
        result = update_ytdlp()
        assert result is False

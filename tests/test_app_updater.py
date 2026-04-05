"""Tests for app_updater module."""
from unittest.mock import patch, MagicMock
from src.utils.app_updater import get_latest_release, check_for_update, get_platform_asset, download_and_update


class TestAppUpdater:
    @patch("requests.get")
    def test_get_latest_release(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"tag_name": "v1.0.4", "name": "v1.0.4", "body": "notes", "html_url": "http://example.com", "assets": [{"name": "test.exe", "browser_download_url": "http://example.com/test.exe", "size": 1000}]}
        mock_get.return_value = mock_resp
        release = get_latest_release()
        assert release["tag_name"] == "1.0.4"

    @patch("requests.get")
    def test_get_latest_release_error(self, mock_get):
        mock_get.side_effect = Exception("network error")
        release = get_latest_release()
        assert release is None

    @patch("src.utils.app_updater.get_current_version")
    @patch("src.utils.app_updater.get_latest_release")
    def test_check_for_update_available(self, mock_release, mock_current):
        mock_current.return_value = "1.0.0"
        mock_release.return_value = {"tag_name": "1.0.4", "name": "v1.0.4", "body": "notes", "html_url": "http://example.com", "assets": [{"name": "test.exe", "url": "http://example.com/test.exe", "size": 1000}]}
        result = check_for_update()
        assert result["update_available"] is True

    @patch("src.utils.app_updater.get_current_version")
    @patch("src.utils.app_updater.get_latest_release")
    def test_check_for_update_not_available(self, mock_release, mock_current):
        mock_current.return_value = "1.0.4"
        mock_release.return_value = {"tag_name": "1.0.4", "name": "v1.0.4", "body": "notes", "html_url": "http://example.com", "assets": []}
        result = check_for_update()
        assert result["update_available"] is False

    def test_get_platform_asset_windows(self):
        assets = [{"name": "test.exe", "url": "http://example.com/test.exe", "size": 1000}]
        with patch("sys.platform", "win32"):
            result = get_platform_asset(assets)
            assert result["name"] == "test.exe"

    def test_get_platform_asset_no_match(self):
        assets = [{"name": "test.txt", "url": "http://example.com/test.txt", "size": 1000}]
        with patch("sys.platform", "win32"):
            result = get_platform_asset(assets)
            assert result is None

    @patch("requests.get")
    def test_download_and_update(self, mock_get, tmp_path):
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [b"fake content"]
        mock_get.return_value = mock_resp
        with patch("tempfile.gettempdir", return_value=str(tmp_path)):
            result = download_and_update("http://example.com/test.exe")
            assert result is not None

    @patch("requests.get")
    def test_download_and_update_error(self, mock_get):
        mock_get.side_effect = Exception("download error")
        result = download_and_update("http://example.com/test.exe")
        assert result is None

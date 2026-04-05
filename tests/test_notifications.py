"""Tests for notification utilities."""
from unittest.mock import patch, MagicMock
from src.utils.notifications import send_notification, notify_download_complete, notify_download_failed


class TestSendNotification:
    @patch("platform.system", return_value="Windows")
    def test_windows_notification(self, mock_system):
        mock_notify = MagicMock()
        with patch.dict("sys.modules", {"plyer": MagicMock(), "plyer.notification": mock_notify}):
            result = send_notification("Test", "Message")
            assert result is True

    @patch("platform.system", return_value="Linux")
    def test_linux_notification(self, mock_system):
        with patch("subprocess.run") as mock_run:
            result = send_notification("Test", "Message")
            assert result is True
            mock_run.assert_called_once()

    @patch("platform.system", return_value="Darwin")
    def test_macos_notification_escapes_quotes(self, mock_system):
        with patch("subprocess.run") as mock_run:
            send_notification("Test", 'Message with "quotes"')
            call_args = mock_run.call_args[0][0]
            assert "display notification" in call_args[2]
            assert "item 1 of argv" in call_args[2]
            assert call_args[3] == 'Message with "quotes"'
            assert call_args[4] == "Test"

    @patch("platform.system", return_value="Windows")
    def test_fallback_on_failure(self, mock_system):
        with patch.dict("sys.modules", {"plyer": MagicMock()}):
            with patch("plyer.notification.notify", side_effect=Exception("fail")):
                with patch("rich.print") as mock_print:
                    result = send_notification("Test", "Message")
                    assert result is False
                    mock_print.assert_called_once()


class TestNotifyHelpers:
    @patch("src.utils.notifications.send_notification")
    def test_notify_download_complete(self, mock_send):
        mock_send.return_value = True
        result = notify_download_complete("Video Title", "/path/to/file.mp4")
        assert result is True
        mock_send.assert_called_once_with("Download Complete", "Video Title\nSaved to: /path/to/file.mp4")

    @patch("src.utils.notifications.send_notification")
    def test_notify_download_failed(self, mock_send):
        mock_send.return_value = True
        result = notify_download_failed("Video Title", "Error msg")
        assert result is True
        mock_send.assert_called_once_with("Download Failed", "Video Title\nError: Error msg", urgency="critical")

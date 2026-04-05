"""Tests for URL expander utilities."""
from unittest.mock import patch, MagicMock
from src.utils.url_expander import expand_url


class TestExpandUrl:
    @patch("requests.head")
    def test_expands_short_url(self, mock_head):
        mock_resp = MagicMock()
        mock_resp.url = "https://www.youtube.com/watch?v=abc123"
        mock_resp.status_code = 200
        mock_head.return_value = mock_resp
        result = expand_url("https://bit.ly/abc")
        assert result == "https://www.youtube.com/watch?v=abc123"

    @patch("requests.head")
    def test_returns_original_on_failure(self, mock_head):
        mock_head.side_effect = Exception("network error")
        result = expand_url("https://bit.ly/abc")
        assert result == "https://bit.ly/abc"

    @patch("requests.head")
    @patch("requests.get")
    def test_falls_back_to_get_on_head_failure(self, mock_get, mock_head):
        mock_head.return_value = MagicMock(status_code=403)
        mock_resp = MagicMock()
        mock_resp.url = "https://example.com/full"
        mock_get.return_value = mock_resp
        result = expand_url("https://t.co/abc")
        assert result == "https://example.com/full"

    @patch("requests.head")
    def test_returns_same_url_if_not_shortened(self, mock_head):
        mock_resp = MagicMock()
        mock_resp.url = "https://www.youtube.com/watch?v=abc"
        mock_resp.status_code = 200
        mock_head.return_value = mock_resp
        result = expand_url("https://www.youtube.com/watch?v=abc")
        assert result == "https://www.youtube.com/watch?v=abc"

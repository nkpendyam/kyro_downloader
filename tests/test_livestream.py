"""Tests for live stream service."""
from unittest.mock import patch
from src.services.livestream import download_livestream, record_livestream_ffmpeg

@patch("src.services.livestream.check_ffmpeg", return_value=False)
def test_no_ffmpeg(mock_ffmpeg):
    result = download_livestream("https://youtube.com/watch?v=test", "/tmp")
    assert result is None

@patch("src.services.livestream.check_ffmpeg", return_value=False)
def test_ffmpeg_no_ffmpeg(mock_ffmpeg):
    result = record_livestream_ffmpeg("https://example.com/live", "/tmp/output.mp4")
    assert result is None

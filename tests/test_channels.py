"""Tests for channel download service."""
from unittest.mock import patch, MagicMock
from src.services.channels import get_channel_info

@patch("yt_dlp.YoutubeDL")
def test_get_channel_info(mock_ydl):
    instance = MagicMock()
    instance.extract_info.return_value = {"title": "Test Channel", "uploader": "Test", "entries": []}
    mock_ydl.return_value.__enter__.return_value = instance
    info = get_channel_info("https://youtube.com/c/TestChannel")
    assert info is not None
    assert info["title"] == "Test Channel"

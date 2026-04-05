"""Tests for format conversion service."""
import os
from unittest.mock import patch, MagicMock
from src.services.converter import convert_file, batch_convert

@patch("src.services.converter.check_ffmpeg", return_value=False)
def test_no_ffmpeg(mock_ffmpeg, temp_dir):
    result = convert_file(os.path.join(temp_dir, "test.mp4"), "mp3")
    assert result is None

@patch("src.services.converter.check_ffmpeg", return_value=True)
@patch("src.services.converter.Path.exists", return_value=True)
@patch("subprocess.run")
def test_convert_success(mock_run, mock_exists, mock_ffmpeg, temp_dir):
    mock_run.return_value = MagicMock(returncode=0)
    result = convert_file(os.path.join(temp_dir, "test.mp4"), "mp3")
    assert result is not None
    assert result.endswith(".mp3")

def test_batch_convert():
    results = batch_convert([], "mp3")
    assert results == []

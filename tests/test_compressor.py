"""Tests for video compression service."""
import os
from unittest.mock import patch, MagicMock
from src.services.compressor import compress_video

@patch("src.services.compressor.check_ffmpeg", return_value=False)
def test_no_ffmpeg(mock_ffmpeg):
    result = compress_video("test.mp4")
    assert result is None

@patch("src.services.compressor.check_ffmpeg", return_value=True)
@patch("src.services.compressor.Path.exists", return_value=True)
@patch("subprocess.run")
def test_compress_success(mock_run, mock_exists, mock_ffmpeg, temp_dir):
    mock_run.return_value = MagicMock(returncode=0)
    input_path = os.path.join(temp_dir, "test.mp4")
    output_path = os.path.join(temp_dir, "test_compressed.mp4")
    with open(input_path, "wb") as f: f.write(b"fake")
    with open(output_path, "wb") as f: f.write(b"smaller")
    result = compress_video(input_path, output_path)
    assert result is not None
    assert "reduction_percent" in result

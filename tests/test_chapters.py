"""Tests for chapter extraction service."""
from unittest.mock import patch, MagicMock
from src.services.chapters import extract_chapters, split_by_chapters

@patch("src.services.chapters.check_ffmpeg", return_value=True)
@patch("subprocess.run")
def test_extract_chapters(mock_run, mock_ffmpeg):
    mock_run.return_value = MagicMock(returncode=0, stdout='{"chapters": [{"start_time": "0", "end_time": "60", "tags": {"title": "Intro"}}]}')
    chapters = extract_chapters("test.mp4")
    assert len(chapters) == 1
    assert chapters[0]["title"] == "Intro"

@patch("src.services.chapters.extract_chapters")
def test_split_by_chapters_no_chapters(mock_extract, temp_dir):
    mock_extract.return_value = []
    result = split_by_chapters("test.mp4", temp_dir)
    assert result == []

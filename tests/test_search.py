"""Tests for search service."""
from unittest.mock import patch, MagicMock
from src.services.search import search_platform, search_all_platforms

@patch("yt_dlp.YoutubeDL")
def test_search_youtube(mock_ydl):
    instance = MagicMock()
    instance.extract_info.return_value = {"entries": [{"title": "Test", "url": "https://youtube.com/watch?v=test", "duration": 300, "uploader": "Test", "view_count": 1000}]}
    mock_ydl.return_value.__enter__.return_value = instance
    results = search_platform("test", "youtube", max_results=1)
    assert len(results) == 1
    assert results[0]["title"] == "Test"

def test_search_all_platforms():
    with patch("src.services.search.search_platform") as mock_search:
        mock_search.return_value = [{"title": "Test", "url": "https://example.com"}]
        results = search_all_platforms("test", max_results=1)
        assert "youtube" in results
        assert "soundcloud" in results

"""Tests for download archive service."""
import os
from src.services.archive import DownloadArchive

def test_archive_init(temp_dir):
    archive_file = os.path.join(temp_dir, "archive.json")
    archive = DownloadArchive(archive_file)
    assert archive.contains("test123") is False

def test_archive_add(temp_dir):
    archive_file = os.path.join(temp_dir, "archive.json")
    archive = DownloadArchive(archive_file)
    archive.add("test123", "Test Video", "https://example.com", "/tmp/test.mp4", size=1000, duration=300, platform="youtube.com")
    assert archive.contains("test123") is True
    entry = archive.get("test123")
    assert entry["title"] == "Test Video"

def test_archive_remove(temp_dir):
    archive_file = os.path.join(temp_dir, "archive.json")
    archive = DownloadArchive(archive_file)
    archive.add("test123", "Test Video", "https://example.com", "/tmp/test.mp4")
    archive.remove("test123")
    assert archive.contains("test123") is False

def test_archive_stats(temp_dir):
    archive_file = os.path.join(temp_dir, "archive.json")
    archive = DownloadArchive(archive_file)
    archive.add("v1", "Video 1", "https://example.com/1", "/tmp/1.mp4", size=1000000, duration=300, platform="youtube.com")
    archive.add("v2", "Video 2", "https://example.com/2", "/tmp/2.mp4", size=2000000, duration=600, platform="vimeo.com")
    stats = archive.get_stats()
    assert stats["total_downloads"] == 2
    assert "youtube.com" in stats["platforms"]

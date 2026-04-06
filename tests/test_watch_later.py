"""Tests for watch_later service."""

from src.services.watch_later import (
    get_watch_later_url,
    extract_playlist_id,
    is_watch_later_url,
    build_watch_later_download_config,
)


class TestWatchLater:
    def test_get_watch_later_url(self):
        url = get_watch_later_url()
        assert "WL" in url

    def test_extract_playlist_id(self):
        pid = extract_playlist_id("https://youtube.com/playlist?list=abc123")
        assert pid == "abc123"

    def test_extract_playlist_id_no_list(self):
        pid = extract_playlist_id("https://youtube.com/watch?v=abc")
        assert pid is None

    def test_is_watch_later_url_true(self):
        assert is_watch_later_url("https://youtube.com/playlist?list=WL") is True

    def test_is_watch_later_url_false(self):
        assert is_watch_later_url("https://youtube.com/playlist?list=abc123") is False

    def test_build_watch_later_download_config(self):
        cfg = build_watch_later_download_config()
        assert cfg["prefer_format"] == "mp4"
        assert cfg["embed_thumbnail"] is True

    def test_build_watch_later_download_config_with_cookies(self):
        cfg = build_watch_later_download_config(cookies_file="cookies.txt")
        assert cfg["cookies_file"] == "cookies.txt"

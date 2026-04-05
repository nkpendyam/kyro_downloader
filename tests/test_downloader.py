"""Tests for core downloader module."""
from unittest.mock import MagicMock, patch

from src.core.downloader import (
    VideoInfo,
    download_single,
    list_video_formats,
    list_audio_formats,
    build_ydl_opts,
)


class TestVideoInfo:
    def test_video_info_basic(self):
        raw = {
            "title": "Test Video",
            "duration": 120,
            "thumbnail": "http://example.com/thumb.jpg",
            "uploader": "Test Uploader",
            "upload_date": "20240101",
            "view_count": 1000000,
            "formats": [],
        }
        info = VideoInfo(raw)
        assert info.title == "Test Video"
        assert info.duration == 120
        assert info.uploader == "Test Uploader"

    def test_duration_str_minutes(self):
        raw = {"title": "Test", "duration": 125}
        info = VideoInfo(raw)
        assert info.duration_str == "2:05"

    def test_duration_str_hours(self):
        raw = {"title": "Test", "duration": 3665}
        info = VideoInfo(raw)
        assert info.duration_str == "1:01:05"

    def test_duration_str_unknown(self):
        raw = {"title": "Test", "duration": 0}
        info = VideoInfo(raw)
        assert info.duration_str == "Unknown"

    def test_view_count_str_millions(self):
        raw = {"title": "Test", "view_count": 5000000}
        info = VideoInfo(raw)
        assert info.view_count_str == "5.0M"

    def test_view_count_str_thousands(self):
        raw = {"title": "Test", "view_count": 5000}
        info = VideoInfo(raw)
        assert info.view_count_str == "5.0K"

    def test_view_count_str_unknown(self):
        raw = {"title": "Test", "view_count": 0}
        info = VideoInfo(raw)
        assert info.view_count_str == "Unknown"

    def test_is_playlist(self):
        raw = {"title": "Test", "_type": "playlist", "entries": []}
        info = VideoInfo(raw)
        assert info.is_playlist is True

    def test_is_not_playlist(self):
        raw = {"title": "Test", "_type": "video"}
        info = VideoInfo(raw)
        assert info.is_playlist is False


class TestListVideoFormats:
    def test_filters_video_only_formats(self):
        formats = [
            {"vcodec": "h264", "acodec": "none", "height": 1080, "format_id": "1"},
            {"vcodec": "none", "acodec": "aac", "height": 0, "format_id": "2"},
            {"vcodec": "h264", "acodec": "aac", "height": 720, "format_id": "3"},
        ]
        result = list_video_formats(formats)
        assert len(result) == 1
        assert result[0]["format_id"] == "1"

    def test_sorted_by_height_descending(self):
        formats = [
            {"vcodec": "h264", "acodec": "none", "height": 720, "format_id": "1"},
            {"vcodec": "h264", "acodec": "none", "height": 1080, "format_id": "2"},
        ]
        result = list_video_formats(formats)
        assert result[0]["height"] == 1080
        assert result[1]["height"] == 720


class TestListAudioFormats:
    def test_filters_audio_only_formats(self):
        formats = [
            {"vcodec": "none", "acodec": "aac", "abr": 128, "format_id": "1"},
            {"vcodec": "h264", "acodec": "none", "abr": 0, "format_id": "2"},
        ]
        result = list_audio_formats(formats)
        assert len(result) == 1
        assert result[0]["format_id"] == "1"

    def test_sorted_by_abr_descending(self):
        formats = [
            {"vcodec": "none", "acodec": "aac", "abr": 128, "format_id": "1"},
            {"vcodec": "none", "acodec": "aac", "abr": 256, "format_id": "2"},
        ]
        result = list_audio_formats(formats)
        assert result[0]["abr"] == 256


class TestBuildYdlOpts:
    def test_basic_options(self, tmp_path):
        opts = build_ydl_opts(str(tmp_path))
        assert "outtmpl" in opts
        assert "postprocessors" in opts
        assert opts["retries"] == 10

    def test_audio_only_options(self, tmp_path):
        opts = build_ydl_opts(str(tmp_path), only_audio=True, audio_format="mp3", audio_quality="320")
        assert opts["format"] == "bestaudio/best"
        assert "keepvideo" not in opts

    def test_specific_format(self, tmp_path):
        opts = build_ydl_opts(str(tmp_path), format_id="137")
        assert opts["format"] == "137+bestaudio/best"

    def test_rate_limit(self, tmp_path):
        opts = build_ydl_opts(str(tmp_path), rate_limit="1M")
        assert opts["ratelimit"] == "1M"

    def test_proxy(self, tmp_path):
        opts = build_ydl_opts(str(tmp_path), proxy="http://proxy:8080")
        assert opts["proxy"] == "http://proxy:8080"

    def test_cookies_file(self, tmp_path):
        opts = build_ydl_opts(str(tmp_path), cookies_file="cookies.txt")
        assert opts["cookiefile"] == "cookies.txt"

    def test_playlist_options(self, tmp_path):
        playlist_cfg = {"sleep_interval": 5, "max_downloads": 10, "playlist_reverse": True}
        opts = build_ydl_opts(str(tmp_path), playlist=True, playlist_config=playlist_cfg)
        assert opts["sleep_interval"] == 5
        assert opts["playlistend"] == 10
        assert opts["playlist_reverse"] is True


class TestDownloadSingle:
    def test_explicit_progress_hook_is_forwarded(self, tmp_path):
        def hook(_data):
            return None

        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value.download.return_value = 0

        with patch("src.core.downloader.build_ydl_opts", return_value={} ) as mock_build:
            with patch("src.core.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
                download_single(
                    url="https://youtube.com/watch?v=abc123",
                    output_path=str(tmp_path),
                    progress_hook=hook,
                )

        assert mock_build.call_args.kwargs["progress_hook"] is hook

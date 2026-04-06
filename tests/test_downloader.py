"""Tests for core downloader module."""

from unittest.mock import MagicMock, patch

from src.core.downloader import (
    VideoInfo,
    build_smart_audio_options,
    download_playlist,
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

    def test_duration_str_float_seconds(self):
        raw = {"title": "Test", "duration": 233.62}
        info = VideoInfo(raw)
        assert info.duration_str == "3:53"

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

    def test_audio_only_opus_disables_thumbnail_embed_postprocessor(self, tmp_path):
        opts = build_ydl_opts(str(tmp_path), only_audio=True, audio_format="opus", audio_quality="96")
        assert opts["writethumbnail"] is False
        assert all(pp["key"] != "EmbedThumbnail" for pp in opts["postprocessors"])

    def test_audio_only_selector_override(self, tmp_path):
        opts = build_ydl_opts(
            str(tmp_path),
            only_audio=True,
            audio_format="opus",
            audio_quality="160",
            audio_selector="bestaudio[acodec*=opus]/bestaudio/best",
        )
        assert opts["format"] == "bestaudio[acodec*=opus]/bestaudio/best"

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

    def test_cookies_from_browser(self, tmp_path):
        opts = build_ydl_opts(str(tmp_path), cookies_from_browser="firefox")
        assert opts["cookiesfrombrowser"] == ("firefox",)

    def test_playlist_options(self, tmp_path):
        playlist_cfg = {"sleep_interval": 5, "max_downloads": 10, "playlist_reverse": True}
        opts = build_ydl_opts(str(tmp_path), playlist=True, playlist_config=playlist_cfg)
        assert opts["sleep_interval"] == 5
        assert opts["playlistend"] == 10
        assert opts["playlist_reverse"] is True

    def test_subtitle_options_enabled(self, tmp_path):
        subtitles_cfg = {
            "enabled": True,
            "languages": ["en", "es"],
            "auto_generated": True,
            "embed": False,
            "format": "srt",
        }
        opts = build_ydl_opts(str(tmp_path), subtitles=subtitles_cfg)
        assert opts["writesubtitles"] is True
        assert opts["writeautomaticsub"] is True
        assert opts["subtitleslangs"] == ["en", "es"]
        assert opts["subtitlesformat"] == "srt"

    def test_output_template_override(self, tmp_path):
        opts = build_ydl_opts(
            str(tmp_path),
            output_template="%(uploader)s/%(title)s [%(id)s].%(ext)s",
        )
        assert opts["outtmpl"].endswith("%(uploader)s/%(title)s [%(id)s].%(ext)s")


class TestDownloadSingle:
    def test_download_single_returns_written_file_paths(self, tmp_path):
        target_file = tmp_path / "video.mp4"
        target_file.write_text("data", encoding="utf-8")

        result_payload = {
            "filepath": str(target_file),
        }

        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value.extract_info.return_value = result_payload

        with patch("src.core.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            result = download_playlist(url="https://youtube.com/playlist?list=PL123", output_path=str(tmp_path))

        assert str(target_file) in result.completed_files
        assert str(tmp_path) not in result.completed_files

    def test_explicit_progress_hook_is_forwarded(self, tmp_path):
        def hook(_data):
            return None

        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value.extract_info.return_value = {}

        with patch("src.core.downloader.build_ydl_opts", return_value={}) as mock_build:
            with patch("src.core.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
                download_single(
                    url="https://youtube.com/watch?v=abc123",
                    output_path=str(tmp_path),
                    progress_hook=hook,
                )

        assert mock_build.call_args.kwargs["progress_hook"] is hook

    def test_download_single_no_unconditional_sleep(self, tmp_path):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value.extract_info.return_value = {}
        captured_opts = {}

        def _ydl_factory(opts):
            captured_opts.update(opts)
            return mock_ydl

        with patch("src.core.downloader.build_ydl_opts", return_value={}):
            with patch("src.core.downloader.yt_dlp.YoutubeDL", side_effect=_ydl_factory):
                download_single(
                    url="https://youtube.com/watch?v=abc123",
                    output_path=str(tmp_path),
                )

        assert "sleep_interval_subtitles" not in captured_opts


class TestSmartAudioOptions:
    def test_build_smart_audio_options_includes_source_and_presets(self):
        analysis = {
            "audio_streams": [
                {
                    "format_id": "251",
                    "codec": "opus",
                    "selector_codec": "opus",
                    "abr": 160,
                    "ext": "webm",
                }
            ]
        }
        options = build_smart_audio_options(analysis)
        labels = [o["label"] for o in options]

        assert labels[0] == "Smart Best Available (Auto)"
        assert any("Source OPUS 160 kbps" in label for label in labels)
        assert any(label.startswith("Preset 320 kbps") for label in labels)


class TestDownloadPlaylist:
    def test_download_playlist_returns_written_file_paths(self, tmp_path):
        target_file = tmp_path / "playlist_video.mp4"
        target_file.write_text("playlist-data", encoding="utf-8")

        result_payload = {
            "entries": [
                {
                    "filepath": str(target_file),
                }
            ]
        }

        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value.extract_info.return_value = result_payload

        with patch("src.core.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            result = download_playlist(url="https://youtube.com/playlist?list=PL123", output_path=str(tmp_path))

        assert str(target_file) in result.completed_files
        assert str(tmp_path) not in result.completed_files

    def test_download_playlist_does_not_false_positive_failed_urls_for_requested_downloads(self, tmp_path):
        target_file = tmp_path / "written.mp4"
        target_file.write_text("video", encoding="utf-8")

        result_payload = {
            "entries": [
                {
                    "url": "https://example.com/video",
                    "title": "Entry 1",
                    "requested_downloads": [{"filepath": str(target_file)}],
                }
            ]
        }

        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value.extract_info.return_value = result_payload

        with patch("src.core.downloader.yt_dlp.YoutubeDL", return_value=mock_ydl):
            result = download_playlist(url="https://youtube.com/playlist?list=PL123", output_path=str(tmp_path))

        assert result.completed_count == 1
        assert result.failed_urls == []

    def test_download_playlist_reports_progress_with_progress_tracker(self, tmp_path):
        events = []

        class FakeTracker:
            def add_task(self, task_id, filename="", total_bytes=0):
                events.append(("add", task_id, filename, total_bytes))

            def update(self, task_id, **kwargs):
                events.append(("update", task_id, kwargs))

            def complete(self, task_id, error=None):
                events.append(("complete", task_id, error))

        class FakeYdl:
            def __init__(self, opts):
                self.opts = opts

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

            def extract_info(self, _url, download=True):
                hook = self.opts["progress_hooks"][0]
                hook(
                    {
                        "status": "downloading",
                        "downloaded_bytes": 50,
                        "total_bytes": 100,
                        "_percent_str": "50.0%",
                        "info_dict": {
                            "playlist_index": 1,
                            "n_entries": 2,
                            "title": "Episode 1",
                        },
                    }
                )
                hook(
                    {
                        "status": "finished",
                        "info_dict": {
                            "playlist_index": 1,
                            "n_entries": 2,
                            "title": "Episode 1",
                        },
                    }
                )
                return {
                    "entries": [
                        {
                            "filepath": str(tmp_path / "episode-1.mp4"),
                            "title": "Episode 1",
                        }
                    ]
                }

        with patch("src.core.downloader.yt_dlp.YoutubeDL", side_effect=lambda opts: FakeYdl(opts)):
            download_playlist(
                url="https://youtube.com/playlist?list=PL123",
                output_path=str(tmp_path),
                progress_tracker=FakeTracker(),
            )

        assert any(event[0] == "add" for event in events)
        assert any(event[0] == "update" for event in events)
        assert any(event[0] == "complete" for event in events)

"""Tests for plugin system."""
from unittest.mock import MagicMock

from src.cli.__main__ import create_parser
from src.plugins.api import PluginBase
from src.plugins.builtin.auto_thumbnail import AutoThumbnailPlugin
from src.plugins.builtin.subtitle_auto import AutoSubtitlePlugin
from src.plugins.loader import PluginLoader


class TestPluginBase:
    def test_default_values(self):
        plugin = PluginBase()
        assert plugin.name == ""
        assert plugin.version == ""
        assert plugin.description == ""
        assert plugin.enabled is True

    def test_hooks_do_nothing(self):
        plugin = PluginBase()
        plugin.on_download_start("http://test.com", {})
        plugin.on_download_progress("http://test.com", 0.5, 1000)
        plugin.on_download_complete("http://test.com", "/path")
        plugin.on_download_error("http://test.com", "error")


class TestPluginLoader:
    def test_init_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        loader = PluginLoader()
        assert len(loader.list_plugins()) >= 0

    def test_enable_disable_plugin(self):
        loader = PluginLoader()
        loader._plugins["test"] = PluginBase()
        loader._plugins["test"].name = "test"
        assert loader.enable_plugin("test") is True
        assert loader._plugins["test"].enabled is True
        assert loader.disable_plugin("test") is True
        assert loader._plugins["test"].enabled is False

    def test_enable_nonexistent_plugin(self):
        loader = PluginLoader()
        assert loader.enable_plugin("nonexistent") is False

    def test_get_plugin(self):
        loader = PluginLoader()
        plugin = PluginBase()
        plugin.name = "test"
        loader._plugins["test"] = plugin
        assert loader.get_plugin("test") is plugin
        assert loader.get_plugin("nonexistent") is None

    def test_fire_hook_enabled(self):
        loader = PluginLoader()
        mock_plugin = MagicMock()
        mock_plugin.enabled = True
        mock_plugin.on_download_start = MagicMock()
        loader._plugins["test"] = mock_plugin
        loader.fire_hook("on_download_start", url="http://test.com")
        mock_plugin.on_download_start.assert_called_once_with(url="http://test.com")

    def test_fire_hook_disabled(self):
        loader = PluginLoader()
        mock_plugin = MagicMock()
        mock_plugin.enabled = False
        loader._plugins["test"] = mock_plugin
        loader.fire_hook("on_download_start", url="http://test.com")
        mock_plugin.on_download_start.assert_not_called()

    def test_fire_hook_error_isolation(self):
        loader = PluginLoader()
        mock_plugin = MagicMock()
        mock_plugin.enabled = True
        mock_plugin.on_download_start = MagicMock(side_effect=Exception("fail"))
        loader._plugins["test"] = mock_plugin
        loader.fire_hook("on_download_start", url="http://test.com")
        mock_plugin.on_download_start.assert_called_once()


class TestSubtitlePlugin:
    def test_auto_subtitle_plugin_uses_video_info(self, monkeypatch, tmp_path):
        plugin = AutoSubtitlePlugin()

        class _Info:
            raw = {
                "title": "test",
                "webpage_url": "https://example.com/watch?v=1",
            }

        called = {}

        def fake_get_video_info(url):
            called["url"] = url
            return _Info()

        def fake_download_subs(info, output_dir, languages=None, subtitle_format="srt"):
            called["info"] = info
            called["output_dir"] = output_dir
            called["languages"] = languages
            return []

        monkeypatch.setattr("src.plugins.builtin.subtitle_auto.get_video_info", fake_get_video_info)
        monkeypatch.setattr("src.services.subtitles.download_subtitles_separately", fake_download_subs)

        result = plugin.on_download_complete("https://example.com/watch?v=1", str(tmp_path / "video.mp4"))
        assert result == str(tmp_path / "video.mp4")
        assert called["url"] == "https://example.com/watch?v=1"
        assert called["languages"] == ["en"]


class TestAutoThumbnailPlugin:
    def test_auto_thumbnail_plugin_downloads_thumbnail(self, monkeypatch, tmp_path):
        plugin = AutoThumbnailPlugin()

        class _Info:
            thumbnail = "https://example.com/thumb.jpg"

        called = {}

        def fake_get_video_info(url):
            called["url"] = url
            return _Info()

        def fake_download_thumbnail(url, output_path, filename="thumbnail"):
            called["thumb_url"] = url
            called["output_path"] = output_path
            called["filename"] = filename
            return tmp_path / f"{filename}.jpg"

        monkeypatch.setattr("src.plugins.builtin.auto_thumbnail.get_video_info", fake_get_video_info)
        monkeypatch.setattr("src.services.thumbnails.download_thumbnail", fake_download_thumbnail)

        output_file = tmp_path / "video.mp4"
        output_file.write_text("dummy", encoding="utf-8")
        result = plugin.on_download_complete("https://example.com/watch?v=1", str(output_file))

        assert result == str(output_file)
        assert called["url"] == "https://example.com/watch?v=1"
        assert called["thumb_url"] == "https://example.com/thumb.jpg"
        assert called["filename"] == "video"


class TestCLISubtitleFlags:
    def test_download_subtitle_flags(self):
        parser = create_parser()
        args = parser.parse_args([
            "download",
            "https://example.com/video",
            "--subs",
            "--subs-lang",
            "en,es",
            "--embed-subs",
            "--subs-format",
            "vtt",
        ])
        assert args.subs is True
        assert args.subs_lang == "en,es"
        assert args.embed_subs is True
        assert args.subs_format == "vtt"

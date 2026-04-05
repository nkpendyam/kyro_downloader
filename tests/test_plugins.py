"""Tests for plugin system."""
from unittest.mock import MagicMock
from src.plugins.api import PluginBase
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

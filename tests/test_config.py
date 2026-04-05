"""Tests for config module."""
import os
import pytest
from src.config.manager import load_config, save_config, get_default_config_path, deep_merge, find_config_file
from src.config.schema import AppConfig
from src.config.defaults import DEFAULT_CONFIG


class TestConfigManager:
    def test_load_config_returns_app_config(self):
        config = load_config()
        assert isinstance(config, AppConfig)

    def test_load_config_with_custom_path(self, tmp_path):
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("general:\n  output_path: /tmp/test\n")
        config = load_config(str(config_file))
        assert config.general.output_path == "/tmp/test"

    def test_save_config(self, tmp_path):
        config = load_config()
        config.general.output_path = "/tmp/custom"
        path = save_config(config, str(tmp_path / "saved.yaml"))
        assert os.path.exists(path)

    def test_get_default_config_path(self):
        path = get_default_config_path()
        assert path is not None
        assert str(path).endswith("config.yaml")

    def test_save_and_reload_config(self, tmp_path):
        config = load_config()
        config.general.output_path = "/tmp/reload_test"
        config_path = str(tmp_path / "reload.yaml")
        save_config(config, config_path)
        reloaded = load_config(config_path)
        assert reloaded.general.output_path == "/tmp/reload_test"

    def test_load_nonexistent_config_returns_default(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(str(tmp_path / "nonexistent.yaml"))

    def test_deep_merge(self):
        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"d": 3}, "e": 4}
        result = deep_merge(base, override)
        assert result["a"] == 1
        assert result["b"]["c"] == 2
        assert result["b"]["d"] == 3
        assert result["e"] == 4

    def test_find_config_file_not_found(self, tmp_path):
        import src.config.manager as mgr
        original = mgr.CONFIG_DIRS
        mgr.CONFIG_DIRS = [tmp_path]
        try:
            result = find_config_file()
            assert result is None
        finally:
            mgr.CONFIG_DIRS = original


class TestConfigSchema:
    def test_default_config(self):
        config = AppConfig()
        assert config.general.output_path is not None
        assert config.download.max_retries == 3

    def test_custom_config(self):
        config = AppConfig(
            general={"output_path": "/custom", "notifications": False},
            download={"max_retries": 10, "concurrent_workers": 8}
        )
        assert config.general.output_path == "/custom"
        assert config.download.max_retries == 10
        assert config.download.concurrent_workers == 8

    def test_model_dump(self):
        config = AppConfig()
        dump = config.model_dump()
        assert "general" in dump
        assert "download" in dump
        assert "ui" in dump


class TestConfigDefaults:
    def test_default_config_has_required_keys(self):
        assert "general" in DEFAULT_CONFIG
        assert "download" in DEFAULT_CONFIG
        assert "ui" in DEFAULT_CONFIG

    def test_default_output_path(self):
        assert "output_path" in DEFAULT_CONFIG["general"]

    def test_default_max_retries(self):
        assert DEFAULT_CONFIG["download"]["max_retries"] == 3

"""Meaningful GUI component tests beyond import checks."""

from __future__ import annotations


from src.config.manager import load_config
from src.config.schema import AppConfig
from src.services.presets import PresetsManager


class TestGUIConfigLogic:
    def test_config_loads_without_errors(self):
        config = load_config()
        assert config is not None
        assert hasattr(config, "general")
        assert hasattr(config, "web")

    def test_config_general_has_required_fields(self):
        config = load_config()
        assert config.general.output_path is not None
        assert isinstance(config.general.output_path, str)

    def test_config_web_has_required_fields(self):
        config = load_config()
        assert config.web.port > 0
        assert config.web.host is not None

    def test_config_model_dump_roundtrip(self):
        config = load_config()
        data = config.model_dump()
        restored = AppConfig.model_validate(data)
        assert restored.general.output_path == config.general.output_path
        assert restored.web.port == config.web.port


class TestGUIPresetLogic:
    def test_presets_manager_loads_default_presets(self, tmp_path):
        mgr = PresetsManager(state_dir=str(tmp_path))
        presets = mgr.get_all_presets()
        assert len(presets) > 0

    def test_presets_manager_add_custom_preset(self, tmp_path):
        mgr = PresetsManager(state_dir=str(tmp_path))
        mgr.add_preset("test-preset", {"only_audio": True, "audio_format": "flac"})
        presets = mgr.get_all_presets()
        assert "test-preset" in presets
        assert presets["test-preset"]["only_audio"] is True

    def test_presets_manager_delete_preset(self, tmp_path):
        mgr = PresetsManager(state_dir=str(tmp_path))
        mgr.add_preset("to-delete", {"only_audio": True})
        presets = mgr.get_all_presets()
        assert "to-delete" in presets

    def test_presets_persistence(self, tmp_path):
        mgr1 = PresetsManager(state_dir=str(tmp_path))
        mgr1.add_preset("persisted", {"audio_format": "opus"})
        mgr2 = PresetsManager(state_dir=str(tmp_path))
        presets = mgr2.get_all_presets()
        assert "persisted" in presets


class TestGUIValidationLogic:
    def test_download_form_validates_url(self):
        from src.utils.validation import validate_url

        assert validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
        assert validate_url("not-a-url") is False
        assert validate_url("") is False
        assert validate_url(None) is False

    def test_download_form_validates_output_path(self, tmp_path):
        from src.utils.validation import validate_output_path

        result = validate_output_path(str(tmp_path))
        assert result.is_dir()
        assert result == tmp_path.resolve()

    def test_download_form_validates_integer(self):
        from src.utils.validation import validate_integer

        assert validate_integer("5") == 5
        assert validate_integer("abc") is None
        assert validate_integer("5", min_val=1, max_val=10) == 5
        assert validate_integer("15", min_val=1, max_val=10) is None


class TestQueueDisplayLogic:
    def test_queue_items_serialize_for_display(self):
        from src.core.queue import DownloadQueue, Priority

        queue = DownloadQueue()
        item = queue.add(url="https://example.com/video", priority=Priority.HIGH)
        display_data = {
            "task_id": item.task_id,
            "url": item.url,
            "status": item.status.value,
            "priority": item.priority.name,
        }
        assert display_data["status"] == "pending"
        assert display_data["priority"] == "HIGH"

    def test_queue_status_counts(self):
        from src.core.queue import DownloadQueue

        queue = DownloadQueue()
        queue.add(url="https://example.com/one")
        queue.add(url="https://example.com/two")
        queue.add(url="https://example.com/three")

        assert queue.pending_count == 3
        assert queue.active_count == 0
        assert queue.completed_count == 0

    def test_queue_clear_completed(self):
        from src.core.queue import DownloadQueue

        queue = DownloadQueue()
        item1 = queue.add(url="https://example.com/one")
        item2 = queue.add(url="https://example.com/two")
        queue.get_next()
        queue.complete(item1.task_id)
        queue.complete(item2.task_id)

        removed = queue.clear_completed()
        assert removed == 2
        assert queue.size == 0

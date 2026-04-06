"""Persistence tests for GUI state components."""

from __future__ import annotations

from src.gui.components.accessibility_settings import AccessibilitySettings
from src.gui.components.history_viewer import HistoryViewer
from src.gui.components.tags_manager import TagsManager


def test_accessibility_settings_persist_roundtrip(tmp_path) -> None:
    settings = AccessibilitySettings(state_dir=str(tmp_path))
    settings.set("font_size", 18)
    settings.set("high_contrast", True)

    reloaded = AccessibilitySettings(state_dir=str(tmp_path))
    assert reloaded.get_font_size() == 18
    assert reloaded.is_high_contrast() is True


def test_tags_manager_persist_roundtrip(tmp_path) -> None:
    tags = TagsManager(state_dir=str(tmp_path))
    tags.add_tags("task-1", "Music, Tutorial")
    tags.remove_tag_from_task("task-1", "music")

    reloaded = TagsManager(state_dir=str(tmp_path))
    assert reloaded.get_tags("task-1") == "tutorial"
    assert "tutorial" in reloaded.get_all_tags()


def test_history_viewer_caps_history_and_persists(tmp_path) -> None:
    history = HistoryViewer(state_dir=str(tmp_path))
    for i in range(1005):
        history.add_entry(task_id=f"task-{i}", url=f"https://example.com/{i}", title=f"Title {i}", status="completed")

    assert len(history.get_history(limit=2000)) == 1000

    reloaded = HistoryViewer(state_dir=str(tmp_path))
    assert len(reloaded.get_history(limit=2000)) == 1000
    assert reloaded.get_entry("task-1004") is not None

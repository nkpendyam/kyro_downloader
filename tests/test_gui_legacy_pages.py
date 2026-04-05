"""Tests for legacy Flet GUI page de-scope behavior."""

import pytest

pytest.importorskip("flet")

from src.gui.pages.download_page import DownloadPage
from src.gui.pages.search_page import SearchPage


class _StubPresetsManager:
    def get_all_presets(self):
        return {}


class _StubTagsManager:
    pass


class TestLegacyFletPages:
    def test_download_page_legacy_actions_raise(self):
        page = DownloadPage(config={}, manager=None, presets_manager=_StubPresetsManager(), tags_manager=_StubTagsManager())

        for method_name in ["start_download", "batch_download", "_on_preset_selected", "_on_tags_submitted"]:
            method = getattr(page, method_name)
            try:
                method(None)
            except NotImplementedError as exc:
                assert "Legacy Flet DownloadPage action" in str(exc)
            else:
                raise AssertionError(f"{method_name} should raise NotImplementedError")

    def test_search_page_legacy_actions_raise(self):
        page = SearchPage()

        for method_name, arg in [("do_search", None), ("_download_search_result", "https://example.com")]:
            method = getattr(page, method_name)
            try:
                method(arg)
            except NotImplementedError as exc:
                assert "Legacy Flet SearchPage action" in str(exc)
            else:
                raise AssertionError(f"{method_name} should raise NotImplementedError")

"""Tests for smart_mode service."""

from types import SimpleNamespace
from src.services.smart_mode import get_smart_quality


class TestSmartMode:
    def test_get_smart_quality_no_formats(self):
        info = SimpleNamespace(formats=[])
        result = get_smart_quality(info)
        assert result["quality"] == "best"

    def test_get_smart_quality_best(self):
        fmt = {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "filesize": 50_000_000}
        info = SimpleNamespace(formats=[fmt])
        result = get_smart_quality(info)
        assert result["format_id"] == "137"

    def test_get_smart_quality_with_max_size(self):
        fmts = [
            {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "filesize": 500_000_000},
            {"format_id": "136", "vcodec": "avc1", "acodec": "none", "height": 720, "filesize": 200_000_000},
        ]
        info = SimpleNamespace(formats=fmts)
        result = get_smart_quality(info, max_size_mb=300)
        assert result["format_id"] == "136"

    def test_get_smart_quality_fallback(self):
        fmts = [
            {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 4320, "filesize": 5_000_000_000},
        ]
        info = SimpleNamespace(formats=fmts)
        result = get_smart_quality(info, max_size_mb=100)
        assert result["format_id"] == "137"

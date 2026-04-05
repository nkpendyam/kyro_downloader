"""Tests for format sorter service."""
from src.services.format_sorter import sort_formats, filter_formats, get_best_format

def test_sort_by_res():
    formats = [{"height": 720}, {"height": 1080}, {"height": 480}]
    sorted_f = sort_formats(formats, "res")
    assert sorted_f[0]["height"] == 1080

def test_filter_by_height():
    formats = [{"height": 1080}, {"height": 720}, {"height": 480}]
    filtered = filter_formats(formats, ["height<=720"])
    assert len(filtered) == 2

def test_get_best_format():
    formats = [{"vcodec": "avc1", "acodec": "none", "height": 1080}, {"vcodec": "none", "acodec": "mp4a", "abr": 128}]
    result = get_best_format(formats, "best")
    assert result["video"] is not None
    assert result["audio"] is not None

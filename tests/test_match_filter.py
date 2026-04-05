"""Tests for match filter service."""
from src.services.match_filter import apply_match_filters

def test_match_filter_equality():
    info = {"title": "Test Video", "view_count": 1000}
    assert apply_match_filters(info, ["title==Test Video"]) is True
    assert apply_match_filters(info, ["title==Other"]) is False

def test_match_filter_comparison():
    info = {"view_count": 1000}
    assert apply_match_filters(info, ["view_count>=500"]) is True
    assert apply_match_filters(info, ["view_count>2000"]) is False

def test_match_filter_regex():
    info = {"description": "This is a test video about cats & dogs"}
    assert apply_match_filters(info, ["description~=cats"]) is True
    assert apply_match_filters(info, ["description~=birds"]) is False

def test_match_filter_negation():
    info = {"title": "Test", "is_live": True}
    assert apply_match_filters(info, ["!is_live"]) is False

"""Tests for output template service."""
from src.services.output_template import apply_template

def test_default_template():
    info = {"title": "Test", "id": "abc123", "ext": "mp4"}
    result = apply_template(None, info)
    assert "Test" in result
    assert "abc123" in result
    assert "mp4" in result

def test_playlist_template():
    info = {"title": "Video", "id": "abc", "ext": "mp4", "playlist_title": "My Playlist", "playlist_index": 5}
    result = apply_template("playlist", info)
    assert "My Playlist" in result
    assert "5" in result

def test_custom_template():
    info = {"title": "Video", "id": "abc", "ext": "mp4", "uploader": "Test"}
    result = apply_template("%(uploader)s_%(title)s.%(ext)s", info)
    assert "Test_Video.mp4" == result

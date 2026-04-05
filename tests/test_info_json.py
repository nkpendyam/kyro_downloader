"""Tests for info JSON service."""
import os
import json
from src.services.info_json import write_info_json, write_description

def test_write_info_json(temp_dir):
    info = {"title": "Test", "id": "abc123", "description": "Test description"}
    result = write_info_json(info, temp_dir)
    assert result is not None
    assert os.path.exists(result)
    with open(result) as f:
        data = json.load(f)
    assert data["title"] == "Test"

def test_write_description(temp_dir):
    info = {"title": "Test", "id": "abc123", "description": "Test description"}
    result = write_description(info, temp_dir)
    assert result is not None
    assert os.path.exists(result)
    with open(result) as f:
        assert f.read() == "Test description"

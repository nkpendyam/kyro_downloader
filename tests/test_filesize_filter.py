"""Tests for filesize filter service."""
from src.services.filesize_filter import parse_size, check_filesize

def test_parse_size():
    assert parse_size("50k") == 50 * 1024
    assert parse_size("1M") == 1024 * 1024
    assert parse_size("1G") == 1024 ** 3

def test_check_filesize():
    assert check_filesize(500000, min_size=100000) is True
    assert check_filesize(500000, max_size=100000) is False
    assert check_filesize(500000, min_size=100000, max_size=1000000) is True

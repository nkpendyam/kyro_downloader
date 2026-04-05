"""Tests for external downloader service."""
from unittest.mock import patch
from src.services.external_dl import check_aria2c, get_external_downloader

@patch("shutil.which", return_value="/usr/bin/aria2c")
def test_check_aria2c_found(mock_which):
    assert check_aria2c() is True

@patch("shutil.which", return_value=None)
def test_check_aria2c_not_found(mock_which):
    assert check_aria2c() is False

@patch("src.services.external_dl.check_aria2c", return_value=True)
def test_get_external_downloader(mock_check):
    assert get_external_downloader() == "aria2c"

"""Tests for date filter service."""
from src.services.date_filter import parse_date, is_date_in_range

def test_parse_date_today():
    from datetime import datetime
    result = parse_date("today")
    assert result == datetime.now().strftime("%Y%m%d")

def test_is_date_in_range():
    assert is_date_in_range("20260101", dateafter="20250101", datebefore="20270101") is True
    assert is_date_in_range("20260101", dateafter="20270101") is False

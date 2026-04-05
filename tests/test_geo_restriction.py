"""Tests for geo restriction service."""
from src.services.geo_restriction import build_geo_opts, COUNTRY_CODES

def test_build_geo_opts():
    opts = build_geo_opts("http://proxy:8080", "US")
    assert opts["proxy"] == "http://proxy:8080"
    assert opts["geo_bypass_country"] == "US"

def test_country_codes():
    assert "US" in COUNTRY_CODES
    assert COUNTRY_CODES["US"] == "United States"

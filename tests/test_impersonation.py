"""Tests for impersonation service."""
from src.services.impersonation import get_impersonation_headers, build_impersonation_opts

def test_chrome_headers():
    headers = get_impersonation_headers("chrome")
    assert "User-Agent" in headers
    assert "Chrome" in headers["User-Agent"]

def test_build_impersonation_opts():
    opts = build_impersonation_opts("firefox")
    assert "user_agent" in opts
    assert "Firefox" in opts["user_agent"]

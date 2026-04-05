"""Tests for netrc auth service."""
from src.services.netrc_auth import build_auth_opts

def test_build_auth_opts():
    opts = build_auth_opts(username="user", password="pass")
    assert opts["username"] == "user"
    assert opts["password"] == "pass"

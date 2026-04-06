"""Tests for proxy_manager service."""

from unittest.mock import patch, MagicMock
from src.services.proxy_manager import ProxyManager


class TestProxyManager:
    def test_add_proxy(self):
        mgr = ProxyManager()
        mgr.add_proxy("http://proxy1.example.com:8080")
        assert mgr.get_total_count() == 1

    def test_get_next_proxy_no_working_returns_none(self):
        mgr = ProxyManager()
        mgr.add_proxy("http://proxy1.example.com:8080")
        with patch("src.services.proxy_manager.requests.get", side_effect=Exception("no network")):
            proxy = mgr.get_next_proxy()
        assert proxy is None

    def test_get_next_proxy_with_working(self):
        mgr = ProxyManager()
        mgr.add_proxy("http://proxy1.example.com:8080")
        mgr.add_proxy("http://proxy2.example.com:8080")
        with patch("src.services.proxy_manager.requests.get", return_value=MagicMock(status_code=200)):
            p1 = mgr.get_next_proxy()
            p2 = mgr.get_next_proxy()
        assert p1 is not None
        assert p2 is not None
        assert p1 != p2

    def test_get_total_count(self):
        mgr = ProxyManager()
        mgr.add_proxy("http://proxy1.example.com:8080")
        mgr.add_proxy("http://proxy2.example.com:8080")
        assert mgr.get_total_count() == 2

    def test_get_working_count(self):
        mgr = ProxyManager()
        mgr.add_proxy("http://proxy1.example.com:8080")
        assert mgr.get_working_count() == 0

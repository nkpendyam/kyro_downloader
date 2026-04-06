"""Tests for subscriptions service."""

from src.services.subscriptions import SubscriptionManager


class TestSubscriptionManager:
    def test_subscribe(self, tmp_path, monkeypatch):
        test_file = tmp_path / "subs.json"
        monkeypatch.setattr("src.services.subscriptions.SUBSCRIPTIONS_FILE", test_file)
        mgr = SubscriptionManager()
        mgr.subscribe("https://youtube.com/channel/abc123")
        assert len(mgr.list_subscriptions()) == 1

    def test_unsubscribe(self, tmp_path, monkeypatch):
        test_file = tmp_path / "subs.json"
        monkeypatch.setattr("src.services.subscriptions.SUBSCRIPTIONS_FILE", test_file)
        mgr = SubscriptionManager()
        mgr.subscribe("https://youtube.com/channel/abc123")
        mgr.unsubscribe("https://youtube.com/channel/abc123")
        assert len(mgr.list_subscriptions()) == 0

    def test_list_subscriptions(self, tmp_path, monkeypatch):
        test_file = tmp_path / "subs.json"
        monkeypatch.setattr("src.services.subscriptions.SUBSCRIPTIONS_FILE", test_file)
        mgr = SubscriptionManager()
        mgr.subscribe("https://youtube.com/channel/abc")
        mgr.subscribe("https://youtube.com/channel/def")
        assert len(mgr.list_subscriptions()) == 2

    def test_subscribe_with_auto_download(self, tmp_path, monkeypatch):
        test_file = tmp_path / "subs.json"
        monkeypatch.setattr("src.services.subscriptions.SUBSCRIPTIONS_FILE", test_file)
        mgr = SubscriptionManager()
        sub = mgr.subscribe("https://youtube.com/channel/abc", auto_download=True)
        assert sub["auto_download"] is True

    def test_update_last_check(self, tmp_path, monkeypatch):
        test_file = tmp_path / "subs.json"
        monkeypatch.setattr("src.services.subscriptions.SUBSCRIPTIONS_FILE", test_file)
        mgr = SubscriptionManager()
        mgr.subscribe("https://youtube.com/channel/abc")
        mgr.update_last_check("https://youtube.com/channel/abc")
        subs = mgr.list_subscriptions()
        assert subs[0]["last_check"] is not None

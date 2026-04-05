"""Tests for smart_mode service."""
from unittest.mock import MagicMock
from src.services.smart_mode import get_smart_quality


class TestSmartMode:
    def test_no_formats(self):
        info = MagicMock()
        info.formats = []
        result = get_smart_quality(info)
        assert result["quality"] == "best"
        assert result["format_id"] is None

    def test_best_quality_no_constraints(self):
        info = MagicMock()
        info.formats = [
            {"vcodec": "h264", "acodec": "none", "height": 1080, "format_id": "1", "filesize": 500_000_000},
            {"vcodec": "h264", "acodec": "none", "height": 720, "format_id": "2", "filesize": 300_000_000},
        ]
        result = get_smart_quality(info)
        assert result["quality"] == "best"
        assert result["format_id"] == "1"

    def test_max_size_constraint(self):
        info = MagicMock()
        info.formats = [
            {"vcodec": "h264", "acodec": "none", "height": 1080, "format_id": "1", "filesize": 500_000_000},
            {"vcodec": "h264", "acodec": "none", "height": 720, "format_id": "2", "filesize": 300_000_000},
            {"vcodec": "h264", "acodec": "none", "height": 480, "format_id": "3", "filesize": 100_000_000},
        ]
        result = get_smart_quality(info, max_size_mb=200)
        assert result["format_id"] == "3"
        assert result["estimated_size_mb"] == 100

    def test_fallback_to_lowest(self):
        info = MagicMock()
        info.formats = [
            {"vcodec": "h264", "acodec": "none", "height": 1080, "format_id": "1", "filesize": 500_000_000},
        ]
        result = get_smart_quality(info, max_size_mb=100)
        assert result["quality"] == "480p"


class TestLinkGrabber:
    def test_grab_youtube_links(self):
        from unittest.mock import patch, MagicMock
        from src.services.link_grabber import grab_links
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = 'href="https://www.youtube.com/watch?v=abc123" href="https://youtu.be/xyz789"'
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp
            results = grab_links("https://example.com")
            assert len(results) >= 1

    def test_grab_links_empty_page(self):
        from unittest.mock import patch, MagicMock
        from src.services.link_grabber import grab_links
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = "<html><body>No links here</body></html>"
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp
            results = grab_links("https://example.com")
            assert results == []

    def test_grab_links_error(self):
        from unittest.mock import patch
        from src.services.link_grabber import grab_links
        with patch("requests.get", side_effect=Exception("network error")):
            results = grab_links("https://example.com")
            assert results == []


class TestSubtitleTranslate:
    def test_translate_empty(self):
        from src.services.subtitle_translate import translate_subtitle
        result = translate_subtitle("")
        assert result == ""

    def test_translate_none(self):
        from src.services.subtitle_translate import translate_subtitle
        result = translate_subtitle(None)
        assert result is None

    def test_translate_srt_file_not_found(self):
        from src.services.subtitle_translate import translate_srt_file
        result = translate_srt_file("/nonexistent/file.srt", "/tmp/out.srt")
        assert result is False


class TestProxyManager:
    def test_init_empty(self):
        from src.services.proxy_manager import ProxyManager
        pm = ProxyManager()
        assert pm.get_total_count() == 0
        assert pm.get_working_count() == 0

    def test_add_proxy(self):
        from src.services.proxy_manager import ProxyManager
        pm = ProxyManager()
        pm.add_proxy("http://proxy1:8080")
        assert pm.get_total_count() == 1

    def test_add_proxies_from_file(self, tmp_path):
        from src.services.proxy_manager import ProxyManager
        proxy_file = tmp_path / "proxies.txt"
        proxy_file.write_text("http://proxy1:8080\nhttp://proxy2:8080\n# comment\n")
        pm = ProxyManager()
        pm.add_proxies_from_file(str(proxy_file))
        assert pm.get_total_count() == 2

    def test_get_next_proxy_no_working(self):
        from src.services.proxy_manager import ProxyManager
        from unittest.mock import patch
        pm = ProxyManager(["http://bad:8080"])
        with patch("requests.get", side_effect=Exception("fail")):
            result = pm.get_next_proxy()
            assert result is None


class TestCategories:
    def test_categorize_music(self):
        from src.services.categories import CategoryManager
        cm = CategoryManager()
        cat = cm.categorize("Best Music Mix 2024")
        assert cat == "Music"

    def test_categorize_education(self):
        from src.services.categories import CategoryManager
        cm = CategoryManager()
        cat = cm.categorize("Python Tutorial for Beginners")
        assert cat == "Education"

    def test_categorize_gaming(self):
        from src.services.categories import CategoryManager
        cm = CategoryManager()
        cat = cm.categorize("Minecraft Gameplay Walkthrough")
        assert cat == "Gaming"

    def test_categorize_other(self):
        from src.services.categories import CategoryManager
        cm = CategoryManager()
        cat = cm.categorize("Random Video Title")
        assert cat == "Other"

    def test_get_folder(self):
        from src.services.categories import CategoryManager
        cm = CategoryManager()
        assert cm.get_folder("Music") == "Music"
        assert cm.get_folder("Gaming") == "Gaming"

    def test_add_category(self):
        from src.services.categories import CategoryManager
        cm = CategoryManager()
        cm.add_category("Cooking", ["recipe", "cook", "baking"], "Cooking")
        assert "Cooking" in cm.list_categories()


class TestSubscriptions:
    def test_subscribe(self, tmp_path, monkeypatch):
        from src.services.subscriptions import SubscriptionManager
        monkeypatch.setattr("src.services.subscriptions.SUBSCRIPTIONS_FILE", tmp_path / "subs.json")
        sm = SubscriptionManager()
        sub = sm.subscribe("https://youtube.com/channel/abc")
        assert sub["url"] == "https://youtube.com/channel/abc"
        assert sub["auto_download"] is False

    def test_unsubscribe(self, tmp_path, monkeypatch):
        from src.services.subscriptions import SubscriptionManager
        monkeypatch.setattr("src.services.subscriptions.SUBSCRIPTIONS_FILE", tmp_path / "subs.json")
        sm = SubscriptionManager()
        sm.subscribe("https://youtube.com/channel/abc")
        sm.unsubscribe("https://youtube.com/channel/abc")
        assert len(sm.list_subscriptions()) == 0

    def test_update_last_check(self, tmp_path, monkeypatch):
        from src.services.subscriptions import SubscriptionManager
        monkeypatch.setattr("src.services.subscriptions.SUBSCRIPTIONS_FILE", tmp_path / "subs.json")
        sm = SubscriptionManager()
        sm.subscribe("https://youtube.com/channel/abc")
        sm.update_last_check("https://youtube.com/channel/abc", "video123")
        subs = sm.list_subscriptions()
        assert subs[0]["last_video"] == "video123"


class TestReports:
    def test_generate_html_report(self, tmp_path):
        from src.services.reports import generate_html_report
        output = str(tmp_path / "report.html")
        result = generate_html_report(output, days=1)
        assert result == output
        with open(output, "r") as f:
            content = f.read()
        assert "<html>" in content
        assert "Kyro Downloader Report" in content

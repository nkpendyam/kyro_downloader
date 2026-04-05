"""Tests for platform utilities."""

from src.utils.platform import (
    get_platform_info,
    detect_content_type,
    is_playlist_url,
    is_story_url,
    normalize_url,
    get_supported_platforms,
    build_quality_preset,
)


class TestGetPlatformInfo:
    def test_youtube(self):
        info = get_platform_info("https://www.youtube.com/watch?v=abc")
        assert info is not None
        assert info["name"] == "YouTube"

    def test_youtu_be(self):
        info = get_platform_info("https://youtu.be/abc")
        assert info is not None
        assert info["name"] == "YouTube"

    def test_unknown_platform(self):
        info = get_platform_info("https://unknown.com/video")
        assert info is None


class TestDetectContentType:
    def test_story(self):
        assert detect_content_type("https://instagram.com/stories/user/123") == "story"

    def test_short(self):
        assert detect_content_type("https://youtube.com/shorts/abc") == "short"

    def test_post(self):
        assert detect_content_type("https://twitter.com/user/status/123") == "post"

    def test_live(self):
        assert detect_content_type("https://twitch.tv/user/live") == "live"

    def test_playlist(self):
        assert detect_content_type("https://youtube.com/playlist?list=abc") == "playlist"

    def test_audio(self):
        assert detect_content_type("https://soundcloud.com/artist/track") == "audio"

    def test_default_video(self):
        assert detect_content_type("https://youtube.com/watch?v=abc") == "video"


class TestIsPlaylistUrl:
    def test_playlist(self):
        assert is_playlist_url("https://youtube.com/playlist?list=abc") is True

    def test_not_playlist(self):
        assert is_playlist_url("https://youtube.com/watch?v=abc") is False


class TestIsStoryUrl:
    def test_story(self):
        assert is_story_url("https://instagram.com/stories/user/123") is True

    def test_not_story(self):
        assert is_story_url("https://youtube.com/watch?v=abc") is False


class TestNormalizeUrl:
    def test_adds_https(self):
        assert normalize_url("youtube.com/watch?v=abc") == "https://youtube.com/watch?v=abc"

    def test_expands_youtu_be(self):
        result = normalize_url("https://youtu.be/abc123")
        assert result == "https://www.youtube.com/watch?v=abc123"

    def test_handles_query_params(self):
        result = normalize_url("https://youtu.be/abc?t=10")
        assert result == "https://www.youtube.com/watch?v=abc"

    def test_handles_none(self):
        assert normalize_url(None) is None

    def test_strips_whitespace(self):
        assert normalize_url("  https://youtube.com  ") == "https://youtube.com"


class TestGetSupportedPlatforms:
    def test_returns_list(self):
        platforms = get_supported_platforms()
        assert isinstance(platforms, list)
        assert len(platforms) > 0

    def test_has_youtube(self):
        platforms = get_supported_platforms()
        domains = [p["domain"] for p in platforms]
        assert "youtube.com" in domains


class TestBuildQualityPreset:
    def test_1080p(self):
        preset = build_quality_preset("1080p")
        assert "height<=1080" in preset

    def test_4k(self):
        preset = build_quality_preset("4k")
        assert "height<=2160" in preset

    def test_hdr(self):
        preset = build_quality_preset("1080p", hdr=True)
        assert "dynamic_range=HDR10" in preset or "HLG" in preset or "DV" in preset

    def test_dolby(self):
        preset = build_quality_preset("1080p", dolby=True)
        assert "acodec^=ec-3" in preset or "ac-3" in preset

    def test_default(self):
        preset = build_quality_preset("unknown")
        assert preset == "bestvideo+bestaudio/best"

"""Tests for downloader format analysis."""
from src.core.downloader import (
    analyze_available_formats,
    build_quality_labels,
    AUDIO_QUALITY_PRESETS,
)


class TestAnalyzeAvailableFormats:
    def test_empty_formats(self):
        result = analyze_available_formats([])
        assert result["available_qualities"] == []
        assert result["has_hdr"] is False
        assert result["has_dolby"] is False
        assert result["audio_bitrates"] == []
        assert result["audio_codecs"] == []

    def test_detects_heights(self):
        formats = [
            {"height": 1080, "acodec": "none"},
            {"height": 720, "acodec": "none"},
            {"height": 480, "acodec": "none"},
        ]
        result = analyze_available_formats(formats)
        assert result["available_qualities"] == [1080, 720, 480]

    def test_detects_hdr(self):
        formats = [{"height": 1080, "acodec": "none", "dynamic_range": "HDR10"}]
        result = analyze_available_formats(formats)
        assert result["has_hdr"] is True

    def test_detects_dolby(self):
        formats = [{"height": 1080, "acodec": "ec-3", "abr": 192}]
        result = analyze_available_formats(formats)
        assert result["has_dolby"] is True

    def test_detects_audio_codecs(self):
        formats = [
            {"height": 0, "acodec": "mp3", "abr": 128},
            {"height": 0, "acodec": "opus", "abr": 160},
            {"height": 0, "acodec": "flac", "abr": 0},
        ]
        result = analyze_available_formats(formats)
        assert "mp3" in result["audio_codecs"]
        assert "opus" in result["audio_codecs"]
        assert "flac" in result["audio_codecs"]

    def test_detects_audio_bitrates(self):
        formats = [
            {"height": 0, "acodec": "mp3", "abr": 128},
            {"height": 0, "acodec": "mp3", "abr": 320},
        ]
        result = analyze_available_formats(formats)
        assert result["audio_bitrates"] == [320, 128]


class TestBuildQualityLabels:
    def test_empty_analysis(self):
        analysis = {
            "available_qualities": [],
            "has_hdr": False,
            "has_dolby": False,
            "audio_bitrates": [],
            "audio_codecs": [],
        }
        result = build_quality_labels(analysis)
        assert result == ["Best Available"]

    def test_basic_qualities(self):
        analysis = {
            "available_qualities": [1080, 720, 480],
            "has_hdr": False,
            "has_dolby": False,
            "audio_bitrates": [],
            "audio_codecs": [],
        }
        result = build_quality_labels(analysis)
        assert result == ["1080p", "720p", "480p"]

    def test_best_available_when_empty(self):
        analysis = {
            "available_qualities": [],
            "has_hdr": False,
            "has_dolby": False,
            "audio_bitrates": [],
            "audio_codecs": [],
        }
        result = build_quality_labels(analysis)
        assert result == ["Best Available"]
        assert result.count("Best Available") == 1

    def test_hdr_label(self):
        analysis = {
            "available_qualities": [2160, 1080],
            "has_hdr": True,
            "has_dolby": False,
            "audio_bitrates": [],
            "audio_codecs": [],
        }
        result = build_quality_labels(analysis)
        assert "4K HDR" in result

    def test_dolby_label(self):
        analysis = {
            "available_qualities": [1080],
            "has_hdr": False,
            "has_dolby": True,
            "audio_bitrates": [],
            "audio_codecs": [],
        }
        result = build_quality_labels(analysis)
        assert "1080p + Dolby" in result

    def test_hdr_and_dolby_label(self):
        analysis = {
            "available_qualities": [2160],
            "has_hdr": True,
            "has_dolby": True,
            "audio_bitrates": [],
            "audio_codecs": [],
        }
        result = build_quality_labels(analysis)
        assert "4K HDR + Dolby" in result


class TestAudioQualityPresets:
    def test_all_presets_have_required_fields(self):
        for name, preset in AUDIO_QUALITY_PRESETS.items():
            assert "abr" in preset
            assert "format" in preset
            assert "description" in preset

    def test_lossless_presets_have_zero_abr(self):
        for name in ["Lossless (FLAC)", "Lossless (ALAC)", "Uncompressed (WAV)"]:
            assert AUDIO_QUALITY_PRESETS[name]["abr"] == "0"

    def test_voice_preset_lowest_bitrate(self):
        assert AUDIO_QUALITY_PRESETS["64 kbps (Voice)"]["abr"] == "64"

    def test_best_mp3_highest_mp3_bitrate(self):
        assert AUDIO_QUALITY_PRESETS["320 kbps (Best MP3)"]["abr"] == "320"

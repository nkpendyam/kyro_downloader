"""Tests for subtitle_translate service."""

from unittest.mock import patch, MagicMock
from src.services.subtitle_translate import translate_subtitle


class TestSubtitleTranslate:
    def test_translate_subtitle_returns_text(self):
        with patch("src.services.subtitle_translate.requests.get") as mock_get:
            mock_get.return_value = MagicMock()
            mock_get.return_value.json.return_value = {"responseData": {"translatedText": "Hola mundo"}}
            result = translate_subtitle("Hello world", "en", "es")
        assert result == "Hola mundo"

    def test_translate_subtitle_empty_text(self):
        result = translate_subtitle("")
        assert result == ""

    def test_translate_subtitle_returns_original_on_failure(self):
        with patch("src.services.subtitle_translate.requests.get", side_effect=Exception("network error")):
            result = translate_subtitle("Hello world", "en", "es")
        assert result == "Hello world"

    def test_translate_subtitle_truncates_long_text(self):
        with patch("src.services.subtitle_translate.requests.get") as mock_get:
            mock_get.return_value = MagicMock()
            mock_get.return_value.json.return_value = {"responseData": {"translatedText": "translated"}}
            long_text = "x" * 600
            translate_subtitle(long_text, "en", "es")
            call_params = mock_get.call_args.kwargs["params"]
            assert len(call_params["q"]) <= 500

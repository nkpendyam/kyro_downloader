"""Tests for CLI parser and smart-audio/subtitle behavior."""

from __future__ import annotations

from typing import Any, Callable, cast
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.cli import __main__ as cli_main


class _FakeConfig:
    """Minimal typed config object for CLI command tests."""

    def __init__(self, output_path: str) -> None:
        self.general = SimpleNamespace(output_path=output_path)

    def model_dump(self) -> dict[str, Any]:
        return {}


def test_create_parser_download_subtitle_flags() -> None:
    """Download command should parse subtitle flags correctly."""
    parser = cli_main.create_parser()
    args = parser.parse_args(
        [
            "download",
            "https://example.com/video",
            "--subs",
            "--subs-lang",
            "en,es",
            "--embed-subs",
            "--subs-format",
            "vtt",
            "--no-auto-subs",
        ]
    )

    assert args.command == "download"
    assert args.subs is True
    assert args.subs_lang == "en,es"
    assert args.embed_subs is True
    assert args.subs_format == "vtt"
    assert args.no_auto_subs is True


def test_create_parser_mp3_smart_audio_flags() -> None:
    """MP3 command should parse smart-audio options."""
    parser = cli_main.create_parser()
    args = parser.parse_args(
        [
            "mp3",
            "https://example.com/video",
            "--smart-audio",
            "--prefer-codec",
            "opus",
            "--subs",
            "--subs-lang",
            "en,fr",
        ]
    )

    assert args.command == "mp3"
    assert args.smart_audio is True
    assert args.prefer_codec == "opus"
    assert args.subs is True
    assert args.subs_lang == "en,fr"


def test_create_parser_download_preset_flag() -> None:
    """Download command should parse competitor-grade preset option."""
    parser = cli_main.create_parser()
    args = parser.parse_args(
        ["download", "https://example.com/video", "--preset", "voice-optimized"]
    )

    assert args.command == "download"
    assert args.preset == "voice-optimized"


def test_create_parser_download_cookies_from_browser_flag() -> None:
    """Download command should parse browser-cookie flag."""
    parser = cli_main.create_parser()
    args = parser.parse_args(
        ["download", "https://example.com/video", "--cookies-from-browser", "firefox"]
    )

    assert args.command == "download"
    assert args.cookies_from_browser == "firefox"


def test_create_parser_playlist_and_batch_cookies_from_browser_flag() -> None:
    """Playlist and batch commands should parse browser-cookie flag."""
    parser = cli_main.create_parser()
    playlist_args = parser.parse_args(
        ["playlist", "https://example.com/playlist", "--cookies-from-browser", "chrome"]
    )
    batch_args = parser.parse_args(
        ["batch", "urls.txt", "--cookies-from-browser", "edge"]
    )

    assert playlist_args.cookies_from_browser == "chrome"
    assert batch_args.cookies_from_browser == "edge"


def test_cmd_mp3_builds_expected_subtitle_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """cmd_mp3 should normalize subtitle settings into manager config."""
    manager = MagicMock()
    manager.config = {}

    def _normalize_url(url: str) -> str:
        return url

    def _validate_url(url: str) -> bool:
        return bool(url)

    def _validate_output_path(path: str) -> str:
        return path

    def _manager_factory(_cfg: dict[str, Any]) -> MagicMock:
        return manager

    monkeypatch.setattr("src.cli.__main__.normalize_url", _normalize_url)
    monkeypatch.setattr("src.cli.__main__.validate_url", _validate_url)
    monkeypatch.setattr("src.cli.__main__.validate_output_path", _validate_output_path)
    monkeypatch.setattr("src.cli.__main__.DownloadManager", _manager_factory)

    args = SimpleNamespace(
        url="https://example.com/video",
        output="downloads",
        format="mp3",
        quality="192",
        smart_audio=False,
        prefer_codec="any",
        subs=True,
        subs_lang="en, es ,",
        embed_subs=True,
        no_auto_subs=True,
        subs_format="srt",
    )
    config = _FakeConfig("downloads")
    cmd_mp3 = cast(Callable[[Any, Any], None], getattr(cli_main, "cmd_mp3"))

    cmd_mp3(args, config)

    assert manager.config["subtitles"] == {
        "enabled": True,
        "languages": ["en", "es"],
        "embed": True,
        "auto_generated": False,
        "format": "srt",
    }


def test_cmd_mp3_smart_audio_updates_manager_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """cmd_mp3 should write smart-audio decision and subtitle config into manager config."""
    manager = MagicMock()
    manager.config = {}

    def _normalize_url(url: str) -> str:
        return url

    def _validate_url(url: str) -> bool:
        return bool(url)

    def _validate_output_path(path: str) -> str:
        return path

    def _manager_factory(_cfg: dict[str, Any]) -> MagicMock:
        return manager

    def _get_video_info(_url: str) -> SimpleNamespace:
        return SimpleNamespace(available=[])

    def _build_audio_options(_available: Any) -> list[dict[str, str]]:
        return [
            {
                "label": "Source Opus 160k",
                "audio_format": "opus",
                "audio_quality": "160",
                "selector": "251",
            },
            {
                "label": "Source AAC 128k",
                "audio_format": "aac",
                "audio_quality": "128",
                "selector": "140",
            },
        ]

    monkeypatch.setattr("src.cli.__main__.normalize_url", _normalize_url)
    monkeypatch.setattr("src.cli.__main__.validate_url", _validate_url)
    monkeypatch.setattr("src.cli.__main__.validate_output_path", _validate_output_path)
    monkeypatch.setattr("src.cli.__main__.DownloadManager", _manager_factory)
    monkeypatch.setattr("src.cli.__main__.get_video_info", _get_video_info)
    monkeypatch.setattr(
        "src.cli.__main__.build_smart_audio_options",
        _build_audio_options,
    )

    args = SimpleNamespace(
        url="https://example.com/video",
        output="downloads",
        format="mp3",
        quality="192",
        smart_audio=True,
        prefer_codec="aac",
        subs=True,
        subs_lang="en",
        subs_format="srt",
        no_auto_subs=False,
        embed_subs=False,
    )
    config = _FakeConfig("downloads")
    cmd_mp3 = cast(Callable[[Any, Any], None], getattr(cli_main, "cmd_mp3"))

    cmd_mp3(args, config)

    assert manager.config["audio_format"] == "aac"
    assert manager.config["audio_quality"] == "128"
    assert manager.config["audio_selector"] == "140"
    assert manager.config["subtitles"]["enabled"] is True
    manager.download_now.assert_called_once_with("https://example.com/video", "downloads", only_audio=True)


def test_cmd_mp3_preset_applies_output_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """Preset should inject output template and default subtitle profile."""
    manager = MagicMock()
    manager.config = {}

    def _normalize_url(url: str) -> str:
        return url

    def _validate_url(url: str) -> bool:
        return bool(url)

    def _validate_output_path(path: str) -> str:
        return path

    def _manager_factory(_cfg: dict[str, Any]) -> MagicMock:
        return manager

    monkeypatch.setattr("src.cli.__main__.normalize_url", _normalize_url)
    monkeypatch.setattr("src.cli.__main__.validate_url", _validate_url)
    monkeypatch.setattr("src.cli.__main__.validate_output_path", _validate_output_path)
    monkeypatch.setattr("src.cli.__main__.DownloadManager", _manager_factory)

    args = SimpleNamespace(
        url="https://example.com/video",
        output="downloads",
        format="mp3",
        quality="192",
        smart_audio=False,
        prefer_codec="any",
        preset="podcast-fast",
        subs=False,
        subs_lang="en",
        subs_format="srt",
        no_auto_subs=False,
        embed_subs=False,
    )
    config = _FakeConfig("downloads")
    cmd_mp3 = cast(Callable[[Any, Any], None], getattr(cli_main, "cmd_mp3"))

    cmd_mp3(args, config)

    assert manager.config["output_template"] == "%(upload_date)s/%(title)s.%(ext)s"
    assert manager.config["subtitles"]["enabled"] is True


def test_cmd_mp3_sets_cookies_from_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    """cmd_mp3 should pass browser cookie preference into manager config."""
    manager = MagicMock()
    manager.config = {}

    monkeypatch.setattr("src.cli.__main__.normalize_url", lambda url: url)
    monkeypatch.setattr("src.cli.__main__.validate_url", lambda url: bool(url))
    monkeypatch.setattr("src.cli.__main__.validate_output_path", lambda path: path)
    monkeypatch.setattr("src.cli.__main__.DownloadManager", lambda _cfg: manager)

    args = SimpleNamespace(
        url="https://example.com/video",
        output="downloads",
        format="mp3",
        quality="192",
        smart_audio=False,
        prefer_codec="any",
        cookies_from_browser="firefox",
        preset="none",
        subs=False,
        subs_lang="en",
        subs_format="srt",
        no_auto_subs=False,
        embed_subs=False,
    )
    config = _FakeConfig("downloads")
    cmd_mp3 = cast(Callable[[Any, Any], None], getattr(cli_main, "cmd_mp3"))

    cmd_mp3(args, config)

    assert manager.config["cookies_from_browser"] == "firefox"

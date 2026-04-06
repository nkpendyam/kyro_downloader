"""Tests for CLI search command module."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.cli.commands import search as search_cmd


def test_safe_console_text_handles_none() -> None:
    assert search_cmd._safe_console_text(None) == "None"


def test_safe_console_text_handles_empty() -> None:
    assert search_cmd._safe_console_text("") == ""


def test_safe_console_text_handles_special_chars() -> None:
    text = "hello<>|:*?"
    assert search_cmd._safe_console_text(text) == text


def test_safe_console_text_handles_unicode() -> None:
    text = "测试-emoji-✅"
    assert isinstance(search_cmd._safe_console_text(text), str)


def test_search_prints_table_when_results_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        search_cmd,
        "search_platform",
        lambda _q, _p, _m: [{"title": "Result", "uploader": "Uploader", "duration": 120, "view_count": 1500}],
    )
    mock_print = Mock()
    monkeypatch.setattr(search_cmd.console, "print", mock_print)

    search_cmd.search("query", "youtube", 1)

    mock_print.assert_called_once()


def test_search_prints_no_results_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(search_cmd, "search_platform", lambda _q, _p, _m: [])
    lines: list[str] = []
    monkeypatch.setattr(search_cmd, "print", lambda message: lines.append(message))

    search_cmd.search("query", "youtube", 1)

    assert any("No results found" in line for line in lines)


def test_search_prints_error_when_search_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_q: str, _p: str, _m: int):
        raise RuntimeError("boom")

    monkeypatch.setattr(search_cmd, "search_platform", _raise)
    lines: list[str] = []
    monkeypatch.setattr(search_cmd, "print", lambda message: lines.append(message))

    search_cmd.search("query", "youtube", 1)

    assert any("Search failed" in line for line in lines)
